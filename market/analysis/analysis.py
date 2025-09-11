from ..tickers import Tickers
from ..vault import Vault
from ..viz import Viz
from .analysis_params import Analysis_Params
import pandas as pd
import numpy as np
from pprint import pp
from ..utils import storage
from ..database import Database
from datetime import datetime
from dateutil.relativedelta import relativedelta
import talib as ta

class Analysis():

    def __init__(self, symbols=[]):
        self.tickers = Tickers(symbols)
        self.db = Database('analysis')
        self.vault = Vault()
        self.__get_data()
        self.params = Analysis_Params()
        # self.viz = Viz()
        # self.benchmarks = Tickers(['SPY', 'QQQ'])

    def get_data(self, active_only=True):
        if active_only:
            data = self.data[self.data['active'] == True].copy()
        else:
            data = self.data.copy()
        data.drop('active', axis=1, inplace=True)
        return data

    def __cache_update(self, symbols):
        pd.options.display.float_format = '{:.2f}'.format
        if len(symbols) == 0: return
        print('update cache %s symbols' % (len(symbols)))

        # start data
        tickers = Tickers(symbols)
        data = tickers.get_symbols_dataframe()

        # get analysis
        print('Get Analysis:')
        vault_analysis = tickers.get_vault_analysis()
        print('Get Analysis: done')
        vault_analysis['type'] = data['type']

        # add treasury rate 10y
        if not '^TNX' in vault_analysis['chart']:
            vault_analysis['treasury_rate_10y'] = Tickers(['^TNX']).get_vault_charts()['chart']['^TNX']['price'].iloc[-1]
        else:
            vault_analysis['treasury_rate_10y'] = vault_analysis['chart']['^TNX']['price'].iloc[-1]

        # merge info
        print('Info:')
        info = vault_analysis['info']

        # add timestamp
        timestamp = int(datetime.now().timestamp())
        info['timestamp'] = timestamp

        # name market cap
        market_cap = info['market_cap'] / 1000000
        info.loc[market_cap >= 250, 'market_cap_name'] = 'Small'
        info.loc[market_cap >= 2000, 'market_cap_name'] = 'Mid'
        info.loc[market_cap >= 10000, 'market_cap_name'] = 'Large'
        info.loc[market_cap >= 200000, 'market_cap_name'] = 'Mega'

        # handle funds info
        if True:
            is_fund_overview = info['fund_overview'].notna()
            info.loc[is_fund_overview, 'fund_category'] = info.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('categoryName'))
            info.loc[is_fund_overview, 'fund_family'] = info.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('family'))
            info = info.drop('fund_overview', axis=1)

        data = data.merge(info, how='left', left_index=True, right_index=True)

        # fix 'infinity' from info
        for column in data.columns[data.apply(lambda x: 'Infinity' in x.values)]:
            data.loc[data[column] == 'Infinity', column] = np.nan

        # get data derrived from charts
        print('charts:')
        active = self.get_active(vault_analysis)
        data = data.merge(active, how='left', left_index=True, right_index=True)
        minervini = self.get_minervini(vault_analysis)
        data = data.merge(minervini, how='left', left_index=True, right_index=True)
        dividends = self.get_dividend_yields(vault_analysis)
        for period in ['yearly', 'ttm']:
            name = 'dividends_'+period
            trends = self.get_trends_percent(dividends[period], name=name)
            data = data.merge(trends, how='left', left_index=True, right_index=True)
        print('charts: done')

        # get fundamentals
        fundamentals = {}
        print('fundamentals: yearly')
        fundamentals['yearly'] = self.get_fundamentals(vault_analysis, 'yearly')
        print('fundamentals: quarterly')
        fundamentals['quarterly'] = self.get_fundamentals(vault_analysis, 'quarterly')
        print('fundamentals: ttm')
        fundamentals['ttm'] = self.get_fundamentals_ttm(vault_analysis).T
        
        # merge trends
        params_skip = ['free cash flow', 'price to free cash flow']
        for period in ['yearly', 'quarterly']:
            for param, trend_data in fundamentals[period].items():
                if param in params_skip: continue
                name = param.replace(' ', '_')+'_'+period
                trends = self.get_trends_percent(trend_data, name=name)
                data = data.merge(trends, how='left', left_index=True, right_index=True)
        
        # rename ttm parameters
        rename = {c:(c.replace(' ', '_')+'_ttm') for c in fundamentals['ttm'].columns}
        fundamentals['ttm'] = fundamentals['ttm'].rename(columns=rename)
        data = data.merge(fundamentals['ttm'], how='left', left_index=True, right_index=True)
        print('fundamentals: done')

        # merge margin of safety
        margins_of_safety = self.get_margins_of_safety(fundamentals, vault_analysis)
        data = data.merge(margins_of_safety, how='left', left_index=True, right_index=True)

        # infer al object columns
        data = data.infer_objects()

        # keep market_cap_name as market_cap
        data.drop('market_cap', axis=1, inplace=True)
        data.rename(columns={'market_cap_name': 'market_cap'}, inplace=True)

        # write to db
        self.db.backup()
        self.db.table_write('analysis', data)

    def get_trends_percent(self, data, name):
        trends = []
        for column in data.columns:
            series = data[column].dropna()
            if series.shape[0] == 0: continue
            
            trend_values = pd.Series(name=column)
            trend_values[name] = series.iloc[-1]
            last_date = series.index[-1]
            if isinstance(last_date, pd.Timestamp):
                trend_values['%s_end_year' % name] = last_date.year
                trend_values['%s_end_month' % name] = last_date.month
            elif last_date > 1900:
                trend_values['%s_end_year' % name] = last_date
            
            if series.shape[0] >= 2:
                count_range = range(series.shape[0])
                slope, intercept = np.polyfit(count_range, series.values, 1)
                std = (series - (count_range*slope + intercept)).std()
                trend_values['%s_count' % name] = series.shape[0]
                trend_values['%s_trend' % name] = slope
                if trend_values[name] != 0.0:
                    trend_values['%s_std_%%' % name] = (( std / abs(trend_values[name]) ) * 100)
                else:
                    trend_values['%s_std_%%' % name] = std
            
            trends.append(trend_values)

        trends = pd.DataFrame(trends)
        
        return trends
        
    def get_active(self, vault_analysis):
        active = pd.Series(name='active')
        now = pd.Timestamp.now()
        for symbol, chart in vault_analysis['chart'].items():
            active[symbol] = False
            symbol_type = vault_analysis['type'].loc[symbol]
            if symbol_type in ['EQUITY', 'ETF']:
                chart_volume = chart[chart['volume'] > 0]
                if chart_volume.empty: continue
                inactive_days = (now - (chart_volume.index[-1])).days
                if inactive_days > 30: continue
            active[symbol] = True

        return active

    def get_dividend_yields(self, vault_analysis, symbols=[]):
        dividend_yields = {
            'all': [],
        }
        if len(symbols) == 0:
            symbols = sorted(vault_analysis['chart'])
        else:
            symbols = sorted(set(symbols).intersection(set(vault_analysis['chart'])))
        for symbol in symbols:
            # prepare dataframe
            chart = vault_analysis['chart'][symbol].copy()
            if 'dividends' in chart.columns:
                is_dividend = chart['dividends'] > 0.0
                if is_dividend.any():
                    dividends = chart[is_dividend]['dividends']
                    if 'stock_splits' in chart.columns:
                        is_stock_split = chart['stock_splits'] > 0.0
                        if is_stock_split.any():
                            chart['dividend_div'] = 1.0
                            chart.loc[is_stock_split, 'dividend_div'] = chart.loc[is_stock_split, 'stock_splits']
                            chart['dividend_div'] = chart['dividend_div'].iloc[::-1].cumprod().iloc[::-1]
                            chart['dividends'] = chart['dividends'] / chart['dividend_div']
                            dividends = chart[is_dividend]['dividends']
                    dividends.name = symbol
                    dividend_yields['all'].append((dividends / float(chart['price'].iloc[-1])) * 100)

        # prepare all dividends
        dividend_yields['all'] = pd.DataFrame(dividend_yields['all']).T
        dividend_yields['all'].sort_index(inplace=True)

        if not dividend_yields['all'].empty:
            now = pd.Timestamp.now()
            last_year = now.year - 1

            # create yearly
            dividend_yields['yearly'] = dividend_yields['all'].groupby(dividend_yields['all'].index.year).sum().loc[:last_year]
            dividend_yields['yearly'] = dividend_yields['yearly'].iloc[1:]
            dividend_yields['yearly'].replace(0, np.nan, inplace=True)
            
            # create ttm
            dividend_yields['ttm'] = dividend_yields['all'].groupby(dividend_yields['all'].index.map(lambda x: relativedelta(now, x).years)).sum()
            dividend_yields['ttm'].sort_index(ascending=False, inplace=True)
            dividend_yields['ttm'] = dividend_yields['ttm'].iloc[1:]
            dividend_yields['ttm'].replace(0, np.nan, inplace=True)
        else:
            dividend_yields['yearly'] = pd.DataFrame()
            dividend_yields['ttm'] = pd.DataFrame()
        
        return dividend_yields

    def get_minervini(self, vault_analysis, symbols=[]):
        chart_data = pd.DataFrame()
        for symbol, chart in vault_analysis['chart'].items():
            # there are some price values that are strings because of Infinity
            chart['price'] = chart['price'].astype(float, errors='ignore')

            # get mark minervini classifications
            # https://www.chartmill.com/documentation/stock-screener/technical-analysis-trading-strategies/496-Mark-Minervini-Trend-Template-A-Step-by-Step-Guide-for-Beginners
            current_price = chart['price'].dropna().iloc[-1]
            chart_data.loc[symbol, 'price'] = current_price

            conditions = []
            
            sma_50 = ta.SMA(chart['price'], timeperiod=50)
            
            for period in [150, 200]:
                if chart.shape[0] >= period:
                    sma = ta.SMA(chart['price'], timeperiod=period)
                    conditions.append(current_price > sma.iloc[-1]) # Current Price Above the period Moving Average
                    conditions.append(sma_50.iloc[-1] > sma.iloc[-1]) # 50-Day Moving Average Above the period Moving Average
                    if chart.shape[0] >= (period + 20):
                        slope = np.polyfit(range(20), sma.iloc[-20:].values, 1)[0]
                        conditions.append(slope > 0.0,) # period Moving Average Increasing during last month
                    else:
                        conditions.append(False)
                else:
                    conditions += [False, False, False]

            if chart.shape[0] >= 52*5:
                low_52_week = chart.iloc[-(52*5)]['low'].min()
                conditions.append(current_price > (low_52_week * 1.3)) # Current Price Above 52-Week Low plus 30%
                high_52_week = chart.iloc[-(52*5)]['high'].max()
                conditions.append(current_price > (high_52_week * 0.75)) # Current Price Above 52-Week High minus 25%
            else:
                conditions += [False, False]

            if chart.shape[0] >= 14:
                rsi = ta.RSI(chart['price'], timeperiod=14).iloc[-1]
                conditions.append(rsi > 70) # RSI Above 70
            else:
                conditions.append(False)

            minervini_score_percent = (np.array([float(x) for x in conditions]) / len(conditions)).sum() * 100.0
            chart_data.loc[symbol, 'minervini_score'] = minervini_score_percent

        return chart_data


    def get_fundamentals_ttm(self, vault_analysis, symbols=[]):
        if len(symbols) == 0:
            trailing = vault_analysis['trailing'].copy()
        else:
            trailing = vault_analysis['trailing'][vault_analysis['trailing'].index.isin(symbols)].copy()
        
        data = pd.DataFrame()
        if 'current_liabilities' in trailing.columns:
            if 'current_assets' in trailing.columns:
                data['current ratio'] = (trailing['current_assets'] / trailing['current_liabilities']) * 100
            if 'cash_and_cash_equivalents' in trailing.columns:
                data['cash ratio'] = (trailing['cash_and_cash_equivalents'] / trailing['current_liabilities']) * 100.0
        if 'total_revenue' in trailing.columns:
            if 'gross_profit' in trailing.columns:
                data['gross profit margin'] = (trailing['gross_profit'] / trailing['total_revenue']) * 100
            if 'operating_income' in trailing.columns:
                data['operating profit margin'] = (trailing['operating_income'] / trailing['total_revenue']) * 100
            if 'pretax_income' in trailing.columns:
                data['profit margin'] = (trailing['pretax_income'] / trailing['total_revenue']) * 100
            if 'net_income' in trailing.columns:
                data['net profit margin'] = (trailing['net_income'] / trailing['total_revenue']) * 100
        if 'free_cash_flow' in trailing.columns:
            data['free cash flow'] = trailing['free_cash_flow']

        # post fix data
        data = data.T
        data = data.infer_objects()
        # values with inf had nan values as deviders
        data = data.replace([np.inf, -np.inf], np.nan)
        # drop symbols and dates where all values are nan
        data.dropna(axis=1, how='all', inplace=True)
        
        return data

    def get_fundamentals(self, vault_analysis, period, symbols=[]):
        # prepare dataframes
        data = {
            'current ratio': [],
            'cash ratio': [],
            'gross profit margin': [],
            'operating profit margin': [],
            'profit margin': [],
            'net profit margin': [],
            'pe': [],
            'free cash flow': [],
            'price to free cash flow': [],
        }

        # go through each symbol's dataframe
        if len(symbols) == 0:
            symbols = sorted(vault_analysis[period])
        else:
            symbols = sorted(set(symbols).intersection(set(vault_analysis[period])))
        for symbol in symbols:
            # prepare dataframe
            symbol_period = vault_analysis[period][symbol].copy()
            symbol_period.dropna(axis=0, how='all', inplace=True)

            # add price to dates
            if symbol in vault_analysis['chart']:
                for date in symbol_period.index:
                    prices = vault_analysis['chart'][symbol].loc[:date]
                    if not prices.empty:
                        symbol_period.loc[date, 'price'] = prices['price'].iloc[-1]

            # change yearly dates to year
            if period == 'yearly':
                symbol_period.index = symbol_period.index.year
            symbol_period = symbol_period.groupby(symbol_period.index).last() # some have more then one results in a period, strangely

            # calculate ratios as Series
            def add_values(param, symbol, values):
                values.name = symbol
                data[param].append(values)
            if 'current_liabilities' in symbol_period.columns:
                if 'current_assets' in symbol_period.columns:
                    add_values('current ratio', symbol, (symbol_period['current_assets'] / symbol_period['current_liabilities']) * 100)
                if 'cash_and_cash_equivalents' in symbol_period.columns:
                    add_values('cash ratio', symbol, (symbol_period['cash_and_cash_equivalents'] / symbol_period['current_liabilities']) * 100.0)
            if 'total_revenue' in symbol_period.columns:
                if 'gross_profit' in symbol_period.columns:
                    add_values('gross profit margin', symbol, (symbol_period['gross_profit'] / symbol_period['total_revenue']) * 100)
                if 'operating_income' in symbol_period.columns:
                    add_values('operating profit margin', symbol, (symbol_period['operating_income'] / symbol_period['total_revenue']) * 100)
                if 'pretax_income' in symbol_period.columns:
                    add_values('profit margin', symbol, (symbol_period['pretax_income'] / symbol_period['total_revenue']) * 100)
                if 'net_income' in symbol_period.columns:
                    add_values('net profit margin', symbol, (symbol_period['net_income'] / symbol_period['total_revenue']) * 100)
            if 'free_cash_flow' in symbol_period.columns:
                add_values('free cash flow', symbol, symbol_period['free_cash_flow'])
            if 'price' in symbol_period.columns:
                if 'eps' in symbol_period.columns:
                    eps = symbol_period['eps']
                    if period == 'quarterly': eps = eps * 4
                    add_values('pe', symbol, symbol_period['price']/eps)
                if 'shares' in symbol_period.columns:
                    market_cap = symbol_period['price'] * symbol_period['shares']
                    if 'free_cash_flow' in symbol_period.columns:
                        fcf = symbol_period['free_cash_flow']
                        if period == 'quarterly': fcf = fcf * 4
                        add_values('price to free cash flow', symbol, market_cap / fcf)
        
        # create dataframe pre parameter
        for parameter, series in data.items():
            data[parameter] = pd.DataFrame(series).T
            # values with inf had nan values as deviders
            data[parameter] = data[parameter].replace([np.inf, -np.inf], np.nan)
            # drop symbols and dates where all values are nan
            data[parameter].dropna(axis=1, how='all', inplace=True)
            # sort index
            data[parameter].sort_index(inplace=True)

        return data
    
    def get_margins_of_safety(self, fundamentals, vault_analysis):
        data = pd.DataFrame(columns=['margin_of_safety', 'margin_of_safety_volatility'])
        if not 'yearly' in fundamentals: return data
        if not 'free cash flow' in fundamentals['yearly']: return data
        if not 'price to free cash flow' in fundamentals['yearly']: return data
        if not 'trailing' in vault_analysis: return data
        if not 'treasury_rate_10y' in vault_analysis: return data

        for symbol in fundamentals['yearly']['free cash flow'].columns:
            if not symbol in fundamentals['yearly']['price to free cash flow'].columns: continue
        
            # get free cash flow trend
            fcf_yearly = fundamentals['yearly']['free cash flow'][symbol].dropna().reset_index(drop=True)
            if fcf_yearly.shape[0] < 2: continue
            coeffs = np.polyfit(fcf_yearly.index, fcf_yearly.values, 1)
            trend = np.polyval(coeffs, fcf_yearly.index)
            residuals = fcf_yearly.values - trend
            residual_std = np.std(residuals)
            volatility = (residual_std / np.abs(trend.mean())) * 100.0 # in percent
            data.loc[symbol, 'margin_of_safety_volatility'] = volatility
            trend_mean = np.mean(trend)
            if trend_mean <= 0: continue # can not deduct growth
            growth = coeffs[0] / trend_mean # in decimal

            # get price to free cash flow multiples average
            pfcf_yearly = fundamentals['yearly']['price to free cash flow'][symbol].dropna()
            pfcf_yearly_mean = pfcf_yearly.mean() # in multiples
            pfcf_yearly_median = pfcf_yearly.median() # in multiples
            similarity = abs(pfcf_yearly_mean-pfcf_yearly_median) / abs((pfcf_yearly_mean+pfcf_yearly_median)/2)
            if similarity > 0.2:
                pfcf_yearly_average = pfcf_yearly_median
            else:
                pfcf_yearly_average = pfcf_yearly_mean

            # calculate intrinsic value after 10 years
            years = 10
            discount = (vault_analysis['treasury_rate_10y'] + 3.0) / 100.0 # at least 10y treasury rate + 3%, change to decimal
            if not symbol in vault_analysis['trailing'].index: continue
            if not 'free_cash_flow' in vault_analysis['trailing'].columns: continue

            fcf = vault_analysis['trailing'].loc[symbol, 'free_cash_flow']
            if fcf <= 0: continue
            values = fcf * (1 + growth) ** np.arange(years+1)
            fcf_growth = pd.Series(values).to_frame('fcf')
            fcf_growth['fcf_dcf'] = fcf_growth['fcf'] / ((1.0 + discount) ** np.arange(years+1))
            terminal_value = fcf_growth['fcf_dcf'].iloc[-1] * pfcf_yearly_average # using exit_multiple
            intrinsic_value = fcf_growth['fcf_dcf'].iloc[:-1].sum() + terminal_value

            # calculate margin of safety
            market_cap = vault_analysis['info'].loc[symbol, 'market_cap']
            margin_of_safety = (1-(market_cap/intrinsic_value))*100 # in percent
            data.loc[symbol, 'margin_of_safety'] = margin_of_safety

        return data

    def __get_data(self):
        symbols = self.tickers.get_symbols()
        # get newest analysis db timestamps
        analysis_timestamps = self.vault.get_db_timestamps('analysis')
        analysis_timestamp = 0
        for db_name, db_timestamps in analysis_timestamps.items():
            if db_timestamps > analysis_timestamp: analysis_timestamp = db_timestamps
        cache_timestamps =  self.db.table_read('analysis', keys=symbols, columns=['timestamp'])
        if cache_timestamps.empty:
            self.__cache_update(symbols)
        else:
            cache_symbols = set(symbols).difference(set(cache_timestamps.index))
            cache_symbols.update(cache_timestamps[cache_timestamps['timestamp'] < analysis_timestamp].index)
            cache_symbols = sorted(cache_symbols)
            self.__cache_update(cache_symbols)
        
        # self.data = self.db.table_read('analysis', keys=symbols)
        self.data = self.db.table_read('analysis')
        self.data.drop('timestamp', axis=1, inplace=True)

        # add industry peers data
        industries = self.data['industry'].dropna().unique()
        peers_parameters = [
            'pe_ttm', 'pe_forward',
        ]
        peers_parameters = [p for p in peers_parameters if p in self.data.columns]
        peers_parameters_new = [(p+'_peers') for p in peers_parameters]
        for industry in industries:
            # go through each industry
            is_industry = self.data['industry'] == industry

            # find mean or median from each industry
            industry_peers = self.data[is_industry][peers_parameters]
            industry_average = industry_peers.mean().to_frame('mean')
            industry_average['median'] = industry_peers.median()
            industry_average['similarity'] = abs(industry_average['mean']-industry_average['median']) / \
                ((industry_average['mean']+industry_average['median']).abs()/2)
            industry_average.loc[industry_average['similarity'] > 0.2, 'average'] = industry_average['median']
            industry_average.loc[industry_average['similarity'] <= 0.2, 'average'] = industry_average['mean']
            industry_average = industry_average['average']

            # set difference between values and peers values if symbols in that industry
            self.data.loc[is_industry, peers_parameters_new] = self.data.loc[is_industry, peers_parameters].values - industry_average.values
    
        # only get needed symbols
        self.data = self.data[self.data.index.isin(symbols)]
        
    # useful ?
    # is_growth_estimates = info['growth_estimates'].notna()
    # values = info.loc[is_growth_estimates, 'growth_estimates'].apply(lambda x: x.get('0q')).apply(lambda x: x.get('stockTrend'))*100
    # info.loc[is_growth_estimates, 'growth_trend_q_cur_%'] = values
    # values = info.loc[is_growth_estimates, 'growth_estimates'].apply(lambda x: x.get('+1q')).apply(lambda x: x.get('stockTrend'))*100
    # info.loc[is_growth_estimates, 'growth_trend_q_next_%'] = values
    # values = info.loc[is_growth_estimates, 'growth_estimates'].apply(lambda x: x.get('0y')).apply(lambda x: x.get('stockTrend'))*100
    # info.loc[is_growth_estimates, 'growth_trend_y_cur_%'] = values
    # values = info.loc[is_growth_estimates, 'growth_estimates'].apply(lambda x: x.get('+1y')).apply(lambda x: x.get('stockTrend'))*100
    # info.loc[is_growth_estimates, 'growth_trend_y_next_%'] = values
    # info = info.drop('growth_estimates', axis=1)

    def get_param_info(self, param):
        return self.params.get_param_info(param)
