from .fmp import FMP
import logging
from ...database import Database

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

        self.logger.info('FMP:     FMP_Stocklist update')

        request_arguments = {
            'url': 'https://financialmodelingprep.com/api/v3/stock/list',
            # 'params': {},
            'timeout': 30,
        }
        self.request(request_arguments)

        self.logger.info('FMP:     FMP_Stocklist update done')

    def pushAPIData(self, response_data):
        write_data =  {}
        for entry in response_data:
            symbol = entry.pop('symbol')
            write_data[symbol] = entry
        self.db.table_write('stocklist', write_data, 'symbol', method='update')
        self.db.commit()

        # self.db.tableWrite('status_db', {'ALLSYMBOLS': {'stocklist': int(datetime.now().timestamp())}}, 'keySymbol', method='update')
