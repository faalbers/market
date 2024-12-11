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

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        self.logger.info('Polygon: Polygon_News update')

        request_arguments = {
            'url': 'https://api.polygon.io/v2/reference/news',
            'params': {
                'limit': 1000,
                'sort': 'published_utc',
                'order': 'asc'
            },
        }
        self.request(request_arguments)

        self.logger.info('Polygon: Polygon_News update done')

    def pushAPIData(self, response_data):
        write_news =  {}
        write_symbols = {}
        for entry in response_data:
            symbols = entry['tickers']
            timestamp = int(datetime.strptime(entry['published_utc'], "%Y-%m-%dT%H:%M:%SZ").timestamp())
            while timestamp in write_news: timestamp += 1
            write_news[timestamp] = entry
            for symbol in symbols:
                if not symbol in write_symbols:
                    write_symbols[symbol] = []
                write_symbols[symbol].append(timestamp)
        
        # append the news articles
        self.db.table_write('news_articles', write_news, 'timestamp', method='append')

        # create symbol references to articles
        for symbol, timestamps in write_symbols.items():
            table_name = 'news_'
            for c in symbol:
                if c.isalnum():
                    table_name += c
                else:
                    table_name += '_'

            self.db.table_write(table_name, timestamps, 'timestamp', method='append')

            # write table reference
            self.db.table_write('table_reference', {symbol: {'news': table_name}}, 'symbol', method='append')

        self.db.commit()