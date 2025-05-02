from .yahoof import YahooF
import logging, time
from ...database import Database
from pprint import pp
import yfinance as yf
from datetime import datetime
from dateutil.relativedelta import relativedelta

class YahooF_Info(YahooF):
    dbName = 'yahoof_info'

    @staticmethod
    def get_table_names(table_name):
        if table_name == 'all':
            return ['info']
        return [table_name]
    
    def get_info(self, data=None):
        def proc_info(ticker, data):
            while True:
                try:
                    info = ticker.info
                    data = info
                    if data == None: return ([False, data, 'info is None'])
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  info: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                    else:
                        return [False, data, e]
                break
            return [True, data, 'ok']
        return [True, proc_info, data]
    
    def get_fund_overview(self, data):
        def proc_fund_overview(ticker, data):
            while True:
                try:
                    fund_overview = ticker.funds_data.fund_overview
                    data[1]['fund_data']['fund_overview'] = fund_overview
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  fund_overview: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        
        if not data[0]: return [False, proc_fund_overview, data]
        if not data[1]['quoteType'] in ['MUTUALFUND']: return [False, proc_fund_overview, data]
        if not'fund_data' in data[1]: data[1]['fund_data'] = {}
        return [True, proc_fund_overview, data]
    
    def get_sector_weightings(self, data):
        def proc_sector_weightings(ticker, data):
            while True:
                try:
                    sector_weightings = ticker.funds_data.sector_weightings
                    data[1]['fund_data']['sector_weightings'] = sector_weightings
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  sector_weightings: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        
        if not data[0]: return [False, proc_sector_weightings, data]
        if not data[1]['quoteType'] in ['MUTUALFUND', 'ETF']: return [False, proc_sector_weightings, data]
        if not'fund_data' in data[1]: data[1]['fund_data'] = {}
        return [True, proc_sector_weightings, data]
    
    def get_asset_classes(self, data):
        def proc_asset_classes(ticker, data):
            while True:
                try:
                    asset_classes = ticker.funds_data.asset_classes
                    data[1]['fund_data']['asset_classes'] = asset_classes
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  asset_classes: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        
        if not data[0]: return [False, proc_asset_classes, data]
        if not data[1]['quoteType'] in ['MUTUALFUND', 'ETF']: return [False, proc_asset_classes, data]
        if not'fund_data' in data[1]: data[1]['fund_data'] = {}
        return [True, proc_asset_classes, data]

    def get_top_holdings(self, data):
        def proc_top_holdings(ticker, data):
            while True:
                try:
                    top_holdings = ticker.funds_data.top_holdings.T.to_dict()
                    data[1]['fund_data']['top_holdings'] = top_holdings
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  top_holdings: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        
        if not data[0]: return [False, proc_top_holdings, data]
        if not data[1]['quoteType'] in ['MUTUALFUND', 'ETF']: return [False, proc_top_holdings, data]
        if not'fund_data' in data[1]: data[1]['fund_data'] = {}
        return [True, proc_top_holdings, data]

    def get_growth_estimates(self, data):
        def proc_growth_estimates(ticker, data):
            while True:
                try:
                    growth_estimates = ticker.growth_estimates
                    if growth_estimates.shape[0] > 0:
                        data[1]['growth_estimates'] = growth_estimates['stockTrend'].to_dict()
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  growth_estimates: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        
        if not data[0] == None: return [False, proc_growth_estimates, data]
        if data[1]['quoteType'] != 'EQUITY': return [False, proc_growth_estimates, data]
        return [True, proc_growth_estimates, data]

    def get_eps_trend(self, data):
        def proc_eps_trend(ticker, data):
            while True:
                try:
                    eps_trend = ticker.eps_trend
                    if eps_trend.shape[0] > 0:
                        data[1]['eps_trend'] = eps_trend.T.to_dict()
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  eps_trend: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        
        if not data[0]: return [False, proc_eps_trend, data]
        if data[1]['quoteType'] != 'EQUITY': return [False, proc_eps_trend, data]
        return [True, proc_eps_trend, data]

    def get_recommendations(self, data):
        def proc_recommendations(ticker, data):
            while True:
                try:
                    recommendations = ticker.recommendations
                    if recommendations.shape[0] > 0:
                        data[1]['recommendations'] = recommendations.T.to_dict()
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  recommendations: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        
        if not data[0]: return [False, proc_recommendations, data]
        return [True, proc_recommendations, data]

    def get_upgrades_downgrades(self, data):
        def proc_upgrades_downgrades(ticker, data):
            while True:
                try:
                    upgrades_downgrades = ticker.upgrades_downgrades
                    if upgrades_downgrades.shape[0] > 0:
                        start_date = upgrades_downgrades.index[0]
                        end_date = start_date - relativedelta(months=3)
                        upgrades_downgrades = upgrades_downgrades[start_date:end_date]
                        upgrades_downgrades.index = upgrades_downgrades.index.astype('int64') // 10**9
                        data[1]['upgrades_downgrades'] = upgrades_downgrades.T.to_dict()
                except Exception as e:
                    if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                        self.logger.info('YahooF:  upgrades_downgrades: Rate Limeit: wait 60 seconds')
                        time.sleep(60)
                        continue
                break
            return data
        
        if not data[0]: return [False, proc_upgrades_downgrades, data]
        return [True, proc_upgrades_downgrades, data]

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

        self.logger.info('YahooF:  Info: update')
        self.logger.info('YahooF:  Info: symbols processing : %s' % len(symbols))

        # backup first
        self.db.backup()

        exec_list = [
            [symbol, [
                    self.get_info,
                    self.get_fund_overview,
                    self.get_sector_weightings,
                    self.get_asset_classes,
                    self.get_top_holdings,
                    # self.get_growth_estimates,
                    # self.get_eps_trend,
                    # self.get_recommendations,
                    # self.get_upgrades_downgrades,
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
        if not found:
            return
        result = result[1]
        
        result['timestamp'] = timestamp
        self.db.table_write('info', {symbol: result}, key_name='symbol', method='replace')
