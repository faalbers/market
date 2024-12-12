from .polygon import Polygon
import logging
from ...database import Database
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pp

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
        status = self.db.table_read('status_db', key_values=['tickers'], column_values=['timestamp'])
        if status:
            if int((datetime.now() - relativedelta(months=6)).timestamp()) < status['tickers']['timestamp']: return

        self.logger.info('Polygon: Polygon_Tickers update')

        # backup first
        self.db.backup()

        # get tickers
        request_arguments = {
            'url': 'https://api.polygon.io/v3/reference/tickers',
            'params': {
                'limit': 1000,
            },
        }

        self.request(request_arguments, self.push_tickers_data)

        # get types
        request_arguments = {
                'url': 'https://api.polygon.io/v3/reference/tickers/types',
        }

        self.request(request_arguments, self.push_types_data)

        # update status
        self.db.table_write('status_db', {'tickers': {'timestamp': int(datetime.now().timestamp())}}, 'table_name', method='update')

        self.logger.info('Polygon: Polygon_Tickers update done')

    def push_tickers_data(self, response_data):
        write_data =  {}
        for entry in response_data:
            symbol = entry.pop('ticker').upper()
            write_data[symbol] = entry
        self.db.table_write('tickers', write_data, 'symbol', method='update')
        
        # update on every page to not loose data
        self.db.commit()

    def push_types_data(self, response_data):
        write_data =  {}
        for entry in response_data:
            symbol = entry.pop('code')
            write_data[symbol] = entry
        self.db.table_write('types', write_data, 'code', method='update')
        
        # update on every page to not loose data
        self.db.commit()
