from ..vault import Vault
from ..scrape import YahooF_Chart
from ..viz import Viz
from ..database import Database
from ..utils import stop_text, storage
import pandas as pd
from pprint import pp
from datetime import datetime
import logging, os
from langchain_ollama import OllamaLLM

class Tickers():
    def __init__(self, symbols=[]):
        self.logger = logging.getLogger('Market')
        self.symbols = set([symbol.upper() for symbol in symbols])
        self.vault = Vault()
        self.viz = Viz()
    
    @property
    def count(self):
        return len(self.symbols)
    
    def add_symbol(self, symbol):
        self.symbols.add(symbol.upper())
    
    def add_symbols(self, symbols):
        self.symbols.update([symbol.upper() for symbol in symbols])

    # TODO: add scraped symbols
    # TODO: add US market symbols

    def get_symbols(self):
        return sorted(self.symbols)

    def get_profiles(self, update=False):
        return self.vault.get_data(['profile'], self.symbols, update=update)['profile']
    
    def get_analysis(self, update=False):
        return self.vault.get_data(['analysis'], self.symbols, update=update)['analysis']
    
    def get_prices(self, update=False):
        return self.vault.get_data(['price'], self.symbols, update=update)['price']

    def get_chart(self, start_date=None, end_date=None, update=False):
        # we cache if more the 65
        if len(self.symbols) > 65:
            if update: self.update(['chart'])
            
            storage_name = 'database/%s' % YahooF_Chart.dbName
            chart_cached = storage.load(storage_name)

            chart = {}
            for symbol in self.symbols:
                if not symbol in chart_cached: continue
                df = chart_cached[symbol]
                if start_date:
                    df = df.loc[start_date:]
                if end_date:
                    df = df.loc[:end_date]
                chart[symbol] = df

            return chart

        # we get from vault if 65 or less
        chart_data = self.vault.get_data(['chart'], self.symbols, update=update)['chart']
        if 'chart' in chart_data:
            chart_data = chart_data['chart']
        else:
            chart_data = {}

        chart = {}
        for symbol, ts_data in chart_data.items():
            df = pd.DataFrame(ts_data).T
            df.index = pd.to_datetime(df.index, unit='s')
            df.sort_index(inplace=True)
            df.index = df.index.floor('D') # set it to beginning of day
            df = df.drop('timestamp', axis=1)
            if start_date:
                df = df.loc[start_date:]
            if end_date:
                df = df.loc[:end_date]
            chart[symbol] = df
        return chart

    def get_all(self):
        return self.vault.get_data(['all'], self.symbols)['all']

    def update(self, catalogs):
        self.vault.update(catalogs, sorted(self.symbols))

    def make_data_report(self):
        all_data = self.get_all()
        self.viz.data_keys_text(all_data, rename_set=set(self.get_symbols()), rename_to='symbol')

    def get_news(self, start_date=None, end_date=None, update=False):
        # update if needed 
        if update:
            self.vault.update(['news'], sorted(self.symbols))

        # get all available news for tickers
        news = self.vault.get_data(['news'], self.symbols)['news']
        
        symbols_news = {}
        for news_name, news_data in news.items():
            for symbol, ts_data in news_data.items():
                if not symbol in symbols_news:
                    symbols_news[symbol] = ts_data
                else:
                    symbols_news[symbol] = {**symbols_news[symbol], **ts_data}
        for symbol, ts_data in symbols_news.items():
            symbols_news[symbol] = pd.DataFrame(ts_data).T
            symbols_news[symbol].index = pd.to_datetime(symbols_news[symbol].index, unit='s')
            symbols_news[symbol].sort_index(inplace=True)
            if start_date != None:
                symbols_news[symbol] = symbols_news[symbol].loc[start_date:]
            if end_date != None:
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
                symbols_news[symbol] = symbols_news[symbol].loc[:end_date]

        return symbols_news

    def get_news_sentiment(self, start_date=None, end_date=None, update=False):
        if update:
            self.update_news_sentiment()
        news = self.get_news(start_date,end_date)
        news_sentiment = {}
        for symbol, news_data in news.items():
            # print(news_data.keys())
            news_sentiment[symbol] = news_data[['sentiment_llama','Link']]
            # news_sentiment[symbol].name = 'news_sentiment'
        return news_sentiment
    
    def update_news_sentiment(self):
        # update the news
        self.update(['news'])
        # get Polygon and Finviz news and ollama server
        db_polygon = Database('polygon_news')
        db_polygon.backup()
        table_reference_polygon = db_polygon.table_read('table_reference')
        db_finviz = Database('finviz_ticker_news')
        db_finviz.backup()
        table_reference_finviz = db_finviz.table_read('table_reference')

        # get symbols profile
        symbols_profile = self.get_profiles()

        # start ollama
        llm = OllamaLLM(model='llama3.1')

        # go throug all symbols and their timeseries
        self.logger.info('Tickers: Updating news sentiment on %d symbols' % len(self.symbols))
        symbol_count = len(self.symbols) + 1
        for symbol in self.symbols:
            symbol_count -= 1
            if symbol_count % 100 == 0: self.logger.info('Tickers: still %s symbols to check' % symbol_count)
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
                self.logger.info('Tickers: %s news articles updated     : %s (%s)' % (symbol, articles_updated, db.name))
                self.logger.info('Tickers: %s news articles to sentiment: %s (%s)' % (symbol, article_count, db.name))
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
            self.logger.info('Tickers: %s news articles updated     : %s (%s)' % (symbol, articles_updated, db.name))

    def get_revenue_growth(self):
        return self.vault.get_data(['revenue_growth'], self.symbols)['revenue_growth']
    
    # TODO: add __str__
