from ..tickers import Tickers
from ..vault import Vault
from ..viz import Viz
import pandas as pd
import numpy as np
from pprint import pp
from ..utils import storage
from ..database import Database
from datetime import datetime

class Analysis():

    def __init__(self, symbols=[], update=False, forced=False, cache_update=False):
        self.db = Database('analysis')
        self.vault = Vault()
        self.__get_data(symbols, update, forced, cache_update)
        # self.viz = Viz()
        # self.benchmarks = Tickers(['SPY', 'QQQ'])

    def get_data(self, active_only=True):
        if active_only:
            return self.data[self.data['active'] == True].copy()
        else:
            return self.data.copy()
    
    def __cache_update(self, symbols, update, forced):
        print('update cache %s symbols' % (len(symbols)))
        tickers = Tickers(symbols)
        if tickers.empty: return data

        # start data
        data = tickers.get_symbols_dataframe()

        # get analysis
        print('Get Analysis:')
        analysis = tickers.get_analysis(update=update, forced=forced)
        analysis['type'] = data['type']

        # merge info
        print('Info:')
        info = analysis['info']

        # handle funds info
        is_fund_overview = info['fund_overview'].notna()
        info.loc[is_fund_overview, 'fund_category'] = info.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('categoryName'))
        info.loc[is_fund_overview, 'fund_family'] = info.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('family'))
        info = info.drop('fund_overview', axis=1)
        
        # handle growth estimates
        is_growth_estimates = info['growth_estimates'].notna()
        values = info.loc[is_growth_estimates, 'growth_estimates'].apply(lambda x: x.get('0q')).apply(lambda x: x.get('stockTrend'))*100
        info.loc[is_growth_estimates, 'growth_trend_q_cur_%'] = values
        values = info.loc[is_growth_estimates, 'growth_estimates'].apply(lambda x: x.get('+1q')).apply(lambda x: x.get('stockTrend'))*100
        info.loc[is_growth_estimates, 'growth_trend_q_next_%'] = values
        values = info.loc[is_growth_estimates, 'growth_estimates'].apply(lambda x: x.get('0y')).apply(lambda x: x.get('stockTrend'))*100
        info.loc[is_growth_estimates, 'growth_trend_y_cur_%'] = values
        values = info.loc[is_growth_estimates, 'growth_estimates'].apply(lambda x: x.get('+1y')).apply(lambda x: x.get('stockTrend'))*100
        info.loc[is_growth_estimates, 'growth_trend_y_next_%'] = values
        info = info.drop('growth_estimates', axis=1)

        data = data.merge(info, how='left', left_index=True, right_index=True)
        
        # fix 'infinity' from info
        for column in data.columns[data.apply(lambda x: 'Infinity' in x.values)]:
            data.loc[data[column] == 'Infinity', column] = np.nan

        # get charts data and valid anaylsis
        if True:
            chart_data = self.__get_chart_data(analysis)
            data = data.merge(chart_data, how='left', left_index=True, right_index=True)

        # get ttm fundamentals
        if True:
            trailing = analysis['trailing'].copy()
            if 'income_operating' in trailing.columns and 'revenue_total' in trailing.columns:
                trailing['operating_profit_margin_ttm_%'] = (trailing['income_operating'] / trailing['revenue_total']) * 100
            if 'income_net' in trailing.columns and 'revenue_total' in trailing.columns:
                trailing['net_profit_margin_ttm_%_%'] = (trailing['income_net'] / trailing['revenue_total']) * 100

            columns_keep = [
                'eps',
                'operating_profit_margin_ttm_%',
                'net_profit_margin_ttm_%',
            ]
            columns = [c for c in trailing.columns if c in columns_keep]
            trailing = trailing[columns]

            columns_rename = {
                'eps': 'eps_ttm_fundamental',
            }
            trailing = trailing.rename(columns=columns_rename)
            data = data.merge(trailing, how='left', left_index=True, right_index=True)

        # get periodic fundamentals
        if True:
            yearly = self.__get_fundamentals(analysis, 'yearly')
            quarterly = self.__get_fundamentals(analysis, 'quarterly')
            data = data.merge(yearly, how='left', left_index=True, right_index=True)
            data = data.merge(quarterly, how='left', left_index=True, right_index=True)

        # sort columns
        columns_main = [c for c in ['name', 'type', 'sub_type', 'sector', 'industry'] if c in data.columns]
        columns = columns_main + sorted([x for x in data.columns if x not in columns_main])
        data = data[columns]

        # infer al object columns
        data = data.infer_objects()

        # write to db
        self.db.backup()
        self.db.table_write('analysis', data)

        return data        

    def __get_chart_data(self, analysis):
        print('charts:')
        chart_data = pd.DataFrame()

        now = pd.Timestamp.now()
        # two_months_ago = pd.Timestamp.now() - pd.DateOffset(months=2)
        # one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
        for symbol, chart in analysis['chart'].items():
            # find of stock is still active
            chart_volume = chart[chart['volume'] > 0]
            chart_data.loc[symbol, 'active'] = False
            symbol_type = analysis['type'].loc[symbol]
            if symbol_type == 'EQUITY':
                if chart_volume.empty: continue
                inactive_days = (now - (chart_volume.index[-1])).days
                if inactive_days > 30: continue
            chart_data.loc[symbol, 'active'] = True
            
            # get dividends data
            if not 'dividends' in chart.columns: continue
            
            # there are some price values that are strings because of Infinity
            chart['price'] = chart['price'].astype(float, errors='ignore')
            chart_dividends = chart[chart['dividends'] > 0]
            if chart_dividends.empty: continue

            # yearly dividends data
            first_year = chart_dividends.index[0].year + 1
            last_year = datetime.now().year-1
            chart_dividends_yearly = chart_dividends[(chart_dividends.index.year >= first_year) & (chart_dividends.index.year <= last_year)]
            dividends = chart_dividends_yearly['dividends'].groupby(chart_dividends_yearly.index.year)
            price = chart_dividends_yearly['price'].groupby(chart_dividends_yearly.index.year)
            dividend_count_yearly = dividends.size()
            dividend_rate_yearly = dividends.sum()
            dividend_price_yearly = price.mean()
            years_count = dividend_count_yearly.shape[0]
            chart_data.loc[symbol, 'dividend_years'] = years_count

            # get trends and stds
            if years_count > 1:
                slope, start = np.polyfit(range(years_count), dividend_rate_yearly.values, 1)
                trend = range(years_count)*slope + start
                trend_mean = np.mean(trend)
                dividend_rate_yearly_trend_percent = ((trend[-1] - trend[0]) / trend_mean) * 100
                chart_data.loc[symbol, 'dividend_rate_yearly_trend_%'] = dividend_rate_yearly_trend_percent
                dividend_rate_yearly_flat = dividend_rate_yearly - trend + trend_mean
                dividend_rate_yearly_std_percent = (dividend_rate_yearly_flat.std() / dividend_rate_yearly_flat.mean()) * 100
                chart_data.loc[symbol, 'dividend_rate_yearly_std_%'] = dividend_rate_yearly_std_percent

            # get last year data
            if last_year in dividend_rate_yearly.index:
                dividend_rate_last_year = dividend_rate_yearly.loc[last_year]
                # chart_data.loc[symbol, 'dividend_rate_last_year_$'] = dividend_rate_last_year
                dividend_yield_last_year_percent = (dividend_rate_last_year / dividend_price_yearly.loc[last_year]) * 100
                chart_data.loc[symbol, 'dividend_yield_last_year_%'] = dividend_yield_last_year_percent
            
            # get ttm data
            dividends_ttm = chart_dividends.loc[chart_dividends.index > (datetime.now() - pd.DateOffset(months=12))]['dividends']
            if not dividends_ttm.empty:
                dividend_count_ttm = dividends_ttm.shape[0]
                dividend_rate_ttm = dividends_ttm.sum()
                # chart_data.loc[symbol, 'dividends_rate_ttm_$'] = dividend_rate_ttm
                dividends_yield_ttm_percent = (dividend_rate_ttm / chart['price'].iloc[-1]) * 100
                chart_data.loc[symbol, 'dividends_yield_ttm_%'] = dividends_yield_ttm_percent
                if last_year in dividend_rate_yearly.index:
                    dividends_rate_ttm_trend_percent = ((dividend_rate_ttm / dividend_rate_last_year) * 100) - 100
                    chart_data.loc[symbol, 'dividends_rate_ttm_trend_%'] = dividends_rate_ttm_trend_percent
            
        return chart_data

    def __get_fundamentals(self, analysis, period):
        print('fundamentals: %s' % period)
        period_single = period.rstrip('ly')
        df_period = pd.DataFrame()
        do_save = True
        for symbol, period_symbol in analysis[period].items():
            period_symbol = period_symbol.dropna(how='all').copy()
            year_count = period_symbol.shape[0]

            # add metrics
            if 'debt_current' in period_symbol.columns and 'cash' in period_symbol.columns:
                period_symbol['debt_v_cash_%s_%%' % (period_single)] = (period_symbol['debt_current'] / period_symbol['cash'])*100
            if 'assets_current' in period_symbol.columns and 'liabilities_current' in period_symbol.columns:
                period_symbol['liquidity_%s_%%' % (period_single)] = (period_symbol['assets_current'] / period_symbol['liabilities_current'])*100
            if 'income_operating' in period_symbol.columns and 'revenue_total' in period_symbol.columns:
                period_symbol['operating_profit_margin_%s_%%' % (period_single)] = (period_symbol['income_operating'] / period_symbol['revenue_total'])*100
            if 'income_net' in period_symbol.columns and 'revenue_total' in period_symbol.columns:
                period_symbol['net_profit_margin_%s_%%' % (period_single)] = (period_symbol['income_net'] / period_symbol['revenue_total'])*100
            if 'free_cash_flow' in period_symbol.columns:
                period_symbol = period_symbol.rename(columns={'free_cash_flow': 'free_cash_flow_%s' % (period_single)})

            # calculate trends
            if year_count > 1:
                trends = period_symbol.dropna(axis=1, how='all').apply(lambda x: np.polyfit(range(year_count), x, 1)).head(1)
                trends = trends / period_symbol.iloc[0]
                trends.index = [symbol]
                trends.index.name = 'symbol'
                rename_trends = {c: '%s_trend' % (c) for c in trends.columns}
                trends = trends.rename(columns=rename_trends)

            # last year entries
            period_symbol = period_symbol.tail(1).copy()
            period_symbol.index = [symbol]
            period_symbol.index.name = 'symbol'

            if year_count > 1:
                period_symbol = period_symbol.merge(trends, how='left', left_index=True, right_index=True)
            period_symbol = period_symbol.dropna(axis=1)
            
            if df_period.empty:
                df_period = period_symbol
            elif not period_symbol.empty:
                df_period = pd.concat([df_period,  period_symbol])
        
        columns_keep = [
            'eps',
            'eps_trend',
            'debt_v_cash_%s_%%' % (period_single),
            'debt_v_cash_%s_%%_trend' % (period_single),
            'liquidity_%s_%%' % (period_single),
            'liquidity_%s_%%_trend' % (period_single),
            'operating_profit_margin_%s_%%' % (period_single),
            'operating_profit_margin_%s_%%_trend' % (period_single),
            'net_profit_margin_%s_%%' % (period_single),
            'net_profit_margin_%s_%%_trend' % (period_single),
            'free_cash_flow_%s_trend' % (period_single),
        ]
        columns = [c for c in df_period.columns if c in columns_keep]
        df_period = df_period[columns]

        columns_rename = {
            'eps': 'eps_%s' % (period_single),
            'eps_trend': 'eps_%s_trend' % (period_single),
        }
        df_period = df_period.rename(columns=columns_rename)

        return df_period

    def __cache_get(self, symbols, update, forced):
        if len(symbols) == 0:
            symbols = Tickers().get_symbols()
        data =  self.db.table_read('analysis', keys=symbols)
        not_found = sorted(set(symbols).difference(set(data.index)))
        if len(not_found) > 0:
            cached = self.__cache_update(not_found, update, forced)
            if data.empty:
                data = cached
            elif not cached.empty:
                data = pd.concat([data, cached])
            data.sort_index(inplace=True)

        return data
    
    def __get_data(self, symbols, update, forced, cache_update=False):
        # check if database needs to be cached
        if update: cache_update = True
        # TODO Needs status_db check to do it correctly
        analysis_timestamps = self.vault.get_db_timestamps('analysis')
        for db_name, db_timestamps in analysis_timestamps.items():
            if db_timestamps > self.db.timestamp: cache_update = True

        if cache_update:
            self.data = self.__cache_update(symbols, update, forced)
        else:
            self.data = self.__cache_get(symbols, update, forced)

        return
        