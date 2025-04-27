from ..tickers import Tickers
# from ..viz import Viz
import pandas as pd
import numpy as np
from pprint import pp
from ..utils import storage
from .gicsm import GICSM
from datetime import datetime
import time

class Analysis():
    equity_types = ['EQUITY', 'MUTUALFUND', 'ETF', 'INDEX', 'MONEYMARKET', 'ECNQUOTE']
    
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

    def __init__(self, tickers=None, recache=False):
        self.tickers = tickers
        self.__make_symbols(recache)
        # self.benchmarks = Tickers(['SPY', 'QQQ'])
        # self.viz = Viz()
        # self.vault = Vault()

    def test(self):
        print(self.charts['AAPL'])
        # values = self.get_values(['etrade_availability_info'])
        # for symbol, value in values.items():
        #     if value != None:
        #         print(symbol, value)

    def sector_industry(self):
        params = self.get_params()
        param_names = sorted(params)
        for param in param_names:
            print(param,':', params[param])

        sector_industry = {'sectors': {}}
        params = [
            'price_to_earnings_trailing',
            'price_to_earnings_forward',
            'dividend_yield',
        ]
        for symbol, symbol_data in self.symbols.items():
            if symbol_data['type'] != 'EQUITY': continue
            if symbol_data['sector'] == None: continue

            # greate sector industry hierarchy
            sector_data = sector_industry['sectors']
            if not symbol_data['sector'] in sector_data:
                sector_data[symbol_data['sector']] = {'industries': {}, 'params': {}, 'count': 0}
            sector_data[symbol_data['sector']]['count'] += 1
            industries_data = sector_data[symbol_data['sector']]['industries']
            sector_params = sector_data[symbol_data['sector']]['params']
            if not symbol_data['industry'] in industries_data:
                industries_data[symbol_data['industry']] = {'params': {}, 'count': 0}
            industries_data[symbol_data['industry']]['count'] += 1
            industry_params = industries_data[symbol_data['industry']]['params']
            
            # add params
            for param in params:
                if symbol_data[param] == None: continue
                if isinstance(symbol_data[param], str): continue # skip 'Infinity'

                # add sector params
                if not param in sector_params:
                    sector_params[param] = {'values': []}
                sector_params[param]['values'].append(symbol_data[param])

                # add industry params
                if not param in industry_params:
                    industry_params[param] = {'values': []}
                industry_params[param]['values'].append(symbol_data[param])

        # calculate averages
        with open('sector_industry.txt', 'w') as f:
            for sector, sector_data in sector_industry['sectors'].items():
                # handle sector params
                f.write('%s: %s\n' % (sector, sector_data['count']))
                for param, param_data in sector_data['params'].items():
                    param_data['count'] = len(param_data['values'])
                    param_data['mean'] = np.mean(param_data['values']).round(2)
                    param_data.pop('values')
                    f.write('\t%s (%s, count = %s)\n' % (param_data['mean'], param, param_data['count']))
                f.write('\n')
                for industry, industry_data in sector_data['industries'].items():
                    # handle industry params
                    f.write('\t%s: %s\n' % (industry, industry_data['count']))
                    for param, param_data in industry_data['params'].items():
                        param_data['count'] = len(param_data['values'])
                        param_data['mean'] = np.mean(param_data['values']).round(2)
                        param_data.pop('values')
                        f.write('\t\t%s (%s, count = %s)\n' % (param_data['mean'], param, param_data['count']))
                    f.write('\n')

        # 1. **Low P/E Ratio (< 10):** May indicate undervalued stocks with potential for growth.
        # 2. **Moderate P/E Ratio (10-20):** Indicates a relatively fair valuation, with some room for growth.
        # 3. **High P/E Ratio (> 20):** Suggests overvaluation, but may be due to high growth expectations or a strong
        # market.
        # 4. **P/E Ratio > 30:** Typically indicates an overvalued stock with limited potential for growth.        
        

    def get_params(self):
        def fix_key(key):
            if key.isupper(): return'<symbol>'
            if key.isnumeric():
                if len(key) == 10: return'<timestamp>'
                return'<number>'
            return key
        def recurse_params(data, params, parent):
            if isinstance(data, dict):
                for key, value in data.items():
                    key = fix_key(key)
                    if parent != '':
                        param_key = '%s:%s' % (parent, key)
                    else:
                        param_key = key
                    if not param_key in params:
                        params[param_key] = set()
                    params[param_key].add(type(value))
                    recurse_params(value, params, param_key)
        params = {}
        for symbol, symbol_data in self.symbols.items():
            recurse_params(symbol_data, params, '')
        return params
    
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

    def find(self, settings):
        # filters:
        # '>', '<', '=', '*'
        # '*' is exists
        # add '!' in front of each individualto invert
        # add '! ' in front of full collection to invert
        all_symbols = sorted(self.symbols.keys())
        all_df = pd.DataFrame(index=all_symbols)
        for filter in settings['filter']:
            filter_name = '%s_%s_%s' % tuple(filter)
            print(filter_name)
            found_values = self.get_values(filter[0])
            found_values = pd.Series(found_values).dropna()

            # get filter chars and se if we need to totally negate
            filter_chars = filter[1]
            filter_value = filter[2]
            filter_negate = False
            if filter_chars.startswith('! '):
                filter_negate = True
                filter_chars = filter_chars[2:]
            
            # create filter blocks, [negate, char]
            filter_blocks = []
            current_filter_block = [False, '']
            for filter_char in filter_chars:
                if filter_char == '!':
                    current_filter_block[0] = True
                    continue
                current_filter_block[1] = filter_char
                filter_blocks.append(current_filter_block)
                current_filter_block = [False, '']
            
            filter_df = pd.DataFrame(index=all_symbols)
            for filter_block in filter_blocks:
                negate = filter_block[0]
                filter_char = filter_block[1]

                if filter_char == '=':
                    if negate:
                        column_name = '!%s' % filter_char
                        filter_df[column_name] = True
                        filter_df.loc[found_values.index, column_name] = found_values != filter_value
                    else:
                        column_name = filter_char
                        filter_df[column_name] = False
                        filter_df.loc[found_values.index, column_name] = found_values == filter_value
                if filter_char == '>':
                    if negate:
                        column_name = '!%s' % filter_char
                        filter_df[column_name] = True
                        filter_df.loc[found_values.index, column_name] = found_values <= filter_value
                    else:
                        column_name = filter_char
                        filter_df[column_name] = False
                        filter_df.loc[found_values.index, column_name] = found_values > filter_value
                if filter_char == '<':
                    if negate:
                        column_name = '!%s' % filter_char
                        filter_df[column_name] = True
                        filter_df.loc[found_values.index, column_name] = found_values >= filter_value
                    else:
                        column_name = filter_char
                        filter_df[column_name] = False
                        filter_df.loc[found_values.index, column_name] = found_values < filter_value
                if filter_char == '*':
                    if negate:
                        column_name = '!%s' % filter_char
                        filter_df[column_name] = True
                        filter_df.loc[found_values.index, column_name] = False
                    else:
                        column_name = filter_char
                        filter_df[column_name] = False
                        filter_df.loc[found_values.index, column_name] = True
            all_df[filter_name] = filter_df.any(axis=1)
        result = all_df.all(axis=1)
        return list(result[result == True].index)

    # def test_equity(self):
    #     find_settings = {
    #         'filter': [
    #             [['type'] , '=' , 'EQUITY'],
    #             # [['dividend_yield'] , '>' , 10.0],
    #         ],
    #     }
    #     symbols = self.find(find_settings)
    #     pp(len(symbols))
    
    # def test_mutual_fund(self):
    #     find_settings = {
    #         'filter': [
    #             [['type'] , '=' , 'MUTUALFUND'],
    #             [['fund_data', 'fund_overview', 'categoryName'], '=', 'Technology'],
    #             [['expense_ratio'] , '<' , 1.0],
    #         ],
    #     }
    #     symbols = self.find(find_settings)
    #     pp(len(symbols))
    #     for symbol in symbols:
    #         print(symbol, self.symbols[symbol]['expense_ratio'], self.symbols[symbol]['name'])

    # def test_etf(self):
    #     find_settings = {
    #         'filter': [
    #             [['type'] , '=' , 'ETF'],
    #         ],
    #     }
    #     symbols = self.find(find_settings)
    #     pp(len(symbols))

    # def index_fund(self):
    #     find_settings = {
    #         'filter': [
    #             [['type'] , '=' , 'INDEX'],
    #         ],
    #     }
    #     symbols = self.find(find_settings)
    #     pp(len(symbols))


    # def get_types(self, symbol_types, invert=False):
    #     symbols = set()
    #     for symbol, symbol_data in self.symbols.items():
    #         if symbol_data['type'] in symbol_types:
    #             symbols.add(symbol)
    #     if invert:
    #         symbols = set(self.symbols.keys()).difference(symbols)
    #     return sorted(symbols)

    # def types(self):
    #     types = set()
    #     for symbol, symbol_data in self.symbols.items():
    #         types.add(symbol_data['type'])
    #     return sorted(types)

    # def get_sectors_industries(self):
    #     sectors_industries = {}
    #     for symbol, symbol_data in self.symbols.items():
    #         if not symbol_data['sector'] in sectors_industries:
    #             sectors_industries[symbol_data['sector']] = set()
    #         sectors_industries[symbol_data['sector']].add(symbol_data['industry'])
    #     return sectors_industries

    def __make_symbols(self, recache):
        # get symbols
        self.symbols = None
        if not recache:
            self.symbols = storage.load('analysis_symbols')
        if recache or self.symbols == None:
            if self.tickers == None:
                raise Exception('no tickers to initialize')  
            print('fetching symbols data')
            analysis = self.tickers.get_analysis()
            self.symbols = {}
            for symbol, symbol_data in analysis.items():
                # skip non us market symbols
                if '.' in symbol: continue

                # skip some others
                if 'name' in symbol_data:
                    if symbol_data['name'] == None: continue
                else:
                    continue
                if not symbol_data['type'] in self.equity_types: continue
                
                self.symbols[symbol] = symbol_data
            storage.save(self.symbols, 'analysis_symbols')
        
        print(len(self.symbols))

        # get charts
        self.charts = self.tickers.get_chart()
        print(len(self.charts))
        
    # def news_sentiment(self):
    #     start_date = '2023-01-01'
    #     end_date = '2025-01-31'
    #     chart = self.tickers.get_chart(start_date, end_date)
    #     sp_500_growth = self.benchmarks.get_chart(start_date, end_date)['SPY']['adjclose']
    #     sp_500_growth = (sp_500_growth / sp_500_growth.iloc[0]) - 1.0
    #     news_sentiment = self.tickers.get_news_sentiment(start_date, end_date)
    #     test_df = {}
    #     for symbol in self.tickers.get_symbols():
    #         if symbol in chart and symbol in news_sentiment:
    #             symbol_growth = chart[symbol]['adjclose']
    #             symbol_growth = (symbol_growth / symbol_growth.iloc[0]) - 1.0
    #             symbol_growth = symbol_growth - sp_500_growth
    #             ns = news_sentiment[symbol][news_sentiment[symbol].ne('NEUTRAL')]
    #             df = pd.merge(symbol_growth, ns, left_index=True, right_index=True, how='outer')
    #             weekly_groups = df.groupby(pd.Grouper(freq='W'))
    #             df_data = pd.DataFrame()
    #             for name, group in weekly_groups:
    #                 df_data.loc[name, 'adjclose'] = group['adjclose'].dropna().mean()
    #                 value_counts = group['news_sentiment'].value_counts()
    #                 positive = 0
    #                 negative = 0
    #                 if 'POSITIVE' in value_counts:
    #                     positive = group['news_sentiment'].value_counts()['POSITIVE']
    #                 if 'NEGATIVE' in value_counts:
    #                     negative = group['news_sentiment'].value_counts()['NEGATIVE']
    #                 sentiment = positive + negative
    #                 if sentiment > 0:
    #                     sentiment = ((positive / sentiment) * 2.0) - 1.0
    #                 # df_data.loc[name, 'P'] = positive
    #                 # df_data.loc[name, 'N'] = negative
    #                 df_data.loc[name, 'sentiment'] = sentiment
                
    #             test_df[symbol] = df_data
    #     self.viz.plot_timeseries(test_df)

    # def revenue_growth(self):
    #     # all_tickers = self.tickers.get_all()
    #     # self.viz.data_keys_text(all_tickers, rename_set=set(self.tickers.get_symbols()), rename_to='symbol')
        
    #     # all_other = self.vault.get_data(['all_other'])['all_other']
    #     # self.viz.data_keys_text(all_other, file_name='data_other_keys')

    #     revenue = self.tickers.get_revenue_growth()
    #     pp(revenue.keys())


