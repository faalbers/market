import logging.handlers
from multiprocessing import Queue, Process, Pool
from time import sleep
import logging

def logger_process(q):
    root = logging.getLogger()
    handler = logging.FileHandler('market.log', mode='w')
    formatter = logging.Formatter('%(asctime)s: %(levelname)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    while True:
        if not q.empty():
            record = q.get()
            if record is None: break
            logger = logging.getLogger(record.name)
            logger.handle(record)

def worker(log_queue,x):
    logger = logging.getLogger("multiprocessing_logger")
    logger.setLevel(logging.INFO)
    queue_handler = logging.handlers.QueueHandler(log_queue)  
    logger.addHandler(queue_handler)  

    logger.info(f'worker {x} starting')
    sleep(2)
    logger.info(f'worker {x} ended')

if __name__ == "__main__":
    print('start')
    log_queue = Queue()
    logger = logging.getLogger("main_logger")
    logger.setLevel(logging.INFO)
    queue_handler = logging.handlers.QueueHandler(log_queue)  
    logger.addHandler(queue_handler)  

    # logger = logging.getLogger('market')
    # handler = logging.FileHandler('rfnmarket.log', mode='w')
    # formatter = logging.Formatter('%(asctime)s: %(levelname)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)
    # logger.setLevel(logLevel)

    log_process = Process(target=logger_process, args=(log_queue,))
    log_process.start()

    # for x in range(10):
    #     log_queue.put('queue log %s' % x)
    
    # p = Process(target=worker, args=(log_queue, 1))
    # p.start()
    # p.join()
    
    processes = []
    for i in range(40):
        p = Process(target=worker, args=(log_queue, i ))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()
    
    # multi_chunks = [(log_queue, i) for i in range(3)]
    # with Pool(len(multi_chunks)) as pool:
    #     pool.map(worker, multi_chunks)


    # while not log_queue.empty():
    #     print(log_queue.get())
    
    logger.info('start sleep')
    sleep(2)
    logger.info('end sleep')

    log_queue.put_nowait(None)
    # log_process.join()
    log_queue.close()
    