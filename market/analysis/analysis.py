from ..tickers import Tickers
from ..vault import Vault
from ..viz import Viz
import pandas as pd
import numpy as np
from pprint import pp
from ..utils import storage
from ..database import Database
from datetime import datetime
import talib as ta

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
        print('Get Analysis: done')
        analysis['type'] = data['type']

        # merge info
        print('Info:')
        info = analysis['info']

        # handle funds info
        if True:
            is_fund_overview = info['fund_overview'].notna()
            info.loc[is_fund_overview, 'fund_category'] = info.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('categoryName'))
            info.loc[is_fund_overview, 'fund_family'] = info.loc[is_fund_overview, 'fund_overview'].apply(lambda x: x.get('family'))
            info = info.drop('fund_overview', axis=1)
        
        # handle growth estimates
        if True:
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
                column_name = 'operating_profit_margin_ttm_%'
                trailing[column_name] = np.nan
                is_revenue = (trailing['revenue_total'] > 0.0) & (trailing['income_operating'] <= trailing['revenue_total'])
                if is_revenue.any():
                    trailing.loc[is_revenue, column_name] = \
                        (trailing.loc[is_revenue, 'income_operating'] / trailing.loc[is_revenue, 'revenue_total']) * 100
            if 'income_net' in trailing.columns and 'revenue_total' in trailing.columns:
                column_name = 'net_profit_margin_ttm_%'
                trailing[column_name] = np.nan
                is_revenue = (trailing['revenue_total'] > 0.0) & (trailing['income_net'] <= trailing['revenue_total'])
                if is_revenue.any():
                    trailing.loc[is_revenue, column_name] = \
                        (trailing.loc[is_revenue, 'income_net'] / trailing.loc[is_revenue, 'revenue_total']) * 100

            columns_keep = [
                'eps',
                'operating_profit_margin_ttm_%',
                'net_profit_margin_ttm_%',
            ]
            columns = [c for c in trailing.columns if c in columns_keep]
            trailing = trailing[columns]

            columns_rename = {
                'eps': 'eps_ttm_fundamental_$',
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
        for symbol, chart in analysis['chart'].items():
            # find if stock is still active
            chart_volume = chart[chart['volume'] > 0]
            chart_data.loc[symbol, 'active'] = False
            symbol_type = analysis['type'].loc[symbol]
            if symbol_type in ['EQUITY', 'ETF']:
                # only check volume on EQUITY and ETF stocks
                # Mutual funds and indices typically don't have volume data displayed on their charts
                if chart_volume.empty: continue
                inactive_days = (now - (chart_volume.index[-1])).days
                if inactive_days > 30: continue

            chart_data.loc[symbol, 'active'] = True

            # get mark minervini classifications
            current_price = chart.iloc[-1]['price']

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
            chart_data.loc[symbol, 'minervini_score_%'] = minervini_score_percent

            # get dividends data
            if not 'dividends' in chart.columns: continue
            
            # there are some price values that are strings because of Infinity
            chart['price'] = chart['price'].astype(float, errors='ignore')
            chart_dividends = chart[chart['dividends'] > 0]
            if chart_dividends.empty: continue

            # yearly dividends data

            # get range between first full year and last full year
            first_year = chart_dividends.index[0].year + 1
            last_year = datetime.now().year-1
            chart_dividends_yearly = chart_dividends[(chart_dividends.index.year >= first_year) & (chart_dividends.index.year <= last_year)]
            
            # find yearly data
            dividends = chart_dividends_yearly['dividends'].groupby(chart_dividends_yearly.index.year)
            price = chart_dividends_yearly['price'].groupby(chart_dividends_yearly.index.year)
            dividend_count_yearly = dividends.size()
            dividend_rate_yearly = dividends.sum()
            dividend_price_yearly = price.mean()
            years_count = dividend_count_yearly.shape[0]
            chart_data.loc[symbol, 'dividend_years'] = years_count
            count_per_year = dividend_count_yearly.mean()
            chart_data.loc[symbol, 'dividend_count_yearly'] = count_per_year

            # get trends and stds for yearly data
            if years_count > 1:
                # calculate polyfit trend
                slope, start = np.polyfit(range(years_count), dividend_rate_yearly.values, 1)
                trend = range(years_count)*slope + start

                # get trend end value
                trend_end_value = trend[-1]

                # get trend percentage from trend end value
                dividend_rate_yearly_trend_percent = (slope / trend_end_value) * 100
                chart_data.loc[symbol, 'dividend_rate_yearly_%_trend'] = dividend_rate_yearly_trend_percent
                
                # get standard deviation from zero flatline
                dividend_rate_yearly_std = (dividend_rate_yearly - trend).std()

                # get std deviation percentage from trend end value
                dividend_rate_yearly_std_percent = (dividend_rate_yearly_std / trend_end_value ) * 100
                chart_data.loc[symbol, 'dividend_rate_yearly_std_%'] = dividend_rate_yearly_std_percent

            else:
                chart_data.loc[symbol, 'dividend_rate_yearly_%_trend'] = 0.0
                chart_data.loc[symbol, 'dividend_rate_yearly_std_%'] = 0.0

            # get last year data
            if last_year in dividend_rate_yearly.index:
                dividend_rate_last_year = dividend_rate_yearly.loc[last_year]
                # chart_data.loc[symbol, 'dividend_rate_last_year_$'] = dividend_rate_last_year
                dividend_yield_last_year_percent = (dividend_rate_last_year / dividend_price_yearly.loc[last_year]) * 100
                chart_data.loc[symbol, 'dividend_yield_last_year_%'] = dividend_yield_last_year_percent
            
            # get ttm data
            dividends_ttm = chart_dividends.loc[chart_dividends.index > (pd.Timestamp.now() - pd.DateOffset(months=12))]['dividends']
            if not dividends_ttm.empty:
                dividend_count_ttm = dividends_ttm.shape[0]
                dividend_rate_ttm = dividends_ttm.sum()
                # chart_data.loc[symbol, 'dividend_rate_ttm_$'] = dividend_rate_ttm
                dividends_yield_ttm_percent = (dividend_rate_ttm / chart['price'].iloc[-1]) * 100
                chart_data.loc[symbol, 'dividend_yield_ttm_%'] = dividends_yield_ttm_percent
                chart_data.loc[symbol, 'dividend_count_ttm'] = dividend_count_ttm
                
                # get ttm trend
                if dividend_count_ttm > 1:
                    # calculate polyfit trend
                    slope, start = np.polyfit(range(dividend_count_ttm), dividends_ttm.values, 1)
                    trend = range(dividend_count_ttm)*slope + start

                    # get trend end value
                    trend_end_value = trend[-1]

                    # get trend percentage from trend end value
                    dividend_rate_ttm_trend_percent = ((trend_end_value - start) / trend_end_value) * 100
                    chart_data.loc[symbol, 'dividend_rate_ttm_%_trend'] = dividend_rate_ttm_trend_percent
                    
                    # get standard deviation from zero flatline
                    dividend_rate_ttm_std = (dividends_ttm - trend).std()

                    # get std deviation percentage from trend end value
                    dividend_rate_ttm_std_percent = (dividend_rate_ttm_std / trend_end_value ) * 100
                    chart_data.loc[symbol, 'dividend_rate_ttm_std_%'] = dividend_rate_ttm_std_percent


                else:
                    chart_data.loc[symbol, 'dividend_rate_ttm_%_trend'] = 0.0
                    chart_data.loc[symbol, 'dividend_rate_ttm_std_%'] = 0.0

                # if last_year in dividend_rate_yearly.index:
                #     dividends_rate_ttm_trend_percent = ((dividend_rate_ttm / dividend_rate_last_year) * 100) - 100
                #     chart_data.loc[symbol, 'dividends_rate_ttm_trend_%'] = dividends_rate_ttm_trend_percent
        return chart_data

    def __get_fundamentals(self, analysis, period):
        print('fundamentals: %s' % period)
        period_single = period.rstrip('ly')
        df_period = pd.DataFrame()
        this_year = datetime.now().year
        for symbol, period_symbol in analysis[period].items():
            period_symbol = period_symbol.dropna(how='all').copy()
            if period_symbol.shape[0] == 0: continue
            if (this_year -period_symbol.index[-1].year) > 1: continue
            period_count = period_symbol.shape[0]

            # add metrics
            if 'debt_current' in period_symbol.columns and 'cash' in period_symbol.columns:
                column_name = 'cash_position_%s' % (period_single)
                period_symbol[column_name] = period_symbol['debt_current'] / period_symbol['cash']
            if 'assets_current' in period_symbol.columns and 'liabilities_current' in period_symbol.columns:
                column_name = 'liquidity_%s' % (period_single)
                period_symbol[column_name] = period_symbol['assets_current'] / period_symbol['liabilities_current']
            if 'income_operating' in period_symbol.columns and 'revenue_total' in period_symbol.columns:
                column_name = 'operating_profit_margin_%s_%%' % (period_single)
                period_symbol[column_name] = np.nan
                is_revenue = (period_symbol['revenue_total'] > 0.0) & (period_symbol['income_operating'] <= period_symbol['revenue_total'])
                if is_revenue.any():
                    period_symbol.loc[is_revenue, column_name] = \
                        (period_symbol.loc[is_revenue, 'income_operating'] / period_symbol.loc[is_revenue, 'revenue_total']) * 100
            if 'income_net' in period_symbol.columns and 'revenue_total' in period_symbol.columns:
                column_name = 'net_profit_margin_%s_%%' % (period_single)
                period_symbol[column_name] = np.nan
                is_revenue = (period_symbol['revenue_total'] > 0.0) & (period_symbol['income_net'] <= period_symbol['revenue_total'])
                if is_revenue.any():
                    period_symbol.loc[is_revenue, column_name] = \
                        (period_symbol.loc[is_revenue, 'income_net'] / period_symbol.loc[is_revenue, 'revenue_total']) * 100
            if 'free_cash_flow' in period_symbol.columns:
                period_symbol = period_symbol.rename(columns={'free_cash_flow': 'free_cash_flow_%s' % (period_single)})

            # calculate trends and standard deviation
            if period_count > 1:
                # prepare period trends calculation
                period_values = period_symbol.dropna(axis=1, how='all').copy()

                # to avoid errors with polyfit
                period_values = period_values.ffill().bfill()
                period_values = period_values.reset_index(drop=True)

                # get slope and start
                period_values_polyfit = period_values.apply(lambda x: np.polyfit(range(period_count), x, 1))
                period_trends_line = period_values_polyfit.apply(lambda x: (x[0]*range(period_count) + x[1]))

                # get trends
                period_trends = period_values_polyfit.iloc[0]
                period_trends.name = symbol
                period_trends = pd.DataFrame(period_trends).T
                rename_trends = {c: '%s_trend' % (c) for c in period_trends.columns}
                period_trends = period_trends.rename(columns=rename_trends)

                # get standard deviation from zero flatline
                period_std = (period_values - period_trends_line).std()
                period_std.name = symbol
                period_std = pd.DataFrame(period_std).T
                rename_std = {c: '%s_std' % (c) for c in period_std.columns}
                period_std = period_std.rename(columns=rename_std)

                # merge them together
                period_trends = period_trends.merge(period_std, how='left', left_index=True, right_index=True)

            # last year entries
            period_symbol = period_symbol.tail(1).copy()
            period_symbol.index = [symbol]
            period_symbol.index.name = 'symbol'

            if period_count > 1:
                period_symbol = period_symbol.merge(period_trends, how='left', left_index=True, right_index=True)
            period_symbol = period_symbol.dropna(axis=1)
            
            if df_period.empty:
                df_period = period_symbol
            elif not period_symbol.empty:
                df_period = pd.concat([df_period,  period_symbol])

        columns_keep = [
            'eps',
            'eps_trend',
            'eps_std',
            'cash_position_%s' % (period_single),
            'cash_position_%s_trend' % (period_single),
            'cash_position_%s_std' % (period_single),
            'liquidity_%s' % (period_single),
            'liquidity_%s_trend' % (period_single),
            'liquidity_%s_std' % (period_single),
            'operating_profit_margin_%s_%%' % (period_single),
            'operating_profit_margin_%s_%%_trend' % (period_single),
            'operating_profit_margin_%s_%%_std' % (period_single),
            'net_profit_margin_%s_%%' % (period_single),
            'net_profit_margin_%s_%%_trend' % (period_single),
            'net_profit_margin_%s_%%_std' % (period_single),
            'free_cash_flow_%s_trend' % (period_single),
            'free_cash_flow_%s_std' % (period_single),
        ]
        columns = [c for c in df_period.columns if c in columns_keep]
        df_period = df_period[columns]

        columns_rename = {
            'eps': 'eps_%s_$' % (period_single),
            'eps_trend': 'eps_%s_$_trend' % (period_single),
            'eps_std': 'eps_%s_$_std' % (period_single),
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
        