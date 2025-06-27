from .polygon import Polygon
import logging
from ...database import Database
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pp
import pandas as pd

class Polygon_Tickers(Polygon):
    dbName = 'polygon_tickers'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['tickers']
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
                if status_db.loc['tickers', 'timestamp'] > six_months_ts: return
        
        self.logger.info('Polygon: Polygon_Tickers update')

        # backup first
        self.logger.info('Polygon: Polygon_Tickers: %s' % self.db.backup())

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
        status_db = pd.DataFrame([{'timestamp': int(datetime.now().timestamp())}], index=['tickers'])
        status_db.index.name = 'table_name'
        self.db.table_write('status_db', status_db)

        self.logger.info('Polygon: Polygon_Tickers update done')

    def push_tickers_data(self, response_data):
        write_data =  []
        write_symbols = []
        for entry in response_data:
            # do not include these markets
            if entry['market'] in ['fx', 'crypto']: continue
            symbol = entry.pop('ticker').upper()

            # create correct ticker symbol
            if entry['market'] == 'stocks' and not symbol.isalpha() and 'type' in entry:
                if 'type' in entry and entry['type'] == 'UNIT':
                    # handle unit
                    symbol = symbol.replace('.U', '-UN')
                elif 'type' in entry and entry['type'] == 'WARRANT':
                    # handle warrant
                    symbol = symbol.replace('.WS.A', '-WT')
                    symbol = symbol.replace('.WS', '-WT')
            if entry['market'] == 'indices':
                # handle indices
                symbol = symbol.replace('I:', '^')
                entry['type'] = 'IX'
            if len(symbol) > 2 and symbol[-2] == '.':
                if symbol[-1] <= 'C':
                    # handle class ticker
                    symbol = symbol.replace('.', '-')
                else:
                    # handle other
                    symbol = symbol.replace('.', '')

            write_data.append(entry)
            write_symbols.append(symbol)
        
        write_data = pd.DataFrame(write_data, index=write_symbols)
        write_data = write_data.reset_index().drop_duplicates(subset='index', keep='last').set_index('index')
        write_data.index.name = 'symbol'
        self.db.table_write('tickers', write_data)

        # update on every page to not loose data
        self.db.commit()

    def push_types_data(self, response_data):
        write_data =  []
        write_symbols = []
        for entry in response_data:
            symbol = entry.pop('code')
            write_data.append(entry)
            write_symbols.append(symbol)
        
        write_data = pd.DataFrame(write_data, index=write_symbols)
        write_data.index.name = 'code'
        self.db.table_write('types', write_data)

        # update on every page to not loose data
        self.db.commit()        

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'tickers':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('tickers', keys=key_values, columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return (data, self.db.timestamp)
            else:
                data = self.db.table_read('tickers', keys=key_values)
                return (data, self.db.timestamp)

    def get_vault_params(self, data_name):
        if data_name == 'tickers':
            column_types = self.db.get_table_info('tickers')['columnTypes']
            column_types.pop('symbol')
            return column_types
