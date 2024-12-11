import logging.handlers
import multiprocessing, logging
from .vault import Vault
import sys, traceback
from pprint import pp

class Market():
    @staticmethod 
    def excepthook(exc_type, exc_value, exc_traceback):
        # terminate all lingering processess
        for p in multiprocessing.active_children(): p.terminate()
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

    def get_us_market_symbols(self):
        test = self.vault.get_data(['symbols'])['symbols']
        pp(test['test'].keys())
        return ['AAPL']

    