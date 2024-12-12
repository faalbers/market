from .fmp import FMP
import logging
from ...database import Database
from datetime import datetime
from dateutil.relativedelta import relativedelta

class FMP_Stocklist(FMP):
    dbName = 'fmp_stocklist'

    @staticmethod
    def get_table_names(table_name):
        # if table_name == 'all':
        #     return list(const.QUOTESUMMARY_MODULES.keys())
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        # updated if longer then 60 half a year ago or initial version
        status = self.db.table_read('status_db', key_values=['stocklist'], column_values=['table_name', 'timestamp'])
        if status:
            if int((datetime.now() - relativedelta(months=6)).timestamp()) < status['stocklist']['timestamp']: return

        self.logger.info('FMP:     FMP_Stocklist update')
        
        # backup first
        self.db.backup()

        request_arguments = {
            'url': 'https://financialmodelingprep.com/api/v3/stock/list',
            # 'params': {},
            'timeout': 30,
        }
        self.request(request_arguments)
        
        # update status
        self.db.table_write('status_db', {'stocklist': {'timestamp': int(datetime.now().timestamp())}}, 'table_name', method='update')

        self.logger.info('FMP:     FMP_Stocklist update done')

    def pushAPIData(self, response_data):
        write_data =  {}
        for entry in response_data:
            symbol = entry.pop('symbol').upper()
            write_data[symbol] = entry
        self.db.table_write('stocklist', write_data, 'symbol', method='update')
