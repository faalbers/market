from .catalog import Catalog
from ..scrape import *
import logging
import multiprocessing
from ..utils import stop_text
from pprint import pp

class Vault():
    def __init__(self):
        self.catalog = Catalog()
        self.logger = logging.getLogger('Market')

    def update_scrapers(log_queue, update_scrapers, key_values, forced):
        logger = logging.getLogger("vault_multi")
        logger.setLevel(logging.INFO)
        queue_handler = logging.handlers.QueueHandler(log_queue)  
        logger.addHandler(queue_handler)  

        for scraper_class, data_names in update_scrapers.items():
            scraper_class(key_values, data_names=data_names, update=True, forced=forced)

    def update(self, updates):
        # fill un sub classes with scrapes that need to be updated
        scraper_classes_data = {YahooF: [], FMP: [], Polygon: [], File: [], Finviz: [], Fred: [], Etrade: []}
        for update in updates:
            catalog = update[0]
            key_values = update[1]
            forced = update[2]
            # print(catalog, len(key_values), forced)
            if not catalog in self.catalog.catalog: continue
            catalog = self.catalog.catalog[catalog]
            for scraper_class, scraper_data in catalog.items():
                for sub_class, scraper_class_data in scraper_classes_data.items():
                    if issubclass(scraper_class, sub_class):
                        scraper_class_data.append((scraper_class, key_values, sorted(scraper_data)))

        # create multi chunks for pool
        multi_chunks = []
        log_queue = self.logger.handlers[0].queue
        do_yahoof_chart = False
        for sub_class, scraper_classes in scraper_classes_data.items():
            # creat multi chunk per sub_class
            update_scrapers = {}
            for scraper_class, key_values, data_names in scraper_classes:
                if scraper_class == YahooF_Chart: do_yahoof_chart = True
                if not scraper_class in update_scrapers:
                    update_scrapers[scraper_class] = []
                for data_name in data_names:
                    update_scrapers[scraper_class] += scraper_class.get_data_names(data_name)
            if len(update_scrapers) > 0:
                multi_chunks.append((log_queue, update_scrapers, key_values, forced))

        # run scrapes in multi thread
        if len(multi_chunks) == 0: return
        self.logger.info('Run scrapes in %s threads' % (len(multi_chunks)))
        processes = []
        for chunk in multi_chunks:
            p = multiprocessing.Process(target=Vault.update_scrapers, args=chunk)
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
        self.logger.info('Scraping threads completed')

        # if we manually stopped we dont want to cache
        if stop_text(): return

        # cache chart
        if do_yahoof_chart: YahooF_Chart().cache_data(key_values)

    def get_data(self, catalog, key_values=[], update=False, forced=False):
        if not catalog in self.catalog.catalog: return {}

        # if update: self.update(catalog, key_values=key_values, forced=forced)
        if update: self.update([[catalog, key_values, forced]])

        catalog = self.catalog.catalog[catalog]

        data = {}
        for scraper_class, scraper_data in catalog.items():
            scraper = scraper_class()
            for data_name, columns in scraper_data.items():
                data[data_name] = scraper.get_vault_data(data_name, columns, key_values)
        return data

    def get_params(self, catalog):
        if not catalog in self.catalog.catalog: return {}

        catalog = self.catalog.catalog[catalog]

        params = {}
        for scraper_class, scraper_data in catalog.items():
            scraper = scraper_class()
            for data_name, columns in scraper_data.items():
                params[data_name] = scraper.get_vault_params(data_name)

        return params

