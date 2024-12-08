import logging.handlers
import multiprocessing, logging
from .vault import Vault

class Market():
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

    def __init__(self):
        self.log_queue = multiprocessing.Queue()
        
        logger = logging.getLogger("Market")
        logging.handlers.QueueHandler(self.log_queue)
        logger.setLevel(logging.INFO)
        queue_handler = logging.handlers.QueueHandler(self.log_queue)  
        logger.addHandler(queue_handler)

        self.log_process = multiprocessing.Process(target=Market.logger_process, args=(self.log_queue,))
        self.log_process.start()

        logger.info('market started')

        self.vault = Vault()

    def __del__(self):
        pass
        self.log_queue.put_nowait(None)
        # self.log_process.join()
        # self.log_queue.close()


    