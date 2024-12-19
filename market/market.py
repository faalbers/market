import logging.handlers
import multiprocessing, logging
from .vault import Vault
import sys, traceback
from pprint import pp
from .database import Database
import pandas as pd
from langchain_ollama import OllamaLLM
from .utils import stop_text

class Market():
    @staticmethod 
    def excepthook(exc_type, exc_value, exc_traceback):
        # stop logger befor the exception traceback
        logger = logging.getLogger('Market')
        logger.exception('Market: %s: %s' % (exc_type.__name__,exc_value), exc_info=(exc_type, exc_value, exc_traceback))
        # logger.exception(exc_info=(exc_type, exc_value, exc_traceback))
        log_queue = logger.handlers[0].queue
        log_queue.put_nowait(None)
        # print traceback
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    @staticmethod
    def logger_process(log_queue):
        root = logging.getLogger()
        handler = logging.FileHandler('market.log', mode='w')
        formatter = logging.Formatter('%(asctime)s: %(levelname)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        root.addHandler(handler)
        root.setLevel(logging.INFO)

        while True:
            if not log_queue.empty():
                record = log_queue.get()
                if record is None: break
                logger = logging.getLogger(record.name)
                logger.handle(record)

    def __setup_logger(self):
        self.log_queue = multiprocessing.Queue()
        
        self.logger = logging.getLogger("Market")
        self.logger.setLevel(logging.INFO)
        queue_handler = logging.handlers.QueueHandler(self.log_queue)  
        self.logger.addHandler(queue_handler)

        self.log_process = multiprocessing.Process(target=Market.logger_process, args=(self.log_queue,))
        self.log_process.start()

        # set an error handler that will kill this process whenever we have an exception
        self.builtin_excepthook =   sys.excepthook
        sys.excepthook = Market.excepthook

        self.logger.info('Market: start logging')

    def __init__(self):
        self.__setup_logger()
        self.vault = Vault()

    def __del__(self):
        self.logger.info('Market: end logging')
        self.log_queue.put_nowait(None)
        sys.excepthook = self.builtin_excepthook
        self.log_queue.close()

    def get_us_market_symbols(self, update=False):
        symbols_data = self.vault.get_data(['us_symbols'], update=update)['us_symbols']

        symbols = set()
        
        # get us acronyms
        acronyms_us = set()
        for iso_entry in symbols_data['iso']:
            if 'cc' in iso_entry and iso_entry['cc'] == 'US':
                if 'acronym' in iso_entry: acronyms_us.add(iso_entry['acronym'])
        for iso_entry in symbols_data['iso']:
            if 'acronym' in iso_entry and iso_entry['acronym'] in acronyms_us:
                if iso_entry['cc'] != 'US':
                    acronyms_us.remove(iso_entry['acronym'])

        # get stocklist symbols with acronym in us
        for symbol, symbol_data in symbols_data['symbols']['stocklist'].items():
            if 'acronym' in symbol_data and symbol_data['acronym'] in acronyms_us: symbols.add(symbol)
        
        # get tickers symbols with locale us
        for symbol, symbol_data in symbols_data['symbols']['tickers'].items():
            # dont want these
            if symbol_data['market'] in {'crypto', 'fx'}: continue
            if 'locale' in symbol_data and symbol_data['locale'] == 'us': symbols.add(symbol)
        
        symbols = list(symbols)
        symbols.sort()
        
        return symbols

    def get_scrape_symbols(self):
        data_symbols = self.vault.get_data(['symbols'])['symbols']
        symbols = {}
        for scrape_name, scrape_symbols in data_symbols.items():
            symbols[scrape_name] = sorted(scrape_symbols.keys())
        return symbols
    
    def update_nightly(self, symbols=[]):
        if len(symbols) == 0:
            scrape_symbols = self.get_scrape_symbols()
            # TODO: Probably get_us_market_symbols if no symbols found
            symbols = set(scrape_symbols['yahoo_chart'])
            symbols.update(scrape_symbols['yahoo_quote'])
            symbols = sorted(symbols)
        else:
            symbols = [symbol.upper() for symbol in symbols]
        self.vault.update(['update_nightly'],symbols)

    def update_test(self, symbols=[]):
        self.vault.update(['update_test'],symbols)

    def update_symbols(self, symbols):
        symbols = [symbol.upper() for symbol in symbols]
        self.vault.update(['update_symbols'],symbols)
    
    def __update_news_sentiment(self, db, llm, symbol_news_table, symbol, symbol_name, text_columns):
        symbol_news_ts = db.table_read(symbol_news_table)
        update_data = {}
        article_count = len(symbol_news_ts) + 1
        articles_updated = 0
        for ts, news_data in symbol_news_ts.items():
            if stop_text(): break
            article_count -= 1
            if len(update_data) >= 100:
                db.table_write(symbol_news_table, update_data, 'timestamp', method='update')
                db.commit()
                articles_updated += len(update_data)
                self.logger.info('Market: %s news articles updated     : %s (%s)' % (symbol, articles_updated, db.name))
                self.logger.info('Market: %s news articles to sentiment: %s (%s)' % (symbol, article_count, db.name))
                update_data = {}
            if 'sentiment_llama' in news_data:
                if news_data['sentiment_llama'] == 'NEUTRAL': continue
                if news_data['sentiment_llama'] == 'POSITIVE': continue
                if news_data['sentiment_llama'] == 'NEGATIVE': continue
            news_text = ''
            for column in text_columns:
                if column in news_data and news_data[column]:
                    news_text += news_data[column] + '. '
            if news_text == '':
                update_data[ts] = {'sentiment_llama': 'NEUTRAL'}
                continue
            if symbol_name:
                invoke_text = f"Classify the sentiment about the stock symbol '{symbol}' or the stock name '{symbol_name}' as 'POSITIVE' or 'NEGATIVE' or 'NEUTRAL' with just that one word only, no additional words or reasoning: {news_text}"
            else:
                invoke_text = f"Classify the sentiment about the stock symbol '{symbol}' as 'POSITIVE' or 'NEGATIVE' or 'NEUTRAL' with just that one word only, no additional words or reasoning: {news_text}"
            output = llm.invoke(invoke_text).upper()
            if 'NEUTRAL' in output: output = 'NEUTRAL'
            elif 'POSITIVE' in output: output = 'POSITIVE'
            elif 'NEGATIVE' in output: output = 'NEGATIVE'
            else: output = 'NEUTRAL'
            update_data[ts] = {'sentiment_llama': output}
        
        # write the table
        if len(update_data) > 0:
            db.table_write(symbol_news_table, update_data, 'timestamp', method='update')
            db.commit()
            articles_updated += len(update_data)
            self.logger.info('Market: %s news articles updated     : %s (%s)' % (symbol, articles_updated, db.name))

    def update_news_sentiment(self, symbols=[]):
        # make all symbols upper if any avalable
        if len(symbols) > 0:
            symbols = [symbol.upper() for symbol in symbols]
        
        # get profile of all available symbols
        if len(symbols) == 0:
            symbols_profile = self.vault.get_data(['profile'], key_values=symbols)['profile']
        else:
            symbols_profile = self.vault.get_data(['profile'])['profile']

        # get Polygon and Finviz news and ollama server
        db_polygon = Database('polygon_news')
        db_polygon.backup()
        table_reference_polygon = db_polygon.table_read('table_reference')
        db_finviz = Database('finviz_ticker_news')
        db_finviz.backup()
        table_reference_finviz = db_finviz.table_read('table_reference')
        
        # start ollama
        llm = OllamaLLM(model='llama3.1')

        # use provided symbols or all availbae symbols in news database
        if len(symbols) > 0:
            symbols = sorted([symbol.upper() for symbol in symbols])
        else:
            symbols = sorted(set(table_reference_polygon.keys()).union(set(table_reference_finviz.keys())))

        # go throug all symbols and their timeseries
        self.logger.info('Market: Updating news sentiment on %d symbols' % len(symbols))
        symbol_count = len(symbols) + 1
        for symbol in symbols:
            symbol_count -= 1
            if symbol_count % 100 == 0: self.logger.info('Market: still %s symbols to check' % symbol_count)
            # get symbol name
            symbol_name = None
            if symbol in symbols_profile: symbol_name = symbols_profile[symbol]['name']
            
            # handle with according database
            if symbol in table_reference_polygon:
                table_reference = table_reference_polygon[symbol]
                self.__update_news_sentiment(db_polygon, llm, table_reference['news'], symbol, symbol_name, ['title', 'description'])
                if stop_text(): break
            if symbol in table_reference_finviz:
                table_reference = table_reference_finviz[symbol]
                self.__update_news_sentiment(db_finviz, llm, table_reference['news'], symbol, symbol_name, ['Title'])
                if stop_text(): break
        
        if stop_text():
            self.logger.info('Market: Updating news sentiment manually stopped')

