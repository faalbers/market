from .fmp import FMP
from multiprocessing import get_logger
from time import sleep
import logging

class FMP_Stocklist(FMP):
    dbName = 'fmp_stocklist'

    @staticmethod
    def get_table_names(table_name):
        # if table_name == 'all':
        #     return list(const.QUOTESUMMARY_MODULES.keys())
        return [table_name]

    def __init__(self, key_values=[], table_names=[]):
        super().__init__()
        self.logger = logging.getLogger('vault_multi')

        self.logger.info('FMP:FMP_Stocklist start')

        # self.logger.info(self.dbName)
        # self.logger.info(key_values)
        # self.logger.info(table_names)
        # for x in range(10):
        #     self.logger.info('FMP: Still to do: %s' % x)
        #     sleep(1)

        # self.logger.info('FMP_Stocklist: Done')

