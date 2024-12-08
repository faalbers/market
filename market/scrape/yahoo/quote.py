from .yahoo import Yahoo
from multiprocessing import get_logger
import logging
from ...database import Database
from time import sleep

class Yahoo_Quote(Yahoo):
    dbName = 'yahoo_quote'

    @staticmethod
    def get_table_names(table_name):
        # if table_name == 'all':
        #     return list(const.QUOTESUMMARY_MODULES.keys())
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        symbol_modules = {symbol: table_names for symbol in key_values}

        if len(symbol_modules) == 0: return

        self.logger.info('Yahoo: Yahoo_Quote update')
        self.logger.info('Yahoo: requested modules  : %s' % ' '.join(table_names))
        self.logger.info('Yahoo: symbols processing : %s' % len(key_values))

        # create request arguments list
        requests_list = []
        modules_processing = set()
        for symbol, modules in symbol_modules.items():
            modules_processing = modules_processing.union(modules)
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
        self.logger.info('Yahoo: modules processing : %s' % " ".join(modules_processing))
        self.multi_symbols_request(requests_list)
        
    def pushAPIData(self, symbol, response_data):
        for module, module_data in response_data.items():
            self.db.table_write(module, {symbol: module_data}, 'symbol', method='replace')

