from .polygon import Polygon
import logging
from ...database import Database
from pprint import pp
from datetime import datetime, timedelta
import pandas as pd
import re

class Polygon_News(Polygon):
    dbName = 'polygon_news'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['news']
        return [data_name]

    def __init__(self, key_values=[], data_names=[], update = False, forced=False):
        self.db = Database(self.dbName)
        if not update: return
        self.logger = logging.getLogger('vault_multi')
        super().__init__()

        request_arguments = {
            'url': 'https://api.polygon.io/v2/reference/news',
            'params': {
                'limit': 1000,
                'sort': 'published_utc',
                'order': 'asc'
            },
        }

        status_db = self.db.table_read('status_db')
        if not status_db.empty:
            last_published_utc = status_db.loc['news', 'last_published_utc']
            # add one minute to make sure we don't get any duplicates
            last_published_utc = datetime.strptime(last_published_utc, '%Y-%m-%dT%H:%M:%SZ') + timedelta(minutes=1)
            last_published_utc = last_published_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
            self.logger.info('Polygon: Polygon_News update starting from: %s' % last_published_utc)
            request_arguments['params']['published_utc.gt'] = last_published_utc
        else:
            self.logger.info('Polygon: Polygon_News update starting from beginning')

        # backup first
        self.logger.info('Polygon: Polygon_News: %s' % self.db.backup())

        self.last_published_utc = None
        self.request(request_arguments, self.push_news_data)

        # update status
        if self.last_published_utc != None:
            status_db = pd.DataFrame([{'last_published_utc': self.last_published_utc}], index=['news'])
            status_db.index.name = 'table_name'
            self.db.table_write('status_db', status_db, replace=True)

        self.logger.info('Polygon: Polygon_News update done')

    def push_news_data(self, response_data):
        # do nothing of response is empty
        if len(response_data) == 0: return

        news_block = pd.DataFrame(response_data)
        news_block.set_index('id', inplace=True)
        self.last_published_utc = str(news_block.iloc[-1]['published_utc'])

        # write news
        self.db.table_write('news', news_block)

        # create index references
        symbol_ids = {}
        for id, news_data in news_block.iterrows():
            for ticker in news_data['tickers']:
                if not ticker.isupper():
                    # fix ticker names with non all upper case
                    lower_cases = re.findall('[a-z]', ticker)
                    if len(lower_cases) > 0:
                        if lower_cases[0] == 'p':
                            ticker = ticker.replace('p', '-P')
                        else:
                            ticker = ticker.replace(lower_cases[0], '-' + lower_cases[0].upper() + 'I')
                    else:
                        continue
                if not ticker in symbol_ids:
                    symbol_ids[ticker] = []
                symbol_ids[ticker].append(id)
        for symbol, ids in symbol_ids.items():
            df = pd.DataFrame(ids, columns=['ids'])
            self.db.table_write_reference(symbol, 'ids', df)

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'news_polygon':
            data = self.db.table_read_reference('ids', keys=key_values)
            for symbol, ids in data.items():
                df = self.db.table_read('news', keys=ids['ids'].tolist())
                # df['timestamp'] = pd.to_datetime(df['published_utc'], format='%Y-%m-%dT%H:%M:%SZ').astype('int64') // 10**9
                df['date'] = pd.to_datetime(df['published_utc'], format='%Y-%m-%dT%H:%M:%SZ')
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
                print(symbol)
                print(df)

            # if len(columns) > 0:
            #     column_names = [x[0] for x in columns]
            #     data = self.db.timeseries_read('news', keys=key_values, columns=column_names)
            #     for symbol in data:
            #         data[symbol] = data[symbol].rename(columns={x[0]: x[1] for x in columns})
            #     return (data, self.db.timestamp)
            # else:
            #     # data = self.get_news(symbols=key_values)
            #     data = self.db.timeseries_read('news', keys=key_values)
            #     return (data, self.db.timestamp)

    def get_vault_params(self, data_name):
        if data_name == 'news_polygon':
            references = sorted(self.db.table_read_df('table_reference')['news'])
            max_len = 0
            for reference in references:
                column_types = self.db.get_table_info(reference)['columnTypes']
                column_types.pop('timestamp')
                # if len(column_types) > max_len:
                #     max_len = len(column_types)
                #     print(max_len)
                return(column_types)
