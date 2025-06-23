from ..tickers import Tickers
# from ..vault import Vault
from ..viz import Viz
import pandas as pd
import numpy as np
from pprint import pp
from ..utils import storage
from datetime import datetime
import time

class Analysis():
    @ staticmethod
    def __get_param(data, param):
        # recursively go through param keys to find value
        if isinstance(data, dict):
            keys = param.split(':')
            key = keys[0]
            if key in data:
                if len(keys) == 1: return data[key]
                new_param = ':'.join(keys[1:])
                return Analysis.__get_param(data[key], new_param)
        return None

    def __init__(self, tickers, update=False, forced=False):
        self.tickers = tickers
        self.__get_data(update, forced)
        return
        self.viz = Viz()
        # self.benchmarks = Tickers(['SPY', 'QQQ'])

    def test(self, symbol, date):
        if not symbol in self.symbols: return
        symbol_data = self.symbols[symbol]
        if symbol_data['type'] != 'EQUITY': return
        if symbol_data['sector'] == None: return
        sector = symbol_data['sector']
        # df = self.sector_indices[[sector]].loc[date:]
        df = self.sector_indices[[sector]]
        df_symbol = self.charts[symbol]['Adj Close']
        first_date = df_symbol.index[0]
        df = df.join(self.charts[symbol]['Adj Close'])
        df = df.loc[first_date:].loc[date:]
        df['Adj Close'] = df['Adj Close'].ffill()
        df = df.rename(columns={'Adj Close': symbol})
        # df = (df / df.iloc[0]) - 1.0
        df = (df / df.iloc[0])
        print(df)
        self.viz.plot_dataframe(df-1.0, line=0.0)
        df['compare'] = (df[symbol]/df[sector])-1.0
        df['follow'] = (df[symbol]-1.0)/(df[sector]-1.0)
        df['follow'] = df['follow'].clip(lower=-10, upper=10)
        self.viz.plot_dataframe(df[['compare']], line=0.0)
        self.viz.plot_dataframe(df[['follow']], line=0.0)

        

    
    def get_values(self, param, symbols=[], only_values=False):
        values = {}
        if len(symbols) > 0:
            for symbol in symbols:
                if symbol not in self.symbols: continue
                symbol_data = self.symbols[symbol]
                value = Analysis.__get_param(symbol_data, param)
                values[symbol] = value
        else:
            for symbol, symbol_data in self.symbols.items():
                value = Analysis.__get_param(symbol_data, param)
                values[symbol] = value
        if not only_values:
            return values
        values = [v for s,v in values.items() if v != None]
        return sorted(values)

    def __get_data(self, update, forced):
        # get data
        self.data = self.tickers.get_profiles(update=update, forced=forced)
        analysis = self.tickers.get_analysis(update=update, forced=forced)
        
        # merge info
        self.data = self.data.merge(analysis['info'], how='left', left_index=True, right_index=True)
        # fix 'infinity'
        self.data.loc[self.data['pe'].apply(lambda x: isinstance(x, str)), 'pe'] = np.nan
        self.data.loc[self.data['ps_ttm'].apply(lambda x: isinstance(x, str)), 'ps_ttm'] = np.nan

        # analysis['info']['data_time'] = pd.to_datetime(analysis['info']['data_time'], unit='s').dt.tz_localize('UTC').dt.tz_convert('US/Pacific')
        # self.data = profile.merge(analysis['info'], how='left', left_index=True, right_index=True)

        # merge last year fundamentals
        yearly = pd.DataFrame()
        for symbol, yearly_symbol in analysis['yearly'].items():
            # free cashflow trends
            free_cash_flow = None
            if 'free_cash_flow' in yearly_symbol:
                free_cash_flow = yearly_symbol['free_cash_flow'].dropna()
                free_cash_flow = (free_cash_flow / free_cash_flow.iloc[0]).mean()

            # last year entries
            yearly_symbol = yearly_symbol.tail(1).copy()
            yearly_symbol.index = [symbol]
            yearly_symbol.index.name = 'symbol'
            if free_cash_flow != None: yearly_symbol['free_cash_flow_trend_yearly'] = free_cash_flow
            yearly = pd.concat([yearly,  yearly_symbol.tail(1)])
        yearly['debt_v_cash_year'] = yearly['debt_current'] / yearly['cash']
        yearly['liquidity_year'] = yearly['assets_current'] / yearly['liabilities_current']
        yearly['net_profit_margin_year'] = yearly['income_net'] / yearly['revenue_total']
        columns_keep = ['debt_v_cash_year', 'liquidity_year', 'net_profit_margin_year', 'free_cash_flow_trend_yearly']
        columns = [c for c in yearly.columns if c in columns_keep]
        yearly = yearly[columns]
        self.data = self.data.merge(yearly, how='left', left_index=True, right_index=True)
        
        # merge last quarter fundamentals
        quarterly = pd.DataFrame()
        for symbol, quarterly_symbol in analysis['quarterly'].items():
            # free cashflow trends
            free_cash_flow = None
            if 'free_cash_flow' in quarterly_symbol:
                free_cash_flow = quarterly_symbol['free_cash_flow'].dropna()
                free_cash_flow = (free_cash_flow / free_cash_flow.iloc[0]).mean()

            # last quarter entries
            quarterly_symbol = quarterly_symbol.tail(1).copy()
            quarterly_symbol.index = [symbol]
            quarterly_symbol.index.name = 'symbol'
            if free_cash_flow != None: quarterly_symbol['free_cash_flow_trend_quarterly'] = free_cash_flow
            quarterly = pd.concat([quarterly,  quarterly_symbol.tail(1)])
        quarterly['debt_v_cash_quarter'] = quarterly['debt_current'] / quarterly['cash']
        quarterly['liquidity_quarter'] = quarterly['assets_current'] / quarterly['liabilities_current']
        quarterly['net_profit_margin_quarter'] = quarterly['income_net'] / quarterly['revenue_total']
        columns_keep = ['debt_v_cash_quarter', 'liquidity_quarter', 'net_profit_margin_quarter', 'free_cash_flow_trend_quarterly']
        columns = [c for c in quarterly.columns if c in columns_keep]
        quarterly = quarterly[columns]
        self.data = self.data.merge(quarterly, how='left', left_index=True, right_index=True)


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



