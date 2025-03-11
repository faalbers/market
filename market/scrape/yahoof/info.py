from .yahoof import YahooF
import logging, time
from ...database import Database
from pprint import pp
import yfinance as yf
from datetime import datetime
import pandas as pd

class YahooF_Info(YahooF):
    dbName = 'yahoof_info'

    @staticmethod
    def get_table_names(table_name):
        return [table_name]
    
    def get_info(self, symbol):
        while True:
            ticker = yf.Ticker(symbol)
            try:
                info = ticker.info
            except Exception as e:
                if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                    self.logger.info('YahooF:  Rate Limeit: wait 120 seconds')
                    time.sleep(120)
                    continue
                else:
                    return ([False, None, e])

            return ([True, info, 'ok'])
                    
    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        # make yfinance non verbose
        yflogger = logging.getLogger('yfinance')
        # yflogger.disabled = True
        # yflogger.propagate = False
        file_handler = logging.FileHandler('yfinance.log')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s: %(levelname)s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        yflogger.addHandler(file_handler)

        # check what symbols need to be updated
        symbols = self.update_check(key_values)
        if len(symbols) == 0: return

        self.logger.info('YahooF:  Info: update')
        self.logger.info('YahooF:  Info: symbols processing : %s' % len(symbols))

        # backup first
        self.db.backup()

        exec_list = [[symbol, self.get_info, {'symbol': symbol}] for symbol in symbols]
        self.multi_execs(exec_list)

    def update_check(self, symbols):
        db_status = self.db.table_read('status_db')
        
        # found is 24 h check
        found_update = int(datetime.now().timestamp()) - 86400
        # not found is 1/2 year check
        not_found_update = int(datetime.now().timestamp()) - (86400 * 182)

        update_symbols = []
        for symbol in symbols:
            if not symbol in db_status:
                # never done before, add it
                update_symbols.append(symbol)
            else:
                if db_status[symbol]['found']:
                    # found before, only do again after 24 h
                    if db_status[symbol]['timestamp'] <= found_update: update_symbols.append(symbol)
                else:
                    # not found before, only try again after 1/2 year
                    if db_status[symbol]['timestamp'] <= not_found_update: update_symbols.append(symbol)

        return update_symbols

    def push_api_data(self, symbol, result):
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ': ', symbol)
        timestamp = int(datetime.now().timestamp())
        found = result[0]
        status_info = {
            'timestamp': timestamp,
            'found': found,
            'message': str(result[2])
        }

        self.db.table_write('status_db', {symbol: status_info}, key_name='symbol', method='update')
        if not found:
            print('\t%s' % result[2])
            return
        result = result[1]
        
        result['timestamp'] = timestamp
        self.db.table_write('info', {symbol: result}, key_name='symbol', method='replace')
