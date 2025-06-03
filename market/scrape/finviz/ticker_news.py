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
        if forced:
            symbols = sorted(key_values)
        else:
            symbols = self.update_check(key_values)
        if len(symbols) == 0: return
        return
        
        self.logger.info('Finviz:  Finviz_Ticker_News update')

        # # backup first
        # self.db.backup()


        symbols_done = 0
        for symbol in symbols:
            if (symbols_done % 100) == 0:
                self.db.commit()
                self.logger.info('Finviz:  symbols still to do: %s' % (len(key_values) - symbols_done))
            self.request_news(symbol)
            symbols_done += 1
            if stop_text():
                self.logger.info('Finviz:  manually stopped request')
                self.logger.info('Finviz:  symbols done       : %s' % symbols_done)
                self.db.commit()
                break
        self.logger.info('Finviz:  Finviz_Ticker_News update done')

    def update_check(self, symbols):
        db_status = self.db.table_read('status_db')
        print(db_status)

        timestamp_pdt = int(datetime.now().timestamp())

        
        
        return symbols

        now_utc = datetime.now(UTC)

        update_symbols = []
        for symbol in symbols:
            if not symbol in db_status:
                # never done before, add it
                update_symbols.append(symbol)
            else:
                pass
                # if db_status[symbol]['found']:
                #     # found before, only do again after 24 h
                #     if db_status[symbol]['timestamp'] <= int(now_utc.timestamp() - (3600 * 24)): update_symbols.append(symbol)
                # else:
                #     # not found before, only try again after 1/2 year
                #     if db_status[symbol]['timestamp'] <= int(now_utc.timestamp() - (3600 * 24 * 182)): update_symbols.append(symbol)
        
        return sorted(update_symbols)

    def pushAPIData(self, symbol, result):
        print('hello')
        found = result[0]
        timestamp = int(datetime.now().timestamp())
        status_info = {
            'timestamp': timestamp,
            'timestamp_str': str(datetime.fromtimestamp(timestamp)),
            'last_timestamp': 0,
            'last_timestamp_str': '',
            'found': found,
        }
        if not found:
            status_info = pd.DataFrame({symbol: status_info}).T
            status_info.index.name = 'symbol'
            self.db.table_write('status_db', status_info)
            return
        news_df = result[1]
        symbol = symbol.upper()
        news_df.sort_values(by='Date', inplace=True)
        news_df.reset_index(drop=True, inplace=True)
        news_df['Date'] = news_df['Date'].apply(lambda x: int(x.timestamp()))
        if not news_df['Date'].is_unique:
            # add a second to not unique timestamps
            grouped_df = news_df.groupby('Date')
            for timestamp, group in grouped_df.groups.items():
                if group.shape[0] > 1:
                    for index in group[1:]:
                        timestamp += 1
                        news_df.loc[index, 'Date'] = timestamp
        news_df.set_index('Date', verify_integrity=True, inplace=True)
        news_df.index.name = 'timestamp'

        tableName = 'news_'
        for c in symbol:
            if c.isalnum():
                tableName += c
            else:
                tableName += '_'
        
        # # write table
        # self.db.table_write(tableName, news_df, update=False)
        
        # # create reference
        # table_reference = pd.DataFrame({symbol: {'news': tableName}}).T
        # table_reference.index.name = 'symbol'
        # self.db.table_write('table_reference', table_reference)

        # update status
        print('bliep')
        status_info['last_timestamp'] = news_df.index[-1]
        status_info['last_timestamp_str'] = str(pd.to_datetime(status_info['last_timestamp'], unit='s'))
        status_info = pd.DataFrame({symbol: status_info}).T
        status_info.index.name = 'symbol'
        print(status_info)
        self.db.table_write('status_db', status_info)

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
