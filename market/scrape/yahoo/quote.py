from .yahoo import Yahoo
import logging
from ...database import Database
from . import const
from datetime import datetime

class Yahoo_Quote(Yahoo):
    dbName = 'yahoo_quote'

    @staticmethod
    def get_table_names(table_name):
        if table_name == 'all':
            return list(const.QUOTESUMMARY_MODULES.keys())
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        symbol_modules = {symbol: table_names for symbol in key_values}

        if len(symbol_modules) == 0: return

        self.logger.info('Yahoo:   Quote: update')
        self.logger.info('Yahoo:   Quote: requested modules  : %s' % ' '.join(table_names))
        self.logger.info('Yahoo:   Quote: symbols processing : %s' % len(key_values))

        # create request arguments list
        requests_list = []
        for symbol, modules in symbol_modules.items():
            modules_string = ','.join(modules)
            request_arguments = {
                'url': 'https://query2.finance.yahoo.com/v10/finance/quoteSummary/'+symbol.upper(),
                'params': {
                    'modules': modules_string,
                    'corsDomain': 'finance.yahoo.com',
                    'formatted': 'false',
                },
                'timeout': 30,
            }
            requests_list.append((symbol,request_arguments))
        self.multi_request(requests_list)

        self.logger.info('Yahoo:   Yahoo_Quote update done')

    def pushAPIData(self, symbol, response_data):
        response_data = response_data['quoteSummary']
        if response_data['error']:
            if response_data['error']['code'] != 'Not Found':
                self.logger.info('Yahoo:   Quote: %s: %s' % (symbol, response_data['error']['code']))
            return False
        elif response_data['result']:
            timestamp = int(datetime.now().timestamp())
            for module, module_data in response_data['result'][0].items():
                module_data['timestamp'] = timestamp
                self.db.table_write(module, {symbol: module_data}, 'symbol', method='replace')
            return True
        return False

