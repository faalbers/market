from .yahoof import YahooF
import logging, time
from ...database import Database
from ...utils import yfinancetest, storage
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

    def get_income_stmt_trailing(self, data):
        def proc_income_stmt_trailing(ticker, data):
            while True:
                try:
                    income_stmt_trailing = ticker.get_income_stmt(freq='trailing')
                    if income_stmt_trailing.empty:
                        data[0] = False
                        data[2] = 'income stmt trailing is empty'
                    else:
                        data[0] = True
                        data[1]['trailing'] = income_stmt_trailing
                        data[2] = 'ok'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        return [False, data, e]
                break
            return data
        # decide if we need to run this yfinace proc, the yfinance proc to run and the current data
        return [True, proc_income_stmt_trailing, data]
    
    def get_cash_flow_trailing(self, data):
        def proc_cash_flow_trailing(ticker, data):
            while True:
                try:
                    cash_flow_trailing = ticker.get_cash_flow(freq='trailing')
                    if not cash_flow_trailing.empty:
                        data[1]['trailing'] = pd.concat([data[1]['trailing'], cash_flow_trailing])
                        data[2] = 'ok'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        # decide if we need to run this yfinace proc, the yfinance proc to run and the current data
        if not data[0]: return [False, proc_cash_flow_trailing, data]
        return [True, proc_cash_flow_trailing, data]
    
    def get_income_stmt_yearly(self, data):
        def proc_income_stmt_yearly(ticker, data):
            while True:
                try:
                    income_stmt_yearly = ticker.get_income_stmt(freq='yearly')
                    if not income_stmt_yearly.empty:
                        data[1]['yearly'] = income_stmt_yearly
                        data[2] = 'ok'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        # decide if we need to run this yfinace proc, the yfinance proc to run and the current data
        if not data[0]: return [False, proc_income_stmt_yearly, data]
        return [True, proc_income_stmt_yearly, data]
    
    def get_cash_flow_yearly(self, data):
        def proc_cash_flow_yearly(ticker, data):
            while True:
                try:
                    cash_flow_yearly = ticker.get_cash_flow(freq='yearly')
                    if not cash_flow_yearly.empty:
                        data[1]['yearly'] = pd.concat([data[1]['yearly'], cash_flow_yearly])
                        data[2] = 'ok'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        # decide if we need to run this yfinace proc, the yfinance proc to run and the current data
        if not data[0]: return [False, proc_cash_flow_yearly, data]
        return [True, proc_cash_flow_yearly, data]
    
    def get_balance_sheet_yearly(self, data):
        def proc_balance_sheet_yearly(ticker, data):
            while True:
                try:
                    balance_sheet_yearly = ticker.get_balance_sheet(freq='yearly')
                    if not balance_sheet_yearly.empty:
                        data[1]['yearly'] = pd.concat([data[1]['yearly'], balance_sheet_yearly])
                        data[2] = 'ok'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        # decide if we need to run this yfinace proc, the yfinance proc to run and the current data
        if not data[0]: return [False, proc_balance_sheet_yearly, data]
        return [True, proc_balance_sheet_yearly, data]

    def get_income_stmt_quarterly(self, data):
        def proc_income_stmt_quarterly(ticker, data):
            while True:
                try:
                    income_stmt_quarterly = ticker.get_income_stmt(freq='quarterly')
                    if not income_stmt_quarterly.empty:
                        data[1]['quarterly'] = income_stmt_quarterly
                        data[2] = 'ok'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        # decide if we need to run this yfinace proc, the yfinance proc to run and the current data
        if not data[0]: return [False, proc_income_stmt_quarterly, data]
        return [True, proc_income_stmt_quarterly, data]
    
    def get_cash_flow_quarterly(self, data):
        def proc_cash_flow_quarterly(ticker, data):
            while True:
                try:
                    cash_flow_quarterly = ticker.get_cash_flow(freq='quarterly')
                    if not cash_flow_quarterly.empty:
                        data[1]['quarterly'] = pd.concat([data[1]['quarterly'], cash_flow_quarterly])
                        data[2] = 'ok'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        # decide if we need to run this yfinace proc, the yfinance proc to run and the current data
        if not data[0]: return [False, proc_cash_flow_quarterly, data]
        return [True, proc_cash_flow_quarterly, data]
    
    def get_balance_sheet_quarterly(self, data):
        def proc_balance_sheet_quarterly(ticker, data):
            while True:
                try:
                    balance_sheet_quarterly = ticker.get_balance_sheet(freq='quarterly')
                    if not balance_sheet_quarterly.empty:
                        data[1]['quarterly'] = pd.concat([data[1]['quarterly'], balance_sheet_quarterly])
                        data[2] = 'ok'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        # decide if we need to run this yfinace proc, the yfinance proc to run and the current data
        if not data[0]: return [False, proc_balance_sheet_quarterly, data]
        return [True, proc_balance_sheet_quarterly, data]

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
        updates = self.update_check(key_values, forced=forced)
        if len(updates['trailing']) == 0: return

        # leave if yfinance limit rate
        if not yfinancetest():
            self.logger.info('YahooF:  Fundamental: yfinance limit rate')
            return

        self.logger.info('YahooF:  Fundamental: update')
        self.logger.info('YahooF:  Fundamental: symbols processing : %s' % len(updates['trailing']))

        # backup first
        self.logger.info('YahooF:  Fundamental: %s' % self.db.backup())

        exec_list = []
        for symbol in updates['trailing']:
            exec_entity = [symbol, [
                    self.get_income_stmt_trailing,
                    self.get_cash_flow_trailing,
                ], {'ticker': None, 'data': [False, {}, '']}]
            if symbol in updates['yearly']:
                exec_entity[1].append(self.get_income_stmt_yearly)
                exec_entity[1].append(self.get_cash_flow_yearly)
                exec_entity[1].append(self.get_balance_sheet_yearly)
            if symbol in updates['quarterly']:
                exec_entity[1].append(self.get_income_stmt_quarterly)
                exec_entity[1].append(self.get_cash_flow_quarterly)
                exec_entity[1].append(self.get_balance_sheet_quarterly)
            exec_list.append(exec_entity)

        self.multi_execs(exec_list)

    def update_check(self, symbols, forced=False):
        status_db = self.db.table_read('status_db', keys=symbols)

        updates = {}

        if forced or status_db.empty:
            symbols = set(symbols)
            updates['trailing'] = symbols
            updates['yearly'] = symbols
            updates['quarterly'] = symbols
            return updates

        
        timestamp_pdt = int(datetime.now().timestamp())
        three_months_plus_ts = timestamp_pdt - (3600 * 24 * 108)
        half_year_plus_ts = timestamp_pdt - (3600 * 24 * 197)
        one_year_plus_ts = timestamp_pdt - (3600 * 24 * 375)
        one_year_half_ts = timestamp_pdt - (3600 * 24 * 548)

        missing_symbols = set(symbols).difference(set(status_db.index))

        found = status_db['found'] > 0
        
        update_trailing_quarterly = found & (status_db['last_timestamp_quarterly'] != 0) \
            & (status_db['last_timestamp_trailing'] < three_months_plus_ts) \
            & (status_db['last_timestamp_quarterly'] > half_year_plus_ts)
        update_trailing_yearly = found & (status_db['last_timestamp_yearly'] != 0) \
            & (status_db['last_timestamp_quarterly'] == 0) \
            & (status_db['last_timestamp_trailing'] < one_year_plus_ts) \
            & (status_db['last_timestamp_yearly'] > one_year_half_ts)
        update_trailing = update_trailing_quarterly | update_trailing_yearly
        updates['trailing'] = set(status_db[update_trailing].index).union(missing_symbols)

        update_yearly = found & (status_db['last_timestamp_yearly'] != 0) \
            & (status_db['last_timestamp_yearly'] < one_year_plus_ts) \
            & (status_db['last_timestamp_yearly'] > one_year_half_ts)
        updates['yearly'] = set(status_db[update_yearly].index).union(missing_symbols)

        update_quarterly = found & (status_db['last_timestamp_quarterly'] != 0) \
            & (status_db['last_timestamp_quarterly'] < three_months_plus_ts) \
            & (status_db['last_timestamp_quarterly'] > half_year_plus_ts)
        updates['quarterly'] = set(status_db[update_quarterly].index).union(missing_symbols)

        # print(status_db[update_trailing][['last_timestamp_trailing_str', 'last_timestamp_yearly_str', 'last_timestamp_quarterly_str']])

        # print(update_trailing)
        # print(update_yearly)
        # print(update_quarterly)

        return updates
    
    def push_api_data(self, symbol, result):
        found = result[0]
        message = result[2]
        result = result[1]

        timestamp = int(datetime.now().timestamp())
        status = {
            'timestamp': timestamp,
            'timestamp_str': str(datetime.fromtimestamp(timestamp)),
            'last_timestamp_trailing': 0,
            'last_timestamp_trailing_str': '',
            'last_timestamp_yearly': 0,
            'last_timestamp_yearly_str': '',
            'last_timestamp_quarterly': 0,
            'last_timestamp_quarterly_str': '',
            'found': found,
            'message': str(message)
        }

        if not found:
            status = pd.DataFrame([status], index=[symbol])
            status.index.name = 'symbol'
            self.db.table_write('status_db', status)
            return
        
        for period, df in result.items():
            print(symbol, period)
            df = df.T.infer_objects()
            df.index = df.index.tz_localize(None)
            df.index = df.index.astype('int64') // 10**9
            df.index.name = 'timestamp'
            df.sort_index(inplace=True)
            df = df.copy() # to avoid 'DataFrame is highly fragmented'
            if period == 'trailing':
                if df.shape[0] > 1:
                    df.iloc[-1] = df.sum()
                    df = df.iloc[-1:]
                df.reset_index(inplace=True)
                df.index = [symbol]
                df.index.name = 'symbol'
                self.db.table_write('trailing', df)
                status['last_timestamp_trailing'] = int(df.iloc[0]['timestamp'])
                status['last_timestamp_trailing_str'] = str(pd.to_datetime(status['last_timestamp_trailing'], unit='s'))
            elif period == 'yearly':
                self.db.table_write_reference(symbol, 'yearly', df, update=False)
                status['last_timestamp_yearly'] = int(df.index[-1])
                status['last_timestamp_yearly_str'] = str(pd.to_datetime(status['last_timestamp_yearly'], unit='s'))
            elif period == 'quarterly':
                self.db.table_write_reference(symbol, 'quarterly', df, update=False)
                status['last_timestamp_quarterly'] = int(df.index[-1])
                status['last_timestamp_quarterly_str'] = str(pd.to_datetime(status['last_timestamp_quarterly'], unit='s'))
        
        # write status
        status = pd.DataFrame([status], index=[symbol])
        status.index.name = 'symbol'
        self.db.table_write('status_db', status)

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'trailing':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('trailing', keys=key_values, columns=column_names)
                columns_rename = {x[0]: x[1] for x in columns if x[1] != None}
                if len(columns_rename) > 0:
                    data = data.rename(columns=columns_rename)
                return data
            else:
                data = self.db.table_read('trailing', keys=key_values)
                return data
        elif data_name == 'yearly':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.timeseries_read('yearly', keys=key_values, columns=column_names)
                columns_rename = {x[0]: x[1] for x in columns if x[1] != None}
                if len(columns_rename) > 0:
                    for symbol in data:
                        data[symbol] = data[symbol].rename(columns=columns_rename)
                return data
            else:
                data = self.db.timeseries_read('yearly', keys=key_values)
                return data
        elif data_name == 'quarterly':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.timeseries_read('quarterly', keys=key_values, columns=column_names)
                columns_rename = {x[0]: x[1] for x in columns if x[1] != None}
                if len(columns_rename) > 0:
                    for symbol in data:
                        data[symbol] = data[symbol].rename(columns=columns_rename)
                return data
            else:
                data = self.db.timeseries_read('quarterly', keys=key_values)
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
