from .yahoof import YahooF
import logging, time
from ...database import Database
from pprint import pp
import yfinance as yf
from datetime import datetime

class YahooF_Chart(YahooF):
    dbName = 'yahoof_chart'

    @staticmethod
    def get_table_names(table_name):
        return [table_name]

    def get_chart(self, data=None):
        def proc_chart(ticker, data):
            while True:
                try:
                    info = ticker.info
                    chart = ticker.history(period="10y",auto_adjust=False)
                    data = chart
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  chart: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        return ([False, data, e])
                break
            if chart.shape[0] == 0:
                return ([False, data, 'empty'])
            return ([True, data, 'ok'])
        return [True, proc_chart, data]

    def get_chart_old(self, symbol):
        while True:
            try:
                ticker = yf.Ticker(symbol)
                chart = ticker.history(period="10y",auto_adjust=False)
            except Exception as e:
                if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                    self.logger.info('YahooF:  Rate Limeit: wait 60 seconds')
                    time.sleep(60)
                    continue
                else:
                    return ([False, None, e])
            if chart.shape[0] == 0:
                return ([False, None, 'empty'])
            return ([True, chart, 'ok'])

    def __init__(self, key_values=[], table_names=[]):
        self.logger = logging.getLogger('vault_multi')
        super().__init__()
        self.db = Database(self.dbName)

        # make yfinance log into a file
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
        # symbols = key_values
        if len(symbols) == 0: return

        self.logger.info('YahooF:  Chart: update')
        self.logger.info('YahooF:  Chart: symbols processing : %s' % len(symbols))

        # backup first
        self.db.backup()

        exec_list = [
            [symbol, [
                    self.get_chart,
                ], {'ticker': None, 'data': None}] for symbol in symbols]
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
        timestamp = int(datetime.now().timestamp())
        found = result[0]
        status_info = {
            'timestamp': timestamp,
            'found': found,
            'message': str(result[2])
        }
        self.db.table_write('status_db', {symbol: status_info}, key_name='symbol', method='update')
        if not found: return
        result = result[1]

        # make unique table name
        table_name = 'chart_'
        for c in symbol:
            if c.isalnum():
                table_name += c
            else:
                table_name += '_'

        # take out utc time of indices and change them to timestamps, rename index
        result.index = result.index.tz_localize(None)
        result.index = result.index.astype('int64') // 10**9
        result.index.name = 'timestamp'

        # write table
        self.db.table_write_df(table_name, result)
        
        # write table reference
        self.db.table_write('table_reference', {symbol: {'chart': table_name}}, 'symbol', method='append')
