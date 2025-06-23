from .yahoof import YahooF
import logging, time
from ...database import Database
from ...utils import yfinancetest
from pprint import pp
import yfinance as yf
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

class YahooF_Info(YahooF):
    dbName = 'yahoof_info'

    @staticmethod
    def get_data_names(data_name):
        if data_name == 'all':
            return ['info']
        return [data_name]

    def get_info(self, data):
        def proc_info(ticker, data):
            while True:
                try:
                    info = ticker.info
                    if not isinstance(info, type(None)) and 'quoteType' in info:
                        data[1]['info'] = info
                    else:
                        data[2]['info'] = 'info is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['info'] = str(e)
                break
            return data
        return [True, proc_info, data]

    def get_earnings_estimate(self, data):
        def proc_earnings_estimate(ticker, data):
            while True:
                try:
                    earnings_estimate = ticker.earnings_estimate
                    if not isinstance(earnings_estimate, type(None)) and len(earnings_estimate) > 0:
                        data[1]['earnings_estimate'] = earnings_estimate
                    else:
                        data[2]['earnings_estimate'] = 'earnings_estimate is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['earnings_estimate'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_earnings_estimate, data]
        if not data[1]['info']['quoteType'] in ['EQUITY']: return [False, proc_earnings_estimate, data]
        return [True, proc_earnings_estimate, data]

    def get_earnings_dates(self, data):
        def proc_earnings_dates(ticker, data):
            while True:
                try:
                    earnings_dates = ticker.earnings_dates
                    if not isinstance(earnings_dates, type(None)) and len(earnings_dates) > 0:
                        data[1]['earnings_dates'] = earnings_dates
                    else:
                        data[2]['earnings_dates'] = 'earnings_dates is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['earnings_dates'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_earnings_dates, data]
        if not data[1]['info']['quoteType'] in ['EQUITY']: return [False, proc_earnings_dates, data]
        return [True, proc_earnings_dates, data]
    
    def get_revenue_estimate(self, data):
        def proc_revenue_estimate(ticker, data):
            while True:
                try:
                    revenue_estimate = ticker.revenue_estimate
                    if not isinstance(revenue_estimate, type(None)) and len(revenue_estimate) > 0:
                        data[1]['revenue_estimate'] = revenue_estimate
                    else:
                        data[2]['revenue_estimate'] = 'revenue_estimate is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['revenue_estimate'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_revenue_estimate, data]
        if not data[1]['info']['quoteType'] in ['EQUITY']: return [False, proc_revenue_estimate, data]
        return [True, proc_revenue_estimate, data]

    def get_growth_estimates(self, data):
        def proc_growth_estimates(ticker, data):
            while True:
                try:
                    growth_estimates = ticker.growth_estimates
                    if not isinstance(growth_estimates, type(None)) and len(growth_estimates) > 0:
                        data[1]['growth_estimates'] = growth_estimates
                    else:
                        data[2]['growth_estimates'] = 'growth_estimates is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['growth_estimates'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_growth_estimates, data]
        if not data[1]['info']['quoteType'] in ['EQUITY']: return [False, proc_growth_estimates, data]
        return [True, proc_growth_estimates, data]

    def get_upgrades_downgrades(self, data):
        def proc_upgrades_downgrades(ticker, data):
            while True:
                try:
                    upgrades_downgrades = ticker.upgrades_downgrades
                    if not isinstance(upgrades_downgrades, type(None)) and len(upgrades_downgrades) > 0:
                        data[1]['upgrades_downgrades'] = upgrades_downgrades
                    else:
                        data[2]['upgrades_downgrades'] = 'upgrades_downgrades is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['upgrades_downgrades'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_upgrades_downgrades, data]
        if not data[1]['info']['quoteType'] in ['EQUITY']: return [False, proc_upgrades_downgrades, data]
        return [True, proc_upgrades_downgrades, data]

    def get_fund_overview(self, data):
        def proc_fund_overview(ticker, data):
            while True:
                try:
                    fund_overview = ticker.funds_data.fund_overview
                    if not isinstance(fund_overview, type(None)) and len(fund_overview) > 0:
                        data[1]['fund_overview'] = fund_overview
                    else:
                        data[2]['fund_overview'] = 'fund_overview is None'
                    data[1]['fund_overview'] = fund_overview
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['fund_overview'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_fund_overview, data]
        if not data[1]['info']['quoteType'] in ['MUTUALFUND', 'ETF']: return [False, proc_fund_overview, data]
        return [True, proc_fund_overview, data]

    def get_sector_weightings(self, data):
        def proc_sector_weightings(ticker, data):
            while True:
                try:
                    sector_weightings = ticker.funds_data.sector_weightings
                    if not isinstance(sector_weightings, type(None)) and len(sector_weightings) > 0:
                        data[1]['sector_weightings'] = sector_weightings
                    else:
                        data[2]['sector_weightings'] = 'sector_weightings is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['sector_weightings'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_sector_weightings, data]
        if not data[1]['info']['quoteType'] in ['MUTUALFUND', 'ETF']: return [False, proc_sector_weightings, data]
        return [True, proc_sector_weightings, data]

    def get_asset_classes(self, data):
        def proc_asset_classes(ticker, data):
            while True:
                try:
                    asset_classes = ticker.funds_data.asset_classes
                    if not isinstance(asset_classes, type(None)) and len(asset_classes) > 0:
                        data[1]['asset_classes'] = asset_classes
                    else:
                        data[2]['asset_classes'] = 'asset_classes is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['asset_classes'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_asset_classes, data]
        if not data[1]['info']['quoteType'] in ['MUTUALFUND', 'ETF']: return [False, proc_asset_classes, data]
        return [True, proc_asset_classes, data]

    def get_top_holdings(self, data):
        def proc_top_holdings(ticker, data):
            while True:
                try:
                    top_holdings = ticker.funds_data.top_holdings
                    if not isinstance(top_holdings, type(None)) and len(top_holdings) > 0:
                        data[1]['top_holdings'] = top_holdings
                    else:
                        data[2]['top_holdings'] = 'top_holdings is None'
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        data[2]['top_holdings'] = str(e)
                break
            return data
        if not 'info' in data[1]: return [False, proc_top_holdings, data]
        if not data[1]['info']['quoteType'] in ['MUTUALFUND', 'ETF']: return [False, proc_top_holdings, data]
        return [True, proc_top_holdings, data]

    def __init__(self, key_values=[], data_names=[], update = False, forced=False):
        self.db = Database(self.dbName)
        if not update: return
        self.logger = logging.getLogger('vault_multi')
        super().__init__()

        # TODO move this to the Yahoof base
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
        for update, symbols in updates.items():
            print(update, len(symbols))
        if len(updates['all']) == 0: return

        # leave if yfinance limit rate
        if not yfinancetest():
            self.logger.info('YahooF:  Info: yfinance limit rate')
            return

        self.logger.info('YahooF:  Info: update')
        self.logger.info('YahooF:  Info: symbols processing : %s' % len(updates['all']))

        # backup first
        self.logger.info('YahooF:  Info: %s' % self.db.backup())

        exec_list = []
        for symbol in updates['all']:
            exec_entity = [symbol, [], {'ticker': None, 'data': [False, {}, {}]}]
            if symbol in updates['regular']:
                exec_entity[1].append(self.get_info)
                exec_entity[1].append(self.get_upgrades_downgrades)
            if symbol in updates['quarterly']:
                exec_entity[1].append(self.get_earnings_estimate)
                exec_entity[1].append(self.get_earnings_dates)
                exec_entity[1].append(self.get_revenue_estimate)
                exec_entity[1].append(self.get_growth_estimates)
                exec_entity[1].append(self.get_fund_overview)
                exec_entity[1].append(self.get_sector_weightings)
                exec_entity[1].append(self.get_asset_classes)
                exec_entity[1].append(self.get_top_holdings)
            exec_list.append(exec_entity)
        self.multi_execs(exec_list)


    def update_check(self, symbols, forced=False):
        status_db = self.db.table_read('status_db', keys=symbols)

        updates = {}

        if forced or status_db.empty:
            symbols = sorted(symbols)
            updates['regular'] = symbols
            updates['quarterly'] = symbols
            updates['all'] = symbols
            return updates
        
        now_ts = int(datetime.now().timestamp())
        five_days_ts = now_ts - (3600 * 24 * 5)
        half_year_ts = now_ts - (3600 * 24 * 182)
        last_quarter_ts = int((pd.Timestamp('now').normalize() - pd.offsets.QuarterEnd(1)).timestamp())

        missing_symbols = set(symbols).difference(set(status_db.index))

        found = status_db['found'] > 0

        # found and last read more then one month ago
        five_days = found & (status_db['timestamp'] < five_days_ts)
        
        # not found and last read more then a half year ago
        half_year = ~found & (status_db['timestamp'] < half_year_ts)

        # find regular symbols
        regular = set(status_db[five_days ^ half_year].index.tolist())
        updates['regular'] = sorted(missing_symbols.union(regular))

        # found and new quarter
        quarterly = found & (status_db['timestamp_last_quarter'] < last_quarter_ts)
        quarterly = set(status_db[quarterly].index.tolist())
        updates['quarterly'] = sorted(missing_symbols.union(quarterly))
        
        updates['all'] = sorted(set(updates['regular']).union(set(updates['quarterly'])))

        return updates

    def push_api_data(self, symbol, result):
        errors = result[2]
        result_data = result[1]

        found = False
        timestamp = int(datetime.now().timestamp())

        info = {'timestamp': timestamp, 'timestampStr': str(datetime.fromtimestamp(timestamp))}
        if 'info' in result_data:
            if 'companyOfficers' in result_data['info']: result_data['info'].pop('companyOfficers')
            if 'executiveTeam' in result_data['info']: result_data['info'].pop('executiveTeam')
            result_data['info'].pop('symbol')
            info.update(result_data['info'])

        if 'earnings_estimate' in result_data:
            info['earningsEstimate'] = result_data['earnings_estimate'].T.to_dict()
        
        if 'growth_estimates' in result_data:
            info['growthEstimates'] = result_data['growth_estimates'].T.to_dict()
        
        if 'revenue_estimate' in result_data:
            info['revenueEstimate'] = result_data['revenue_estimate'].T.to_dict()
        
        if 'fund_overview' in result_data:
            info['fundOverview'] = result_data['fund_overview']
        
        if 'sector_weightings' in result_data:
            info['sectorWeightings'] = result_data['sector_weightings']
        
        if 'asset_classes' in result_data:
            info['assetClasses'] = result_data['asset_classes']
        
        if 'top_holdings' in result_data:
            info['topHoldings'] = result_data['top_holdings'].T.to_dict()
        
        if len(info) > 2: # timestamp and timestampStr
            found = True
            info = pd.DataFrame([info], index=[symbol])
            info.index.name = 'symbol'
            self.db.table_write('info', info)
        
        if 'earnings_dates' in result_data:
            found = True
            result_data['earnings_dates'].dropna(how='all', inplace=True)
            result_data['earnings_dates'].index = result_data['earnings_dates'].index.tz_localize(None)
            result_data['earnings_dates'].index = result_data['earnings_dates'].index.astype('int64') // 10**9
            result_data['earnings_dates'].index.name = 'timestamp'
            result_data['earnings_dates'].sort_index(inplace=True)
            # remove duplicates
            result_data['earnings_dates'] = result_data['earnings_dates'].groupby(level=0).last()
            self.db.table_write_reference(symbol, 'earnings_dates', result_data['earnings_dates'], update=False)
        
        if 'upgrades_downgrades' in result_data:
            found = True
            result_data['upgrades_downgrades'].index = result_data['upgrades_downgrades'].index.tz_localize(None)
            result_data['upgrades_downgrades'].index = result_data['upgrades_downgrades'].index.astype('int64') // 10**9
            result_data['upgrades_downgrades'].index.name = 'timestamp'
            result_data['upgrades_downgrades'].sort_index(inplace=True)
            self.db.table_write_reference(symbol, 'upgrades_downgrades', result_data['upgrades_downgrades'], update=False)
        
        # make status_db
        timestamp_last_quarter = int((pd.Timestamp('now').normalize() - pd.offsets.QuarterEnd(1)).timestamp())
        message = 'ok'
        if not found:
            for data_type, error in errors.items():
                message = '%s: %s' % (data_type, error)
                break
        status = {
            'timestamp': timestamp,
            'timestamp_str': str(datetime.fromtimestamp(timestamp)),
            'timestamp_last_quarter': timestamp_last_quarter,
            'timestamp_last_quarter_str': str(pd.to_datetime(timestamp_last_quarter, unit='s')),
            'found': found,
            'message': message
        }
        status = pd.DataFrame([status], index=[symbol])
        status.index.name = 'symbol'
        self.db.table_write('status_db', status)

        # check if failed on log
        result[0] = found

        if 'info' in result_data:
            print(symbol, result_data['info']['quoteType'], found, list(result_data.keys()))
        else:
            print(symbol, None, found, list(result_data.keys()))

    def get_vault_data(self, data_name, columns, key_values):
        if data_name == 'info':
            if len(columns) > 0:
                column_names = [x[0] for x in columns]
                data = self.db.table_read('info', keys=key_values, columns=column_names)
                data = data.rename(columns={x[0]: x[1] for x in columns})
                return data
            else:
                data = self.db.table_read('info', keys=key_values)
                return data
