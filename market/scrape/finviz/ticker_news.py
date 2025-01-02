from .finviz import Finviz
import logging
from ...database import Database
from pprint import pp
import pandas as pd
from ...utils import stop_text

class Finviz_Ticker_News(Finviz):
    dbName = 'finviz_ticker_news'

    @staticmethod
    def get_table_names(table_name):
        # if table_name == 'all':
        #     return list(const.QUOTESUMMARY_MODULES.keys())
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        if len(key_values) == 0: return

        self.logger.info('Finviz:  Finviz_Ticker_News update')

        # backup first
        self.db.backup()

        symbols_done = 0
        for symbol in key_values:
            if (symbols_done % 100) == 0:
                self.db.commit()
                self.logger.info('Finviz:  symbols still to do: %s' % (len(key_values) - symbols_done))
            self.request_news(symbol)
            # break
            symbols_done += 1
            if stop_text():
                self.logger.info('Finviz:  manually stopped request')
                self.logger.info('Finviz:  symbols done       : %s' % symbols_done)
                self.db.commit()
                break

        self.logger.info('Finviz:  Finviz_Ticker_News update done')

    def pushAPIData(self, symbol,news_df):
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
        
        # make unique table name
        tableName = 'news_'
        for c in symbol:
            if c.isalnum():
                tableName += c
            else:
                tableName += '_'
        
        # write ticker news table and update table reference
        self.db.table_write(tableName, news_df.T.to_dict(), 'timestamp', method='append')
        self.db.table_write('table_reference', {symbol: {'news': tableName}}, 'symbol', method='append')
