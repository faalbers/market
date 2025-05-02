import logging.handlers
import multiprocessing, logging
from .tickers import Tickers
from .vault import Vault
import sys, traceback
from pprint import pp
from .database import Database
import pandas as pd
from langchain_ollama import OllamaLLM
from .utils import stop_text, yfinancetest
from .analysis import Analysis
from .quicken import Quicken
from .report import Report
from .portfolio import Portfolio
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta

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

        # self.logger.info('Market: start logging')

    def __init__(self):
        self.__setup_logger()
        self.vault = Vault()

    def __del__(self):
        self.logger.info('Market: end logging')
        self.log_queue.put_nowait(None)
        sys.excepthook = self.builtin_excepthook
        self.log_queue.close()
    
    def update(self):
        self.vault.update(['update'])
    
    def update_weekly(self, tickers=None):
        if not tickers or tickers.count == 0:
            tickers = self.get_scraped_tickers()
        # # catalog 'update'
        # tickers.update(['update'])
        # catalog 'fundamental'
        equity_tickers = self.get_tickers(tickers.get_symbols(['EQUITY']))
        equity_tickers.update(['fundamental'])

    def update_nightly(self, tickers=None):
        if not tickers or tickers.count == 0:
            tickers = self.get_scraped_tickers()
        tickers.update(['update'])
    
    def update_nightly_us_market(self):
        tickers = self.get_us_market_tickers()
        tickers.update(['update'])

    def get_tickers(self, symbols):
        return Tickers(symbols)
    
    def get_us_market_tickers(self, update=False):
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
        
        # fix symbol names
        symbols_fixed = set()
        for symbol in symbols:
            if symbol.startswith('I:'):
                symbol = '^' + symbol[2:]
            symbols_fixed.add(symbol)

        # fix some names
        return Tickers(symbols_fixed)

    def get_scraped_tickers(self):
        data_symbols = self.vault.get_data(['profile'])['profile']
        symbols = sorted(data_symbols)
        return Tickers(symbols)

    def get_portfolio(self, update=False):
        return Portfolio(update)

    def get_analysis(self, tickers):
        return Analysis(tickers)

    def make_data_report(self):
        tickers = self.get_scraped_tickers()
        tickers.make_data_report()

    def make_quicken_prices(self):
        # quicken prices at end of month for import to quicken
        if not yfinancetest(): return

        # get last day of month string
        now = datetime.now()
        last_day = calendar.monthrange(now.year, now.month)[1]
        if now.day == last_day:
            date_string = now.strftime('%Y-%m-%d')
        else:
            last_month = now - relativedelta(months=1)
            last_day = calendar.monthrange(last_month.year, last_month.month)[1]
            last_month = datetime(year=last_month.year, month=last_month.month, day=last_day)
            date_string = last_month.strftime('%Y-%m-%d')

        quicken = self.get_quicken('database/2020.QIF')
        symbols = quicken.get_securities()['symbol'].dropna().unique()
        tickers = self.get_tickers(symbols)
        chart = tickers.get_chart(end_date=date_string, update=True)
        # chart = tickers.get_chart(end_date=date_string)
        dftn = pd.Series()
        for symbol, df in chart.items():
            df_symbol = df.loc[:date_string]
            if df_symbol.shape[0] == 0: continue
            dftn[symbol] = df_symbol.iloc[-1]['Close']
        dftn = dftn.dropna().round(2)
        print(dftn)
        dftn.to_csv('Z:\\Quicken\\QuickenImport.csv', header=False, sep=',', encoding='utf-8')

    # TODO these need to be checked
    def get_quicken(self, qif_file):
        return Quicken(qif_file)

    def make_porfolios_report(self):
        quicken = self.get_quicken('database/2020.QIF')
        portfolios = quicken.get_portfolios()
        for portfolio in portfolios:
            report_name = portfolio.name.replace(' ', '_') + '_report'
            report = Report(report_name)
            
            portfolio.add_report(report)
            report.buildDoc()
    
