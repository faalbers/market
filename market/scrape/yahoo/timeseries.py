from .yahoo import Yahoo
import logging
from ...database import Database
from . import const
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pprint import pp

class Yahoo_Timeseries(Yahoo):
    dbName = 'yahoo_timeseries'

    @staticmethod
    def get_table_names(table_name):
        if table_name == 'all':
            modules = []
            for ts_type in ['financials', 'cashFlow']:
                for module in const.FUNDAMENTALS_KEYS[ts_type]:
                    for frequency in ['quarterly', 'annual', 'trailing']:
                        modules.append(f'{frequency}{module}')
            for module in const.FUNDAMENTALS_KEYS['balanceSheet']:
                for frequency in ['quarterly', 'annual', 'trailing']:
                    modules.append(f'{frequency}{module}')
            return modules
            return [
                'quarterly_financials', 'annual_financials', 'trailing_financials',
                'quarterly_balanceSheet', 'annual_balanceSheet',
                'quarterly_cashFlow', 'annual_cashFlow', 'trailing_cashFlow',
            ]
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        # find the ones that need updating
        symbol_modules = {}
        symbols = set(key_values)
        now = datetime.now()
        for table_name in table_names:
            if table_name.startswith('annual') or table_name.startswith('trailing'):
                timestamp_update = int((now - relativedelta(years=1)).timestamp())
            elif table_name.startswith('quarterly'):
                timestamp_update = int((now - relativedelta(months=3)).timestamp())
            else: continue

            table_data = self.db.table_read(table_name, key_values=key_values)
            for symbol in symbols.difference(table_data.keys()):
                # add module to symbols that are not in it
                if symbol not in symbol_modules: symbol_modules[symbol] = []
                symbol_modules[symbol].append(table_name)
            for symbol, symbol_value in  table_data.items():
                if timestamp_update > symbol_value['timestamp_latest']:
                    # add module to symbol if symbol needs updating
                    if symbol not in symbol_modules: symbol_modules[symbol] = []
                    symbol_modules[symbol].append(table_name)

        if len(symbol_modules) == 0: return

        self.logger.info('Yahoo:   Timeseries: update')
        self.logger.info('Yahoo:   Timeseries: requested modules  : %s' % len(table_names))
        self.logger.info('Yahoo:   Timeseries: symbols processing : %s' % len(key_values))

        # backup first
        self.db.backup()

        # create request arguments list
        requests_list = []
        now = datetime.now()
        period1 = int((now - relativedelta(years=10)).timestamp())
        period2 = int(now.timestamp())
        max_modules = 500
        for symbol, modules in symbol_modules.items():
            for modules_chunk in [modules[i:i + max_modules] for i in range(0, len(modules), max_modules)]:
                modules_string = ','.join(modules_chunk)
                request_arguments = {
                    'url': 'https://query2.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/'+symbol.upper(),
                    'params': {
                        'type': modules_string,
                        'period1': period1,
                        'period2': period2,
                    },
                    'timeout': 30,
                }                      
                requests_list.append((symbol,request_arguments))
        
        self.multi_request(requests_list)

        self.logger.info('Yahoo:   Timeseries update done')

    def push_api_data(self, symbol, response_data, request_arguments):
        symbol = symbol.upper()
        requested_ts_types = set(request_arguments['params']['type'].split(','))
        found_ts_types = set()
        response_data = response_data['timeseries']
        success = False
        if response_data['error']:
            if response_data['error']['code'] != 'Not Found':
                self.logger.info('Yahoo:   Timeseries: %s: %s' % (symbol, response_data['error']['code']))
        elif response_data['result']:
            for type_data in response_data['result']:
                ts_type = type_data['meta']['type'][0]
                if not ts_type in type_data: continue
                type_data = type_data[ts_type]
                write_data = {}
                if len(type_data) > 0:
                    last_timestamp = 0
                    write_data[symbol] = {}
                    for entry in type_data:
                        write_data[symbol]['currency'] = entry['currencyCode']
                        write_data[symbol][entry['asOfDate']] = entry['reportedValue']['raw']
                        entry_timestamp = int(datetime.strptime(entry['asOfDate'], '%Y-%m-%d').timestamp())
                        if entry_timestamp > last_timestamp: last_timestamp = entry_timestamp
                    write_data[symbol]['timestamp_latest'] = last_timestamp
                if len(write_data) > 0:
                    self.db.table_write(ts_type, write_data, 'symbol', method='update')
                    found_ts_types.add(ts_type)
            success = True
        
        # those not found , fill in current timestamp as latest
        timestamp_latest = int(datetime.now().timestamp())
        for ts_type in requested_ts_types.difference(found_ts_types):
            self.db.table_write(ts_type, {symbol: {'timestamp_latest': timestamp_latest}}, 'symbol', method='update')
        
        return success

