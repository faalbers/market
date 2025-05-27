from .yahoof import YahooF
import logging, time, os
from ...database import Database
from ...utils import storage, yfinancetest
from pprint import pp
import yfinance as yf
from datetime import datetime, UTC
from dateutil.relativedelta import relativedelta
from dateutil import tz
from multiprocessing import Pool
import pandas as pd
import calendar, holidays

class YahooF_Chart(YahooF):
    dbName = 'yahoof_chart'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['chart']
        return [data_name]

    def get_chart(self, data=None):
        def proc_chart(ticker, data):
            while True:
                try:
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

    def __init__(self, key_values=[], data_names=[], update = False, forced=False):
        self.db = Database(self.dbName)
        if not update: return
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
        
        # Don't update during market hours
        if not forced:
            now = datetime.now().astimezone(tz.gettz('America/New_York'))
            today = now.date()
            is_market_day = not (today in holidays.US()) and (calendar.weekday(now.year, now.month, now.day) < 5)
            is_market_hours = now.hour >= 9 and now.hour < 17 # give it a bit of padding
            is_market_open = is_market_day and is_market_hours
            if is_market_open:
                self.logger.info('YahooF:  Chart: market still open, not updating')
                return

        # check what symbols need to be updated
        if forced:
            symbols = sorted(key_values)
        else:
            symbols = self.update_check(key_values)
        if len(symbols) == 0: return

        # leave if yfinance limit rate
        if not yfinancetest():
            self.logger.info('YahooF:  Chart: yfinance limit rate')
            return

        self.logger.info('YahooF:  Chart: update')
        self.logger.info('YahooF:  Chart: symbols processing : %s' % len(symbols))

        # backup first
        self.logger.info('YahooF:  Chart: %s' % self.db.backup())

        exec_list = [
            [symbol, [
                    self.get_chart,
                ], {'ticker': None, 'data': None}] for symbol in symbols]
        self.multi_execs(exec_list)

    def update_check(self, symbols):
        timestamp_pdt = int(datetime.now().timestamp())

        one_day_ts = timestamp_pdt - (3600 * 24 * 1)
        three_month_ts = timestamp_pdt - (3600 * 24 * 91)
        six_months_ts = timestamp_pdt - (3600 * 24 * 182)
        seven_months_ts = timestamp_pdt - (3600 * 24 * 212)

        status_db = self.db.table_read('status_db', keys=symbols)

        # found and last read more then a day ago
        one_day = (status_db['found'] > 0) & (status_db['timestamp'] < one_day_ts)
        
        # not found and last read more then 6 months ago and less then 7 months ago (last try)
        six_months = (status_db['found'] == 0) & ((status_db['timestamp'] > seven_months_ts) & (status_db['timestamp'] < six_months_ts))
        
        # if last timestamp is longer then 3 months ago, don't handle it anymore
        three_month = (status_db['found'] > 0) & (status_db['last_timestamp'] >= three_month_ts)

        # checked from status_db
        status_check = set(status_db[(one_day & three_month) ^ six_months].index.tolist())

        # not read
        not_read = set(symbols).difference(set(status_db.index))

        return sorted(not_read.union(status_check))

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

        # take out utc time of indices and change them to timestamps, rename index
        result.index = result.index.tz_localize(None)
        result.index = result.index.astype('int64') // 10**9
        result.index.name = 'timestamp'
        self.db.table_write_reference(symbol, 'chart', result, replace=True)
        
        # write status
        status['last_timestamp'] = int(result.index[-1])
        status['last_timestamp_str'] = str(pd.to_datetime(status['last_timestamp'], unit='s'))
        status = pd.DataFrame([status], index=[symbol])
        status.index.name = 'symbol'
        self.db.table_write('status_db', status)
        
    def cache_data(self, symbols):
        # update cache if needed
        db_storage = 'database/%s' % self.dbName
        db_storage_timestamp = storage.timestamp(db_storage)
        if db_storage_timestamp != None and self.db.timestamp <= db_storage_timestamp: return

        logger = logging.getLogger('Market')
        logger.info('YahooF:  Chart: update cache for %s symbols. can not be interrupted with stop text !' % len(symbols))

        # get cach if exists
        charts = {}
        if db_storage_timestamp != None:
            charts = storage.load(db_storage)
        
        # remove all the symbols froom charts that are not in the list
        if len(charts) > 0:
            for symbol in symbols:
                if symbol in charts: charts.pop(symbol)
                
        # retrieve symbol charts from database
        charts_db = self.db.timeseries_read('chart', keys=symbols)

        # combine them together
        charts.update(charts_db)

        # backup and write to storage
        logger.info('YahooF:  Chart: backup cache ...')
        storage.backup(db_storage)
        logger.info('YahooF:  Chart: saving updated cache ...')
        storage.save(charts, db_storage)
        logger.info('YahooF:  Chart: saving cache done')

    def get_charts(self, symbols = [], columns=[]):
        # get cached or database
        if len(symbols) == 0 or len(symbols) > 2500:
            # get cached
            db_storage = 'database/%s' % self.dbName
            db_storage_timestamp = storage.timestamp(db_storage)
            if db_storage_timestamp != None:
                # we have cached data load it
                symbols = set(symbols)
                pop_symbols = len(symbols) > 2500
                charts = storage.load(db_storage)
                if len(columns) > 0:
                    # we have to select columns
                    columns_set = set(columns)
                    # get all symbols from cache
                    charts_symbols = list(charts.keys())
                    for symbol in charts_symbols:
                        # go through each chart symbol
                        # remove the cached ones we don't need
                        if pop_symbols and symbol not in symbols: charts.pop(symbol)
                        # just keep columns that we need
                        found_columns = list(set(charts[symbol].columns).intersection(columns_set))
                        if len(found_columns) == 0:
                            # no needed columns found, pop the chart
                            charts.pop(symbol)
                        else:
                            # columns found keep only them and only needed columns
                            charts[symbol] = charts[symbol][found_columns]
                return charts

        # get from db
        return self.db.timeseries_read('chart', keys=symbols, columns=columns)

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'chart':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.get_charts(symbols=key_values, columns=column_names)
                columns_rename = {x[0]: x[1] for x in columns if x[1] != None}
                if len(columns_rename) > 0:
                    for symbol in data:
                        data[symbol] = data[symbol].rename(columns=columns_rename)
                return data
            else:
                data = self.get_charts(symbols=key_values)
                return data

    def get_vault_params(self, data_name):
        if data_name == 'chart':
            references = sorted(self.db.table_read_df('table_reference')['chart'])
            for reference in references:
                column_types = self.db.get_table_info(reference)['columnTypes']
                column_types.pop('timestamp')
                if len(column_types) > 8: return(column_types)
