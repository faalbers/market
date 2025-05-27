from .yahoof import YahooF
import logging, time
from ...database import Database
from ...utils import yfinancetest
from datetime import datetime, UTC
from pprint import pp
import pandas as pd
from dateutil.relativedelta import relativedelta
from multiprocessing import Pool

class YahooF_Fundamental(YahooF):
    dbName = 'yahoof_fundamental'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['fundamental']
        return [data_name]

    def get_balance_sheet(self, data={}):
        def proc_balance_sheet(ticker, data):
            while True:
                try:
                    data = ticker.balance_sheet
                    if data.empty: return [False, data, 'balance_sheet is empty']
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        return [False, data, e]
                break
            return [True, data, 'ok']
        return [True, proc_balance_sheet, data]
    
    def get_income_stmt(self, data):
        def proc_income_stmt(ticker, data):
            while True:
                try:
                    income_stmt = ticker.income_stmt
                    data[1] = pd.concat([data[1], income_stmt])
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        if not data[0]: return [False, proc_income_stmt, data]
        return [True, proc_income_stmt, data]

    def get_cash_flow(self, data):
        def proc_cash_flow(ticker, data):
            while True:
                try:
                    cash_flow = ticker.cash_flow
                    data[1] = pd.concat([data[1], cash_flow])
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        if not data[0]: return [False, proc_cash_flow, data]
        return [True, proc_cash_flow, data]

    def __init__(self, key_values=[], data_names=[], update = False, forced=False):
        self.db = Database(self.dbName)
        if not update: return
        self.logger = logging.getLogger('vault_multi')
        super().__init__()

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
        if forced:
            symbols = sorted(key_values)
        else:
            symbols = self.update_check(key_values)
        if len(symbols) == 0: return

        # leave if yfinance limit rate
        if not yfinancetest():
            self.logger.info('YahooF:  Fundamental: yfinance limit rate')
            return

        self.logger.info('YahooF:  Fundamental: update')
        self.logger.info('YahooF:  Fundamental: symbols processing : %s' % len(symbols))

        # backup first
        self.logger.info('YahooF:  Fundamental: %s' % self.db.backup())

        exec_list = [
            [symbol, [
                    self.get_balance_sheet,
                    self.get_income_stmt,
                    self.get_cash_flow,
                ], {'ticker': None, 'data': {}}] for symbol in symbols]
        self.multi_execs(exec_list, yfinance_ok=True)

    def update_check(self, symbols):
        status_db = self.db.table_read('status_db', keys=symbols)

        timestamp_pdt = int(datetime.now().timestamp())
        one_year_plus_ts = timestamp_pdt - (3600 * 24 * 375)
        two_year_ts = timestamp_pdt - (3600 * 24 * 365 * 2)

        update_found = (status_db['found'] > 0) & (status_db['last_timestamp'] < one_year_plus_ts) & (status_db['last_timestamp'] > two_year_ts)
        update_found = set(status_db[update_found].index)
        
        update_new = set(symbols).difference(set(status_db.index))
        
        update = update_found.union(update_new)
        
        return sorted(update)
    
    def push_api_data(self, symbol, result):
        found = result[0]
        message = result[2]
        result = result[1]


        timestamp = int(datetime.now().timestamp())
        status = {
            'timestamp': timestamp,
            'timestamp_str': str(datetime.fromtimestamp(timestamp)),
            'last_timestamp': 0,
            'last_timestamp_str': '',
            'found': found,
            'message': str(message)
        }
        if not found:
            status = pd.DataFrame([status], index=[symbol])
            status.index.name = 'symbol'
            self.db.table_write('status_db', status)
            return
        
        result = result.T.infer_objects()
        
        # take out utc time of indices and change them to timestamps, rename index
        result.index = result.index.tz_localize(None)
        result.index = result.index.astype('int64') // 10**9
        result.index.name = 'timestamp'
        result.sort_index(inplace=True)
        self.db.table_write_reference(symbol, 'fundamental', result, replace=True)

        # write status
        status['last_timestamp'] = int(result.index[-1])
        status['last_timestamp_str'] = str(pd.to_datetime(status['last_timestamp'], unit='s'))
        status = pd.DataFrame([status], index=[symbol])
        status.index.name = 'symbol'
        self.db.table_write('status_db', status)

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'fundamental':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.timeseries_read('fundamental', keys=key_values, columns=column_names)
                columns_rename = {x[0]: x[1] for x in columns if x[1] != None}
                if len(columns_rename) > 0:
                    for symbol in data:
                        data[symbol] = data[symbol].rename(columns=columns_rename)
                return data
            else:
                data = self.db.timeseries_read('fundamental', keys=key_values)
                return data

    def get_vault_params(self, data_name):
        if data_name == 'fundamental':
            references = sorted(self.db.table_read_df('table_reference')['fundamental'])
            max_len = 0
            for reference in references:
                column_types = self.db.get_table_info(reference)['columnTypes']
                column_types.pop('timestamp')
                # if len(column_types) > max_len:
                #     max_len = len(column_types)
                #     print(max_len)
                if len(column_types) >= 219: return(column_types)
