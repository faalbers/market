from .catalog import Catalog
from ..scrape import *
from pprint import pp
import multiprocessing
import logging

class Vault():
    def __init__(self):
        self.catalog = Catalog()
        self.logger = logging.getLogger('Market')

    @staticmethod
    def update_scrapers(log_queue, update_scrapers, key_values):
        logger = logging.getLogger("vault_multi")
        logger.setLevel(logging.INFO)
        queue_handler = logging.handlers.QueueHandler(log_queue)  
        logger.addHandler(queue_handler)  

        logger.info('update_scrapers: multi')

        for scraper_class, table_names in update_scrapers.items():
            scraper_class(key_values, table_names=table_names)

    def update(self, catalogs=[], key_values=[]):
        # gather scrape classes
        scraper_classes_data = {Yahoo: [], FMP: []}
        for catalog in catalogs:
            catalog_data =  self.catalog.get_catalog(catalog)
            if len(catalog_data) > 0:
                for set_name, test_set_data in catalog_data['sets'].items():
                    for scraper_class, scraper_data in test_set_data['scrapes'].items():
                        for sub_class, scraper_class_data in scraper_classes_data.items():
                            if issubclass(scraper_class, sub_class):
                                scraper_class_data.append((scraper_class, list(scraper_data.keys())))
        multi_chunks = []
        log_queue = self.logger.handlers[0].queue
        for sub_class, scraper_classes in scraper_classes_data.items():
            # creat multi cunk per sub_class
            update_scrapers = {}
            for scraper_class, table_names in scraper_classes:
                if not scraper_class in update_scrapers:
                    update_scrapers[scraper_class] = []
                for table_name in table_names:
                    update_scrapers[scraper_class] += scraper_class.get_table_names(table_name)
            if len(update_scrapers) > 0:
                multi_chunks.append((log_queue, update_scrapers, key_values))
        
        # run scrapes in multi thread
        self.logger.info('Run scrapes in %s threads' % (len(multi_chunks)))
        log_queue = self.logger.handlers[0].queue
        processes = []
        for chunk in multi_chunks:
            p = multiprocessing.Process(target=Vault.update_scrapers, args=chunk)
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        self.logger.info('Scraping threads completed')

    def get_data(self, catalogs=[], key_values=[], update=False):
        if update : self.update(catalogs, key_values)

