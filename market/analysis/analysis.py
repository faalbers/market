from ..tickers import Tickers
# from ..viz import Viz
import pandas as pd
from pprint import pp
# from ..vault import Vault
from .gicsm import GICSM
from datetime import datetime

class Analysis():
    @ staticmethod
    def __get_param(symbol_data, keys):
        # recursively go through param keys to find value
        if len(keys) > 0:
            if isinstance(symbol_data, dict):
                if keys[0] in symbol_data and symbol_data[keys[0]] != None:
                    if len(keys) == 1:
                        return symbol_data[keys[0]]
                    else:
                        return Analysis.__get_param(symbol_data[keys[0]], keys[1:])
                else:
                    return None
            else:
                return None

    def __init__(self, tickers):
        self.tickers = tickers
        self.__make_symbols()
        # self.benchmarks = Tickers(['SPY', 'QQQ'])
        # self.viz = Viz()
        # self.vault = Vault()

    def test(self):
        types = set()
        symbols = set()
        for symbol, symbol_data in self.symbols.items():
            types.add(symbol_data['type'])
        pp(types)
        # pp(len(symbols))
        # print(sorted(symbols))

    def test_equity(self):
        find_settings = {
            'filter': [
                [['type'] , '=' , 'equity'],
                # [['dividend_yield'] , '>' , 10.0],
            ],
        }
        symbols = self.find(find_settings)
        pp(len(symbols))
    
    def test_mutual_fund(self):
        find_settings = {
            'filter': [
                [['type'] , '=' , 'mutual fund'],
                # [['expense_ratio'] , '>' , 0.0],
                # [['fund_data', 'fund_overview', 'categoryName'],'=', 'Technology'],
            ],
        }
        symbols = self.find(find_settings)
        pp(len(symbols))

    def test_etf(self):
        find_settings = {
            'filter': [
                [['type'] , '=' , 'etf'],
            ],
        }
        symbols = self.find(find_settings)
        pp(len(symbols))

    def index_fund(self):
        find_settings = {
            'filter': [
                [['type'] , '=' , 'index fund'],
            ],
        }
        symbols = self.find(find_settings)
        pp(len(symbols))

    def find(self, settings):
        symbols = set()
        for symbol, symbol_data in self.symbols.items():
            valid = True
            for filter in settings['filter']:
                value = Analysis.__get_param(symbol_data, filter[0])
                if value != None:
                    filter_valid = False
                    for filter_char in filter[1]:
                        if filter_char == '=':
                            if value == filter[2]:
                                filter_valid = True
                                break
                        elif filter_char == '>':
                            if value > filter[2]:
                                filter_valid = True
                                break
                        elif filter_char == '<':
                            if value < filter[2]:
                                filter_valid = True
                                break
                        else:
                            raise ValueError('Unknown filter char %s' % filter_char)
                    if not filter_valid:
                        valid = False
                        break
                else:
                    valid = False
                    break
            if valid:
                symbols.add(symbol)
        return symbols

    def get_types(self, symbol_types, invert=False):
        symbols = set()
        for symbol, symbol_data in self.symbols.items():
            if symbol_data['type'] in symbol_types:
                symbols.add(symbol)
        if invert:
            symbols = set(self.symbols.keys()).difference(symbols)
        return sorted(symbols)

    def types(self):
        types = set()
        for symbol, symbol_data in self.symbols.items():
            types.add(symbol_data['type'])
        return sorted(types)

    def get_values(self, param_keys, symbols=True):
        values = {}
        for symbol, symbol_data in self.symbols.items():
            value = Analysis.__get_param(symbol_data, param_keys)
            values[symbol] = value
        if symbols:
            return values
        values = [v for s,v in values.items() if v != None]
        return sorted(values)
            
    def get_sectors_industries(self):
        sectors_industries = {}
        for symbol, symbol_data in self.symbols.items():
            if not symbol_data['sector'] in sectors_industries:
                sectors_industries[symbol_data['sector']] = set()
            sectors_industries[symbol_data['sector']].add(symbol_data['industry'])
        return sectors_industries
            
    def __make_symbols(self):
        analysis = self.tickers.get_analysis()
        # # GICS names
        # gicsm = GICSM()
        # gicsm.print_hierarchy()

        test = set()

        symbols = set(self.tickers.get_symbols())
        self.symbols = {}
        for symbol in symbols:
            # skip non us market symbols
            if '.' in symbol: continue
            
            # fet symbols data
            symbol_type = None
            if symbol in analysis:
                # don't handle the ones with no name
                if analysis[symbol]['name'] == None: continue
                # skip non us markets
                if analysis[symbol]['exchange_time_zone_name'] != None and not analysis[symbol]['exchange_time_zone_name'].startswith('America/'):
                    continue

                # handle the ones with a type
                symbol_type = None
                if analysis[symbol]['type'] == 'EQUITY':
                    symbol_type = 'equity'
                elif analysis[symbol]['type'] == 'MUTUALFUND':
                    symbol_type = 'mutual fund'
                elif analysis[symbol]['type'] == 'ETF':
                    symbol_type = 'etf'
                elif analysis[symbol]['type'] == 'INDEX':
                    symbol_type = 'index fund'
                elif analysis[symbol]['type'] == 'MONEYMARKET':
                    symbol_type = 'money market'
                elif analysis[symbol]['type'] == 'ECNQUOTE':
                    symbol_type = 'ecn quote'
                else:
                    # all others are not handled
                    continue
                
                self.symbols[symbol] = {} 
                self.symbols[symbol]['name'] = analysis[symbol]['name']
                self.symbols[symbol]['type'] = symbol_type
                self.symbols[symbol]['exchange'] =  analysis[symbol]['exchange']
                self.symbols[symbol]['exchange_name'] =  analysis[symbol]['exchange_name']
                self.symbols[symbol]['sector'] = analysis[symbol]['sector']
                self.symbols[symbol]['industry'] = analysis[symbol]['industry']
                self.symbols[symbol]['etf_category'] = analysis[symbol]['category']
                self.symbols[symbol]['etf_family'] = analysis[symbol]['fund_family']
                self.symbols[symbol]['earnings_per_share_current_year'] = analysis[symbol]['eps_current_year']
                self.symbols[symbol]['earnings_per_share_forward'] = analysis[symbol]['eps_forward']
                self.symbols[symbol]['earnings_per_share_trailing'] = analysis[symbol]['eps_trailing']
                self.symbols[symbol]['earnings_growth'] = analysis[symbol]['earnings_growth']
                self.symbols[symbol]['earnings_growth_quarterly'] = analysis[symbol]['earnings_growth_quarterly']
                self.symbols[symbol]['revenue_per_share'] = analysis[symbol]['revenue_per_share']
                self.symbols[symbol]['revenue_growth'] = analysis[symbol]['revenue_growth']
                self.symbols[symbol]['price_to_earnings_trailing'] = analysis[symbol]['pe_trailing']
                if isinstance(analysis[symbol]['pe_trailing'], float): # dividend percentage of price 12 m trailing, %
                    self.symbols[symbol]['price_to_earnings_trailing'] = analysis[symbol]['pe_trailing'] * 100.0
                else:
                    self.symbols[symbol]['price_to_earnings_trailing'] = None
                if isinstance(analysis[symbol]['pe_forward'], float): # dividend percentage of price 12 m trailing, %
                    self.symbols[symbol]['price_to_earnings_forward'] = analysis[symbol]['pe_forward'] * 100.0
                else:
                    self.symbols[symbol]['price_to_earnings_forward'] = None
                self.symbols[symbol]['price_to_earnings_to_growth_trailing'] = analysis[symbol]['peg_trailing']
                self.symbols[symbol]['dividend_yield'] = analysis[symbol]['dividend_yield'] # dividend percentage of price per year, %
                if isinstance(analysis[symbol]['dividend_yield_trailing'], float): # dividend percentage of price 12 m trailing, %
                    self.symbols[symbol]['dividend_yield_trailing'] = analysis[symbol]['dividend_yield_trailing'] * 100.0
                else:
                    self.symbols[symbol]['dividend_yield_trailing'] = None
                self.symbols[symbol]['dividend_rate'] = analysis[symbol]['dividend_rate'] # total dividend payed per year, $/sh
                self.symbols[symbol]['dividend_rate_trailing'] = analysis[symbol]['dividend_rate_trailing'] # total dividend payed 12 m trailing, $/sh
                self.symbols[symbol]['dividend_date_record'] = analysis[symbol]['ex_dividend_date']
                if self.symbols[symbol]['dividend_date_record'] != None:
                    self.symbols[symbol]['dividend_date_record'] = datetime.fromtimestamp(self.symbols[symbol]['dividend_date_record'])
                self.symbols[symbol]['dividend_date_execution'] = analysis[symbol]['dividend_date']
                if self.symbols[symbol]['dividend_date_execution'] != None:
                    self.symbols[symbol]['dividend_date_execution'] = datetime.fromtimestamp(self.symbols[symbol]['dividend_date_execution'])
                self.symbols[symbol]['dividend_date_record_last'] = analysis[symbol]['dividend_date_last']
                if self.symbols[symbol]['dividend_date_record_last'] != None:
                    self.symbols[symbol]['dividend_date_record_last'] = datetime.fromtimestamp(self.symbols[symbol]['dividend_date_record_last'])
                self.symbols[symbol]['dividend_last'] = analysis[symbol]['dividend_last']
                self.symbols[symbol]['price'] = analysis[symbol]['price']
                self.symbols[symbol]['book_value_per_share'] = analysis[symbol]['book_value_per_share']
                self.symbols[symbol]['expense_ratio'] = analysis[symbol]['expense_ratio']
                self.symbols[symbol]['fund_data'] = analysis[symbol]['fund_data']
                self.symbols[symbol]['recommendations'] = analysis[symbol]['recommendations']
                self.symbols[symbol]['growth_estimates'] = analysis[symbol]['growth_estimates']
                self.symbols[symbol]['eps_trend'] = analysis[symbol]['eps_trend']
                self.symbols[symbol]['upgrades_downgrades'] = analysis[symbol]['upgrades_downgrades']

        # print(len(self.symbols))
        # print(test)

        
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


