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

    def __cache_update(self, symbols, update, forced):
        tickers = Tickers(symbols)
        data = tickers.get_symbols_dataframe()
        if data.empty: return data

        print('update cache %s symbols' % (len(symbols)))

        # get analysis
        analysis = tickers.get_analysis(update=update, forced=forced)

        # merge info
        data = data.merge(analysis['info'], how='left', left_index=True, right_index=True)
        
        # fix 'infinity'
        for column in data.columns[data.apply(lambda x: 'Infinity' in x.values)]:
            data.loc[data[column] == 'Infinity', column] = np.nan

        # get ttm fundamentals
        trailing = analysis['trailing'].copy()
        if 'income_operating' in trailing.columns and 'revenue_total' in trailing.columns:
            trailing['operating_profit_margin_ttm'] = trailing['income_operating'] / trailing['revenue_total']
        if 'income_net' in trailing.columns and 'revenue_total' in trailing.columns:
            trailing['net_profit_margin_ttm'] = trailing['income_net'] / trailing['revenue_total']

        columns_keep = [
            'eps',
            'operating_profit_margin_ttm',
            'net_profit_margin_ttm',
        ]
        columns = [c for c in trailing.columns if c in columns_keep]
        trailing = trailing[columns]

        columns_rename = {
            'eps': 'eps_ttm_fundamental',
        }
        trailing = trailing.rename(columns=columns_rename)

        # get periodic fundamentals
        yearly = self.__get_fundamentals(analysis, 'yearly')
        quarterly = self.__get_fundamentals(analysis, 'quarterly')

        # merge them all together
        data = data.merge(trailing, how='left', left_index=True, right_index=True)
        data = data.merge(yearly, how='left', left_index=True, right_index=True)
        data = data.merge(quarterly, how='left', left_index=True, right_index=True)

        # sort fundamentals columns
        columns_main = ['name', 'type', 'sub_type', 'sector', 'industry']
        columns = columns_main + sorted([x for x in data.columns if x not in columns_main])
        data = data[columns]

        # infer al object columns
        data = data.infer_objects()

        # write to db
        self.db.backup()
        self.db.table_write('analysis', data)

        return data

    def __get_fundamentals(self, analysis, period):
        print(period)
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
        analysis_timestamps = self.vault.get_db_timestamps('analysis')
        for db_name, db_timestamps in analysis_timestamps.items():
            if db_timestamps > self.db.timestamp: cache_update = True

        if cache_update:
            self.data = self.__cache_update(symbols, update, forced)
        else:
            self.data = self.__cache_get(symbols, update, forced)

        return
        