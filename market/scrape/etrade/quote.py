from .etrade import Etrade
from ...database import Database
import logging
from pprint import pp

class Etrade_Quote(Etrade):
    dbName = 'etrade_quote'

    @staticmethod
    def get_table_names(table_name):
        # if table_name == 'all':
        #     return ['info']
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        self.logger.info('Etrade: update')

        # # backup first
        # self.db.backup()

        symbols = key_values
        block_size = 50
        block_end = 0
        symbol_blocks = []
        for block_idx in range(int(len(symbols)/block_size)):
            block_start = block_idx*block_size
            block_end = block_start+block_size
            symbol_blocks.append(symbols[block_start:block_end])
        if len(symbols)%block_size > 0:
            symbol_blocks.append(symbols[block_end:])
        for symbol_block in symbol_blocks:
            symbols_string = ','.join(symbol_block)
            detail_flag = 'ALL'
            request_arguments = {
                'url': 'https://api.etrade.com/v1/market/quote/%s.json' % symbols_string,
                'params': {
                    'detailFlag': 'ALL',
                    'overrideSymbolCount': 'true',
                },
            }


        self.logger.info('Etrade:   update done')
