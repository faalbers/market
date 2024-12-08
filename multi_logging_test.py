import multiprocessing
import logging
import time

def worker_process(name):
    logger = multiprocessing.get_logger()
    start_time = time.time()
    logger.info(f"Worker {name} started at {start_time}")
    # Simulate some work
    time.sleep(2)
    end_time = time.time()
    logger.info(f"Worker {name} finished at {end_time} (Duration: {end_time - start_time:.2f} seconds)")

# print("all Processes starting.")

if __name__ == "__main__":
    print("main process starting.")
    # Set up logging for the main process
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s')
    
    # Set up multiprocessing logging
    multiprocessing.log_to_stderr(logging.INFO)
    
    if False:
        processes = []
        for i in range(3):
            p = multiprocessing.Process(target=worker_process, args=(f"Worker-{i}",))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()
    else:
        multi_chunks = [f"Worker-{i}" for i in range(3)]
        with multiprocessing.Pool(len(multi_chunks)) as pool:
            pool.map(worker_process, multi_chunks)

    print("main process completed.")

# print("all processes Completed.")

