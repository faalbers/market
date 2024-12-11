from .catalog import Catalog
from ..scrape import *
from ..database import Database
from pprint import pp
import multiprocessing
import logging

class Vault():
    def __init__(self):
        self.catalog = Catalog()
        self.logger = logging.getLogger('Market')
        self.databases = {}

    @staticmethod
    def update_scrapers(log_queue, update_scrapers, key_values):
        logger = logging.getLogger("vault_multi")
        logger.setLevel(logging.INFO)
        queue_handler = logging.handlers.QueueHandler(log_queue)  
        logger.addHandler(queue_handler)  

        for scraper_class, table_names in update_scrapers.items():
            scraper_class(key_values, table_names=table_names)

    def update(self, catalogs=[], key_values=[]):
        # gather scrape classes
        scraper_classes_data = {Yahoo: [], FMP: [], Polygon: [], File: [], Finviz: []}
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

    def get_scrape_database(self, scrape_class):
        if not scrape_class in self.databases:
            self.databases[scrape_class] = Database(scrape_class.dbName)
        return self.databases[scrape_class]

    def close_scrape_database(self, scrape_class):
        if scrape_class in self.databases:
            self.databases.pop(scrape_class)

    def close_all_scrape_databases(self):
        scrape_classes = list(self.databases.keys())
        for scrape_class in scrape_classes:
            self.close_scrape_database(scrape_class)

    def get_data(self, catalogs=[], key_values=[], update=False):
        if update : self.update(catalogs, key_values)

        main_data = {}
        for catalog in catalogs:
            catalog_data =  self.catalog.get_catalog(catalog)

            sets_data = {}
            for set_name , set_data in catalog_data['sets'].items():
                tables_data = {}
                for scrape_class, scrape_data in set_data['scrapes'].items():
                    db = self.get_scrape_database(scrape_class)
                    for table_name, table_data in scrape_data.items():
                        scrape_table_names = scrape_class.get_table_names(table_name)
                        handle_key_values = table_data['key_values']
                        for table_name in scrape_table_names:
                            columns = {}
                            for column_set in table_data['column_settings']:
                                search_column = column_set[0]
                                make_column = column_set[1]
                                if search_column == 'all':
                                    for column_name in db.getTableColumnNames(table_name):
                                        if make_column != '':
                                            newColumnName = make_column + column_name.capitalize()
                                        else:
                                            newColumnName = column_name
                                        if not column_name in columns:
                                            columns[column_name] = {}
                                        columns[column_name]['new_name'] = newColumnName
                                else:
                                    if not search_column in columns:
                                        columns[search_column] = {}
                                    columns[search_column]['new_name'] = make_column

                            # get table data
                            found_data = db.table_read(table_name, key_values, list(columns.keys()), handle_key_values=handle_key_values)
                            # skip if no data found
                            if len(found_data) == 0: continue

                            # make data
                            if handle_key_values:
                                make_data = {}
                                for key_value, key_data in found_data.items():
                                    new_key_data = {}
                                    for search_column, column_settings in columns.items():
                                        if not search_column in key_data: continue
                                        new_key_data[column_settings['new_name']] = key_data[search_column]
                                    if len(new_key_data) > 0:
                                        make_data[key_value] = new_key_data
                            else:
                                make_data = []
                                for rowData in found_data:
                                    new_row_data = {}
                                    for search_column, column_settings in columns.items():
                                        if not search_column in rowData: continue
                                        new_row_data[column_settings['new_name']] = rowData[search_column]
                                    if len(new_row_data) > 0:
                                        make_data.append(new_row_data)

                            if len(make_data) > 0:
                                tables_data[table_name] = make_data
                
                # run sets post procs
                if 'post_procs' in set_data:
                    for proc_entry in set_data['post_procs']:
                        proc = proc_entry[0]
                        proc_params = proc_entry[1]
                        proc(self, tables_data, **proc_params)
                        # sets_data[set_name] = proc(self, tables_data, **proc_params)
                sets_data[set_name] = tables_data
                
            # run set catalogs post procs
            if 'post_procs' in catalog_data:
                for procEntry in catalog_data['post_procs']:
                    proc = procEntry[0]
                    procParams = procEntry[1]
                    proc(self, sets_data, **procParams)
            main_data[catalog] = sets_data
        
        self.close_all_scrape_databases()
        return main_data
