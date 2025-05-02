from .yahoof import YahooF
import logging, time, os
from ...database import Database
from ...utils import storage
from pprint import pp
import yfinance as yf
from datetime import datetime
from multiprocessing import Pool
import pandas as pd

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

    def __init__(self, key_values=[], table_names=[], forced=False):
        self.db = Database(self.dbName)
        if len(key_values) == 0: return
        self.logger = logging.getLogger('vault_multi')
        super().__init__()

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
        if forced:
            symbols = sorted(key_values)
        else:
            symbols = self.update_check(key_values)
        if len(symbols) == 0: return

        # leave if yfinance limit rate
        if not self.yfinance_ok(): return

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
        
        # found is 1 days check
        found_update = int(datetime.now().timestamp()) - (3600 * 24 * 1)
        # not found is 1/2 year check
        not_found_update = int(datetime.now().timestamp()) - (3600 * 24 * 182)

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

    @staticmethod
    # def reference_chunk(data):
    def reference_chunk(data):
        symbols = data[0]
        db_name = data[1]
        db = Database(db_name)

        charts = {}
        for symbol, symbol_chart_table in symbols.items():
            chart = db.table_read(symbol_chart_table)
            df = pd.DataFrame(chart).T
            df.index = pd.to_datetime(df.index, unit='s')
            df.sort_index(inplace=True)
            df.index = df.index.floor('D') # set it to beginning of day
            df = df.drop('timestamp', axis=1)
            charts[symbol] = df
        return charts
    
    def cache_data(self, symbols):
        # get cache info
        db_storage = 'database/%s' % self.dbName
        db_storage_timestamp = storage.timestamp(db_storage)
        charts = {}
        if db_storage_timestamp != None:
            charts = storage.load(db_storage)
        
        # get get chart symbols that need updated
        table_reference = pd.DataFrame(self.db.table_read('table_reference')).T
        if len(charts) > 0:
            status_db = pd.DataFrame(self.db.table_read('status_db')).T
            status_db = status_db.loc[table_reference.index]
            status_db = status_db[(status_db['found'] == 1) & (status_db['timestamp'] > db_storage_timestamp)]
            chart_symbols = sorted(status_db.index)
        else:
            chart_symbols = sorted(table_reference.index)
        if len(chart_symbols) == 0: return
        
        logger = logging.getLogger('Market')
        logger.info('YahooF:  Chart: update cache for %s symbols. can not be interrupted with stop text !' % len(chart_symbols))

        # gather symbol chunks based on cpu count
        cpus = 8
        symbols_limit = int(len(chart_symbols)/cpus)
        if len(chart_symbols) % cpus > 0: symbols_limit += 1
        symbol_chunks = []
        limit_idx = symbols_limit
        while limit_idx < (len(chart_symbols)+1):
            symbol_chunk = chart_symbols[limit_idx-symbols_limit:limit_idx]
            dict_chunk = {symbol: table_reference.loc[symbol, 'chart'] for symbol in symbol_chunk}
            symbol_chunks.append((dict_chunk, self.dbName))
            limit_idx += symbols_limit
        left_idx = len(chart_symbols) % symbols_limit
        if left_idx > 0:
            symbol_chunk = chart_symbols[-left_idx:]
            dict_chunk = {symbol: table_reference.loc[symbol, 'chart'] for symbol in symbol_chunk}
            symbol_chunks.append((dict_chunk, self.dbName))

        with Pool(processes=cpus) as pool:
            results = pool.map(YahooF_Chart.reference_chunk, symbol_chunks)
            for result in results:
                charts.update(result)

        # backup and write to storage
        logger.info('YahooF:  Chart: backup cache ...')
        storage.backup(db_storage)
        logger.info('YahooF:  Chart: saving updated cache ...')
        storage.save(charts, db_storage)
        logger.info('YahooF:  Chart: saving cache done')
