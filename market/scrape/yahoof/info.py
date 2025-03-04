from .yahoof import YahooF
import logging
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
    
    # statcmethod
    def get_info(symbol):
        ticker = yf.Ticker(symbol)
        try:
            info = ticker.info
        except:
            return (False, None)
        return (True, info)

        # try:
        #     data = yf.download(ticker)
        #     return data
        # except HTTPError as e:
        #     if e.response.status_code == 429 or e.response.status_code == 503:
        #         print(f"Rate limit hit or service unavailable. Retrying in {retry_delay} seconds...")
        #         time.sleep(retry_delay)
        #     else:
        #         print(f"HTTP error occurred: {e}")
        #         break  # Exit the loop for non-retryable HTTP errors
        # except Exception as e:
        #      print(f"An unexpected error occurred: {e}")
        #      break # Exit the loop for unexpected errors
    
    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        # # make yfinance non verbose
        # yflogger = logging.getLogger('yfinance')
        # yflogger.disabled = True
        # yflogger.propagate = False

        # check what symbols need to be updated
        symbols = self.update_check(key_values)
        if len(symbols) == 0: return

        self.logger.info('YahooF:  Info: update')
        self.logger.info('YahooF:  Info: symbols processing : %s' % len(symbols))

        exec_list = [[symbol, YahooF_Info.get_info, {'symbol': symbol}] for symbol in symbols]
        self.multi_execs(exec_list)

    def update_check(self, symbols):
        db_status = self.db.table_read('status_db', key_values=symbols)
        
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

    def push_api_data(self, symbol, success, result):
        timestamp = int(datetime.now().timestamp())
        self.db.table_write('status_db', {symbol: {'timestamp': timestamp, 'found': success}}, key_name='symbol', method='update')
        if not success: return
        
        result['timestamp'] = timestamp
        self.db.table_write('info', {symbol: result}, key_name='symbol', method='replace')
