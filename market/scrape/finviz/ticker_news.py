from .finviz import Finviz
import logging
from ...database import Database
from pprint import pp
import pandas as pd
from ...utils import stop_text
from datetime import datetime, UTC

class Finviz_Ticker_News(Finviz):
    dbName = 'finviz_ticker_news'

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

        # check what symbols need to be updated
        symbols = self.update_check(key_values, forced=forced)
        if len(symbols) == 0: return
        
        self.logger.info('Finviz:  Finviz_Ticker_News update')

        # backup first
        self.logger.info('Finviz:  Finviz_Ticker_News: %s' % self.db.backup())

        symbols_done = 0
        found = 0
        for symbol in symbols:
            if (symbols_done % 100) == 0:
                self.db.commit()
                self.logger.info('Finviz:  symbols still to do and found so far: (%s / %s)' % (len(symbols) - symbols_done, found))
            if self.request_news(symbol): found += 1
            symbols_done += 1
            if stop_text():
                self.logger.info('Finviz:  manually stopped request')
                self.logger.info('Finviz:  symbols done       : %s' % symbols_done)
                self.db.commit()
                break
        self.logger.info('Finviz:  total symbols found: %s' % (found))
        self.logger.info('Finviz:  Finviz_Ticker_News update done')

    def update_check(self, symbols, forced=False):
        status_db = self.db.table_read('status_db', keys=symbols)

        if forced or status_db.empty:
            return sorted(symbols)

        timestamp_pdt = int(datetime.now().timestamp())
        one_day_ts = timestamp_pdt - (3600 * 24)

        missing_symbols = set(symbols).difference(set(status_db.index))

        update = status_db['timestamp'] < one_day_ts

        update_symbols = set(status_db[update].index).union(missing_symbols)

        return sorted(update_symbols)

    def push_api_data(self, symbol, result):
        symbol = symbol.upper()

        found = not result.empty

        if found:
            result.sort_values(by='Date', inplace=True)
            result.reset_index(drop=True, inplace=True)
            result['Date'] = result['Date'].apply(lambda x: int(x.timestamp()))
            if not result['Date'].is_unique:
                # add a second to not unique timestamps
                grouped_df = result.groupby('Date')
                for timestamp, group in grouped_df.groups.items():
                    if group.shape[0] > 1:
                        for index in group[1:]:
                            timestamp += 1
                            result.loc[index, 'Date'] = timestamp
            result.set_index('Date', verify_integrity=True, inplace=True)
            result.index.name = 'timestamp'
            self.db.table_write_reference(symbol, 'news', result, update=False)

        # update last time we checked on status
        timestamp = int(datetime.now().timestamp())
        status = {
            'timestamp': timestamp,
            'timestamp_str': str(datetime.fromtimestamp(timestamp)),
        }
        status = pd.DataFrame([status], index=[symbol])
        status.index.name = 'symbol'
        self.db.table_write('status_db', status)

        return found

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'news_finviz':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.timeseries_read('news', keys=key_values, columns=column_names)
                for symbol in data:
                    data[symbol] = data[symbol].rename(columns={x[0]: x[1] for x in columns})
                return data
            else:
                data = self.db.timeseries_read('news', keys=key_values)
                return data

    def get_vault_params(self, data_name):
        if data_name == 'news_finviz':
            references = sorted(self.db.table_read_df('table_reference')['news'])
            max_len = 0
            for reference in references:
                column_types = self.db.get_table_info(reference)['columnTypes']
                column_types.pop('timestamp')
                # if len(column_types) > max_len:
                #     max_len = len(column_types)
                #     print(max_len)
                return(column_types)
