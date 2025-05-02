from .yahoof import YahooF
import logging, time
from ...database import Database
from datetime import datetime
from pprint import pp
import pandas as pd
from dateutil.relativedelta import relativedelta

class YahooF_Fundamental(YahooF):
    dbName = 'yahoof_fundamental'

    @staticmethod
    def get_table_names(table_name):
        if table_name == 'all':
            return ['fundamental']
        return [table_name]

    def get_balance_sheet(self, data={}):
        def proc_balance_sheet(ticker, data):
            while True:
                try:
                    balance_sheet = ticker.balance_sheet
                    balance_sheet = balance_sheet.T
                    balance_sheet.index = balance_sheet.index.astype('int64') // 10**9
                    for index, row in balance_sheet.iterrows():
                        data[index] = row.dropna().to_dict()
                    if len(data) == 0: return ([False, data, 'balance_sheet is empty'])
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
                    income_stmt = income_stmt.T
                    income_stmt.index = income_stmt.index.astype('int64') // 10**9
                    for index, row in income_stmt.iterrows():
                        row_data = row.dropna().to_dict()
                        if not index in data[1]:
                            data[1][index] = row_data
                        else:
                            data[1][index].update(row_data)
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
                    cash_flow = cash_flow.T
                    cash_flow.index = cash_flow.index.astype('int64') // 10**9
                    for index, row in cash_flow.iterrows():
                        row_data = row.dropna().to_dict()
                        if not index in data[1]:
                            data[1][index] = row_data
                        else:
                            data[1][index].update(row_data)
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        if not data[0]: return [False, proc_cash_flow, data]
        return [True, proc_cash_flow, data]

    def __init__(self, key_values=[], table_names=[], forced=False):
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
        if forced:
            symbols = sorted(key_values)
        else:
            symbols = self.update_check(key_values)
        if len(symbols) == 0: return

        # leave if yfinance limit rate
        if not self.yfinance_ok(): return

        self.logger.info('YahooF:  Fundamental: update')
        self.logger.info('YahooF:  Fundamental: symbols processing : %s' % len(symbols))

        # backup first
        self.db.backup()

        exec_list = [
            [symbol, [
                    self.get_balance_sheet,
                    self.get_income_stmt,
                    self.get_cash_flow,
                ], {'ticker': None, 'data': {}}] for symbol in symbols]
        self.multi_execs(exec_list, yfinance_ok=True)

    def update_check(self, symbols):
        db_status = self.db.table_read('status_db')

        now = datetime.now()
        months_3 = (now - relativedelta(months=3)).timestamp()
        months_12 = (now - relativedelta(months=12)).timestamp()
        months_18 = (now - relativedelta(months=18)).timestamp()

        update_symbols = []
        for symbol in symbols:
            if not symbol in db_status:
                # never done before, add it
                update_symbols.append(symbol)
            elif db_status[symbol]['timestamp'] < months_3 and db_status[symbol]['found']:
                    # if it's longer than 3 months and it's found before
                    if db_status[symbol]['last_timestamp'] < months_12 and db_status[symbol]['last_timestamp'] > months_18:
                        # only redo if it's between 12 and 18 months. If longer, it probably will not be updated again
                        update_symbols.append(symbol)

        return update_symbols
    
    def push_api_data(self, symbol, result):
        timestamp = int(datetime.now().timestamp())
        found = result[0]
        status_info = {
            'timestamp': timestamp,
            'timestamp_str': str(datetime.fromtimestamp(timestamp)),
            'last_timestamp': 0,
            'last_timestamp_str': '',
            'found': found,
            'message': str(result[2])
        }
        if not found:
            self.db.table_write('status_db', {symbol: status_info}, key_name='symbol', method='replace')
            return
        result = result[1]
        status_info['last_timestamp'] = sorted(result, reverse=True)[0]
        status_info['last_timestamp_str'] = str(datetime.fromtimestamp(status_info['last_timestamp']))

        # make unique table name
        table_name = 'fundamental_'
        for c in symbol:
            if c.isalnum():
                table_name += c
            else:
                table_name += '_'

        # get newly found result
        result_df = pd.DataFrame(result).T
        result_df.sort_index(inplace=True)
        result_df.index.name = 'timestamp'

        # we need to commit everything before reading from database
        self.db.commit()
        current_df = self.db.table_read_df(table_name, index_column='timestamp')
        if not current_df.empty:
            # update current data with new data
            current_df.update(result_df)
            result_concat = result_df[~result_df.index.isin(current_df.index)]
            # concat non existant data
            if not result_concat.empty:
                current_df = pd.concat([current_df, result_concat])
                # print(current_df)
            current_df.sort_index(inplace=True)
            # write it out updated
            self.db.table_write_df(table_name, current_df)
        else:
            # write out fresh new data
            self.db.table_write_df(table_name, result_df)
        
        # write table reference
        self.db.table_write('table_reference', {symbol: {'fundamental': table_name}}, 'symbol', method='append')
    
        # write status
        self.db.table_write('status_db', {symbol: status_info}, key_name='symbol', method='replace')
