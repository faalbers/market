import logging.handlers
import multiprocessing, logging, sys, traceback
from .tickers import Tickers
from .vault import Vault
from .analysis import Analysis, Analysis_GUI
from .utils import yfinancetest
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
from .quicken import Quicken
from pprint import pp
import pandas as pd

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
    
    def get_tickers(self, symbols=[], types=[]):
        return Tickers(symbols, types)
    
    def get_data(self, catalog):
        return self.vault.get_data(catalog)
    
    def get_params(self, catalog):
        return self.vault.get_params(catalog)

    def get_analysis(self, symbols=[], update=False, forced=False, cache_update=False):
        return Analysis(symbols, update=update, forced=forced, cache_update=cache_update)
    
    def analysis_gui(self, symbols=[], update=False, forced=False, cache_update=False):
        return Analysis_GUI(symbols, update=update, forced=forced, cache_update=cache_update)

    def get_quicken(self, qif_file):
        return Quicken(qif_file)

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
        print(symbols)
        tickers = self.get_tickers(symbols)
        charts = tickers.get_charts(update=True, forced=True)
        dftn = pd.Series()
        for symbol, df in charts.items():
            df_symbol = df.loc[:date_string]
            if df_symbol.shape[0] == 0: continue
            dftn[symbol] = df_symbol.iloc[-1]['Close']
        dftn = dftn.dropna().round(2)
        print(dftn)
        dftn.to_csv('Z:\\Quicken\\QuickenImport.csv', header=False, sep=',', encoding='utf-8')
