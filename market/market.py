import logging.handlers
import multiprocessing, logging
from .vault import Vault
import sys, traceback
from pprint import pp

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
        test = self.vault.get_data(['us_symbols'], update=update)['symbols']
        
        symbols = set()
        
        # get us acronyms
        acronyms_us = set()
        for iso_entry in test['iso']:
            if 'cc' in iso_entry and iso_entry['cc'] == 'US':
                if 'acronym' in iso_entry: acronyms_us.add(iso_entry['acronym'])
        for iso_entry in test['iso']:
            if 'acronym' in iso_entry and iso_entry['acronym'] in acronyms_us:
                if iso_entry['cc'] != 'US':
                    acronyms_us.remove(iso_entry['acronym'])

        # get stocklist symbols with acronym in us
        for symbol, symbol_data in test['symbols']['stocklist'].items():
            if 'acronym' in symbol_data and symbol_data['acronym'] in acronyms_us: symbols.add(symbol)
        
        # get tickers symbols with locale us
        for symbol, symbol_data in test['symbols']['tickers'].items():
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
            scrape_symbols = list(scrape_symbols.keys())
            scrape_symbols.sort()
            symbols[scrape_name] = scrape_symbols
        return symbols
    
    def update_nightly(self, symbols=[]):
        if len(symbols) == 0:
            scrape_symbols = self.get_scrape_symbols()
            symbols = list(set(scrape_symbols['Yahoo_Chart']).union(set(scrape_symbols['Yahoo_Quote'])))
            symbols.sort()
        self.vault.update(['update_nightly'],symbols)
