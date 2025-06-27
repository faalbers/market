from ..tickers import Tickers
from ..vault import Vault
from ..viz import Viz
import pandas as pd
import numpy as np
from pprint import pp
from ..utils import storage
from ..database import Database
from datetime import datetime
import time

class Analysis():

    def __init__(self, symbols=[], update=False, forced=False):
        self.db = Database('analysis')
        self.vault = Vault()
        self.__get_data(symbols, update, forced)
        # self.viz = Viz()
        # self.benchmarks = Tickers(['SPY', 'QQQ'])

    def __cache_update(self, symbols, update, forced):
        tickers = Tickers(symbols)
        data = tickers.get_symbols_dataframe()
        if data.empty: return data
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

        # infer al object columns
        data = data.infer_objects()
        # pp(data.columns.to_list())
        # print(data)

        # write to db
        self.db.table_write('analysis', data)

        return data

    def __get_fundamentals(self, analysis, period):
        print(period)
        period_single = period.rstrip('ly')
        df_period = pd.DataFrame()
        for symbol, period_symbol in analysis[period].items():
            period_symbol = period_symbol.dropna(how='all').copy()
            year_count = period_symbol.shape[0]

            # add metrics
            if 'debt_current' in period_symbol.columns and 'cash' in period_symbol.columns:
                period_symbol['debt_v_cash_%s' % (period_single)] = period_symbol['debt_current'] / period_symbol['cash']
            if 'assets_current' in period_symbol.columns and 'liabilities_current' in period_symbol.columns:
                period_symbol['liquidity_%s' % (period_single)] = period_symbol['assets_current'] / period_symbol['liabilities_current']
            if 'income_operating' in period_symbol.columns and 'revenue_total' in period_symbol.columns:
                period_symbol['operating_profit_margin_%s' % (period_single)] = period_symbol['income_operating'] / period_symbol['revenue_total']
            if 'income_net' in period_symbol.columns and 'revenue_total' in period_symbol.columns:
                period_symbol['net_profit_margin_%s' % (period_single)] = period_symbol['income_net'] / period_symbol['revenue_total']
            if 'free_cash_flow' in period_symbol.columns:
                period_symbol = period_symbol.rename(columns={'free_cash_flow': 'free_cash_flow_%s' % (period_single)})

            # calculate trends
            if year_count > 1:
                trends = period_symbol.apply(lambda x: np.polyfit(range(year_count), x, 1)).head(1)
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
            df_period = pd.concat([df_period,  period_symbol])
        
        columns_keep = [
            'eps',
            'eps_trend',
            'debt_v_cash_%s' % (period_single),
            'debt_v_cash_%s_trend' % (period_single),
            'liquidity_%s' % (period_single),
            'liquidity_%s_trend' % (period_single),
            'operating_profit_margin_%s' % (period_single),
            'operating_profit_margin_%s_trend' % (period_single),
            'net_profit_margin_%s' % (period_single),
            'net_profit_margin_%s_trend' % (period_single),
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
            print('update %s symbols' % (len(not_found)))
            cached = self.__cache_update(not_found, update, forced)
            if data.shape[0] == 0:
                data = cached
            else:
                data = pd.concat([data, cached])
            data.sort_index(inplace=True)

        return data
    
    def __get_data(self, symbols, update, forced):

        # check if database needs to be cached
        analysis_timestamps = self.vault.get_db_timestamps('analysis')
        cache_update = False
        for db_name, db_timestamps in analysis_timestamps.items():
            if db_timestamps > self.db.timestamp: cache_update = True

        if cache_update:
            self.data = self.__cache_update(symbols, update, forced)
        else:
            self.data = self.__cache_get(symbols, update, forced)

        return
        
        # data = self.db.table_read('analysis', keys=key_values, columns=column_names)
        # db = Database('analysis')
        
        # self.data = self.tickers.get_profiles(update=update, forced=forced)
        # analysis = self.tickers.get_analysis(update=update, forced=forced)

        # for data_name, data in analysis.items():
        #     if not data_name.endswith('_db_timestamp'): continue
        return
        
        return

        # analysis['info']['data_time'] = pd.to_datetime(analysis['info']['data_time'], unit='s').dt.tz_localize('UTC').dt.tz_convert('US/Pacific')
        # self.data = profile.merge(analysis['info'], how='left', left_index=True, right_index=True)

        # # get sector charts
        # sectors = {
        #     'XLV': 'Healthcare',
        #     'XLB': 'Basic Materials',
        #     'XLK': 'Technology',
        #     'XLF': 'Financial Services',
        #     'XLI': 'Industrials',
        #     'XLRE': 'Real Estate',
        #     'XLC': 'Communication Services',
        #     'XLU': 'Utilities',
        #     'XLE': 'Energy',
        #     'XLP': 'Consumer Defensive',
        #     'XLY': 'Consumer Cyclical',
        #     'SPY': 'S&P500',
        # }
        # sector_tickers = Tickers(list(sectors.keys()))
        # sector_charts = sector_tickers.get_charts(update=update, forced=forced)
        # self.sector_indices = sector_charts['SPY'][['Close']]
        # self.sector_indices = self.sector_indices.rename(columns={'Close': 'S&P500'})
        # for sector_symbol, sector in sectors.items():
        #     if sector_symbol == 'SPY': continue
        #     if not sector_symbol in sector_charts:
        #         raise Exception('sector ticker not found: %s' % sector_symbol)
        #     self.sector_indices = self.sector_indices.join(sector_charts[sector_symbol]['Close'])
        #     self.sector_indices = self.sector_indices.rename(columns={'Close': sector})
        # # pp(self.sector_indices.round(2))

    # @ staticmethod
    # def __get_param(data, param):
    #     # recursively go through param keys to find value
    #     if isinstance(data, dict):
    #         keys = param.split(':')
    #         key = keys[0]
    #         if key in data:
    #             if len(keys) == 1: return data[key]
    #             new_param = ':'.join(keys[1:])
    #             return Analysis.__get_param(data[key], new_param)
    #     return None

    # def test(self, symbol, date):
    #     if not symbol in self.symbols: return
    #     symbol_data = self.symbols[symbol]
    #     if symbol_data['type'] != 'EQUITY': return
    #     if symbol_data['sector'] == None: return
    #     sector = symbol_data['sector']
    #     # df = self.sector_indices[[sector]].loc[date:]
    #     df = self.sector_indices[[sector]]
    #     df_symbol = self.charts[symbol]['Adj Close']
    #     first_date = df_symbol.index[0]
    #     df = df.join(self.charts[symbol]['Adj Close'])
    #     df = df.loc[first_date:].loc[date:]
    #     df['Adj Close'] = df['Adj Close'].ffill()
    #     df = df.rename(columns={'Adj Close': symbol})
    #     # df = (df / df.iloc[0]) - 1.0
    #     df = (df / df.iloc[0])
    #     print(df)
    #     self.viz.plot_dataframe(df-1.0, line=0.0)
    #     df['compare'] = (df[symbol]/df[sector])-1.0
    #     df['follow'] = (df[symbol]-1.0)/(df[sector]-1.0)
    #     df['follow'] = df['follow'].clip(lower=-10, upper=10)
    #     self.viz.plot_dataframe(df[['compare']], line=0.0)
    #     self.viz.plot_dataframe(df[['follow']], line=0.0)

    # def get_values(self, param, symbols=[], only_values=False):
    #     values = {}
    #     if len(symbols) > 0:
    #         for symbol in symbols:
    #             if symbol not in self.symbols: continue
    #             symbol_data = self.symbols[symbol]
    #             value = Analysis.__get_param(symbol_data, param)
    #             values[symbol] = value
    #     else:
    #         for symbol, symbol_data in self.symbols.items():
    #             value = Analysis.__get_param(symbol_data, param)
    #             values[symbol] = value
    #     if not only_values:
    #         return values
    #     values = [v for s,v in values.items() if v != None]
    #     return sorted(values)

    # def get_params(self):
    #     def fix_key(key):
    #         if key.isupper(): return'<symbol>'
    #         if key.isnumeric():
    #             if len(key) == 10: return'<timestamp>'
    #             return'<number>'
    #         return key
    #     def recurse_params(data, params, parent):
    #         if isinstance(data, dict):
    #             for key, value in data.items():
    #                 key = fix_key(key)
    #                 if parent != '':
    #                     param_key = '%s:%s' % (parent, key)
    #                 else:
    #                     param_key = key
    #                 if not param_key in params:
    #                     params[param_key] = set()
    #                 params[param_key].add(type(value))
    #                 recurse_params(value, params, param_key)
    #     params = {}
    #     for symbol, symbol_data in self.symbols.items():
    #         recurse_params(symbol_data, params, '')
    #     return params

    # def sector_industry(self):
    #     pp(sorted(self.sector_indices.columns))
    #     pp(sorted(self.data['sector'].dropna().unique()))
    
    # def sector_industry_old(self):
    #     params = self.get_params()
    #     param_names = sorted(params)
    #     for param in param_names:
    #         print(param,':', params[param])

    #     sector_industry = {'sectors': {}}
    #     params = [
    #         'price_to_earnings_trailing',
    #         'price_to_earnings_forward',
    #         'dividend_yield',
    #     ]
    #     for symbol, symbol_data in self.symbols.items():
    #         if symbol_data['type'] != 'EQUITY': continue
    #         if symbol_data['sector'] == None: continue

    #         # greate sector industry hierarchy
    #         sector_data = sector_industry['sectors']
    #         if not symbol_data['sector'] in sector_data:
    #             sector_data[symbol_data['sector']] = {'industries': {}, 'params': {}, 'count': 0}
    #         sector_data[symbol_data['sector']]['count'] += 1
    #         industries_data = sector_data[symbol_data['sector']]['industries']
    #         sector_params = sector_data[symbol_data['sector']]['params']
    #         if not symbol_data['industry'] in industries_data:
    #             industries_data[symbol_data['industry']] = {'params': {}, 'count': 0}
    #         industries_data[symbol_data['industry']]['count'] += 1
    #         industry_params = industries_data[symbol_data['industry']]['params']
            
    #         # add params
    #         for param in params:
    #             if symbol_data[param] == None: continue
    #             if isinstance(symbol_data[param], str): continue # skip 'Infinity'

    #             # add sector params
    #             if not param in sector_params:
    #                 sector_params[param] = {'values': []}
    #             sector_params[param]['values'].append(symbol_data[param])

    #             # add industry params
    #             if not param in industry_params:
    #                 industry_params[param] = {'values': []}
    #             industry_params[param]['values'].append(symbol_data[param])

    #     # calculate averages
    #     with open('sector_industry.txt', 'w') as f:
    #         for sector, sector_data in sector_industry['sectors'].items():
    #             # handle sector params
    #             f.write('%s: %s\n' % (sector, sector_data['count']))
    #             for param, param_data in sector_data['params'].items():
    #                 param_data['count'] = len(param_data['values'])
    #                 param_data['mean'] = np.mean(param_data['values']).round(2)
    #                 param_data.pop('values')
    #                 f.write('\t%s (%s, count = %s)\n' % (param_data['mean'], param, param_data['count']))
    #             f.write('\n')
    #             for industry, industry_data in sector_data['industries'].items():
    #                 # handle industry params
    #                 f.write('\t%s: %s\n' % (industry, industry_data['count']))
    #                 for param, param_data in industry_data['params'].items():
    #                     param_data['count'] = len(param_data['values'])
    #                     param_data['mean'] = np.mean(param_data['values']).round(2)
    #                     param_data.pop('values')
    #                     f.write('\t\t%s (%s, count = %s)\n' % (param_data['mean'], param, param_data['count']))
    #                 f.write('\n')

    #     # 1. **Low P/E Ratio (< 10):** May indicate undervalued stocks with potential for growth.
    #     # 2. **Moderate P/E Ratio (10-20):** Indicates a relatively fair valuation, with some room for growth.
    #     # 3. **High P/E Ratio (> 20):** Suggests overvaluation, but may be due to high growth expectations or a strong
    #     # market.
    #     # 4. **P/E Ratio > 30:** Typically indicates an overvalued stock with limited potential for growth.        



