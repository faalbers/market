from .polygon import Polygon
import logging
from ...database import Database
from pprint import pp
from datetime import datetime

class Polygon_News(Polygon):
    dbName = 'polygon_news'

    @staticmethod
    def get_table_names(table_name):
        # if table_name == 'all':
        #     return list(const.QUOTESUMMARY_MODULES.keys())
        return [table_name]

    def __init__(self, key_values=[], table_names=[], forced=False):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        request_arguments = {
            'url': 'https://api.polygon.io/v2/reference/news',
            'params': {
                'limit': 1000,
                'sort': 'published_utc',
                'order': 'asc'
            },
        }

        last_published_utc = self.db.table_read('status_db', key_values=['news'], column_values=['published_utc'])
        if len(last_published_utc) > 0:
            self.last_published_utc = last_published_utc['news']['published_utc']
            self.logger.info('Polygon: Polygon_News update starting from: %s' % self.last_published_utc)
            request_arguments['params']['published_utc.gt'] = self.last_published_utc
        else:
            self.last_published_utc = None
            self.logger.info('Polygon: Polygon_News update starting from beginning')

        # backup first
        self.db.backup()

        self.request(request_arguments, self.push_news_data)

        # update status
        self.db.table_write('status_db', {'news': {'published_utc': self.last_published_utc}}, key_name='name', method='update')

        self.logger.info('Polygon: Polygon_News update done')

    def push_news_data(self, response_data):
        # TODO: data should be cleaned up for smaller database size ?
        
        # do nothing of response is empty
        if len(response_data) == 0: return

        # create dictionary with unique timestamp keys first
        write_news =  {}
        for entry in response_data:
            # create entry in dictionary with unique timestamp key
            timestamp = int(datetime.strptime(entry['published_utc'], "%Y-%m-%dT%H:%M:%SZ").timestamp())
            while timestamp in write_news: timestamp += 1
            write_news[timestamp] = entry
            # keep last published utc for status update
            self.last_published_utc = entry['published_utc']

        # create symbol table dictionary to append to database
        write_tables = {}
        for timestamp, entry in write_news.items():
            symbols = entry['tickers']
            for symbol in symbols:
                symbol = symbol.upper()
                table_name = 'news_'
                for c in symbol:
                    if c.isalnum():
                        table_name += c
                    else:
                        table_name += '_'
                if not table_name in write_tables:
                    write_tables[table_name] = {}
                write_tables[table_name][timestamp] = entry
                self.db.table_write('table_reference', {symbol: {'news': table_name}}, 'symbol', method='append')

        # now lets update the database tables
        for table_name, table_data in write_tables.items():
            self.db.table_write(table_name, table_data, key_name='timestamp', method='append')

        self.db.commit()
