from .fmp import FMP
import logging
from ...database import Database
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

class FMP_Stocklist(FMP):
    dbName = 'fmp_stocklist'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['stocklist']
        return [data_name]

    def __init__(self, key_values=[], data_names=[], update = False, forced=False):
        self.db = Database(self.dbName)
        if not update: return
        self.logger = logging.getLogger('vault_multi')
        super().__init__()

        # updated if longer then half a year ago or initial version
        if not forced:
            status_db = self.db.table_read('status_db')
            if status_db.shape[0] > 0:
                timestamp_pdt = int(datetime.now().timestamp())
                six_months_ts = timestamp_pdt - (3600 * 24 * 182)
                if status_db.loc['stocklist', 'timestamp'] > six_months_ts: return

        self.logger.info('FMP:     FMP_Stocklist update')
        
        # backup first
        self.logger.info('FMP:     FMP_Stocklist: %s' % self.db.backup())

        request_arguments = {
            'url': 'https://financialmodelingprep.com/api/v3/stock/list',
            # 'params': {},
            'timeout': 30,
        }
        self.request(request_arguments)
        
        # update status
        status_db = pd.DataFrame([{'timestamp': int(datetime.now().timestamp())}], index=['stocklist'])
        status_db.index.name = 'table_name'
        self.db.table_write('status_db', status_db)

        self.logger.info('FMP:     FMP_Stocklist update done')

    def pushAPIData(self, response_data):
        write_data =  []
        write_symbols = []
        exchange_us = ['NYSE', 'NASDAQ', 'PNK', 'OTC', 'AMEX', 'CBOE']
        for entry in response_data:
            if not entry['exchangeShortName'] in exchange_us: continue
            symbol = entry.pop('symbol').upper()
            write_data.append(entry)
            write_symbols.append(symbol)
        
        write_data = pd.DataFrame(write_data, index=write_symbols)
        write_data.index.name = 'symbol'
        self.db.table_write('stocklist', write_data, replace=True)

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'stocklist':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('stocklist', keys=key_values, columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return (data, self.db.timestamp)
            else:
                data = self.db.table_read('stocklist', keys=key_values)
                return (data, self.db.timestamp)

    def get_vault_params(self, data_name):
        if data_name == 'stocklist':
            column_types = self.db.get_table_info('stocklist')['columnTypes']
            column_types.pop('symbol')
            return column_types
