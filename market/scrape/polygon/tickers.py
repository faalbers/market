from .polygon import Polygon
import logging
from ...database import Database
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Polygon_Tickers(Polygon):
    dbName = 'polygon_tickers'

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
        status = self.db.table_read('status_db', key_values=['tickers'], columns=['timestamp'])
        if status:
            if int((datetime.now() - relativedelta(months=6)).timestamp()) < status['tickers']['timestamp']: return

        self.logger.info('Polygon: Polygon_Tickers update')

        # backup first
        self.db.backup()

        request_arguments = {
            'url': 'https://api.polygon.io/v3/reference/tickers',
            'params': {
                'limit': 1000,
            },
        }

        self.request(request_arguments)

        # update status
        self.db.table_write('status_db', {'tickers': {'timestamp': int(datetime.now().timestamp())}}, 'table_name', method='update')

        self.logger.info('Polygon: Polygon_Tickers update done')

    def pushAPIData(self, response_data):
        write_data =  {}
        for entry in response_data:
            symbol = entry.pop('ticker')
            write_data[symbol] = entry
        self.db.table_write('tickers', write_data, 'symbol', method='update')
        
        # update on every page to not loose data
        self.db.commit()

        # self.db.tableWrite('status_db', {'ALLSYMBOLS': {'stocklist': int(datetime.now().timestamp())}}, 'keySymbol', method='update')
