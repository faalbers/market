from ..vault import Vault
import logging
from ..scrape import *
from pprint import pp
import pandas as pd
import numpy as np

class Tickers():
    def __init__(self, symbols=[], types=[]):
        self.logger = logging.getLogger('Market')
        self.vault = Vault()
        self.__make_symbols(symbols, types)

    def __make_symbols(self, symbols=[], types=[] ,update=False, forced=False):
        symbols_data_vault = self.vault.get_data('symbols', key_values=symbols, update=update, forced=forced)
        
        # get scraped symbols
        symbols_data = symbols_data_vault['stocklist'].merge(symbols_data_vault['tickers'],
            how='outer', left_index=True, right_index=True, suffixes=('_stocklist', '_tickers'))

        # fill in missing names and drop name_tickers
        # if 'name' in symbols_data.columns and 'name_tickers' in symbols_data.columns:
        if 'name_tickers' in symbols_data.columns:
            if 'name' in symbols_data.columns:
                symbols_data['name'] = symbols_data['name'].fillna(symbols_data['name_tickers'])
                symbols_data.drop('name_tickers', axis=1, inplace=True)
            else:
                symbols_data.rename(columns={'name_tickers': 'name'}, inplace=True)
        
        # sub_type fixes
        if 'sub_type' in symbols_data.columns:
            if 'type' in symbols_data.columns:
                upper_type = symbols_data['sub_type'].isna() & symbols_data['type'].isin(['etf', 'fund', 'trust'])
                symbols_data.loc[upper_type, 'sub_type'] = symbols_data.loc[upper_type, 'type'].str.upper()
                stock_type = symbols_data['sub_type'].isna() & (symbols_data['type'] == 'stock')
                symbols_data.loc[stock_type, 'sub_type'] = 'CS'
                stocks_type = symbols_data['sub_type'].isna() & (symbols_data['market'] == 'stocks')
                symbols_data.loc[stocks_type, 'sub_type'] = 'CS'
                # we don't need type anymore
                symbols_data.drop(['type'], axis=1, inplace=True)
            symbols_data.drop(['market'], axis=1, inplace=True)

        # now merge info
        if not symbols_data_vault['info'].empty:
            if 'type' in symbols_data.columns: symbols_data.drop(['type'], axis=1, inplace=True)
            symbols_data = symbols_data.merge(symbols_data_vault['info'],
            how='outer', left_index=True, right_index=True)
        
        # fix type column names
        if 'type' in symbols_data.columns:
            # we have type, but it could be from stocklist
            symbols_data['type'] = symbols_data['type'].str.upper()
        elif 'sub_type' in symbols_data.columns:
            # we oonly have sub_type, make it type
            symbols_data.rename(columns={'sub_type': 'type'}, inplace=True)

        # use name of info if present
        if 'name' in symbols_data.columns and 'name_short' in symbols_data.columns:
            has_info_name = symbols_data['name_short'].notna() & \
                ~pd.to_numeric(symbols_data['name_short'], errors='coerce').notna()
            symbols_data.loc[has_info_name, 'name'] = symbols_data.loc[has_info_name, 'name_short']
            symbols_data.drop(['name_short'], axis=1, inplace=True)

        # cleanup types
        if 'type' in symbols_data.columns:
            symbols_data.loc[symbols_data['type'].isna(), 'type'] = 'NONE'
        if 'sub_type' in symbols_data.columns:
            symbols_data.loc[symbols_data['sub_type'].isna(), 'sub_type'] = 'NONE'

        # final cleanup
        symbols_data.sort_index(inplace=True)

        self.__symbols = symbols_data

        # filter types iif needed
        if len(types) > 0:
            self.__symbols = self.get_symbols_info(types)

    def update(self, forced=False):
        updates = []

        # update data
        updates.append(['update_data', [], forced])

        # update symbols data
        symbols_all = self.__symbols.index.to_list()
        if len(symbols_all) > 0:
            updates.append(['update_symbols_all', symbols_all, forced])

        # update info
        symbols_info = self.get_symbols_info(['EQUITY', 'ETF', 'INDEX', 'MUTUALFUND']).index.to_list()
        if len(symbols_info) > 0:
            updates.append(['update_symbols_info', symbols_info, forced])

        # update equity
        symbols_equity = self.get_symbols_info(['EQUITY']).index.to_list()
        if len(symbols_equity) > 0:
            updates.append(['update_symbols_equity', symbols_equity, forced])

        self.vault.update(updates)
    
    def update_old(self, forced=False):
        self.vault.update('update', key_values=self.__symbols.index.to_list(), forced=forced)

    def add_symbols(self, symbols):
        pass

    def get_symbols(self):
        return self.__symbols.index.to_list()
    
    def get_symbols_types(self):
        types_all = set()
        if 'type' in self.__symbols.columns:
            types = self.__symbols['type'].unique()
            # types_all.update(self.__symbols['type'].unique())
            if 'sub_type' in self.__symbols.columns:
                for type_name in types:
                    for sub_type in self.__symbols[self.__symbols['type'] == type_name]['sub_type'].unique():
                        types_all.add('%s_%s' % (type_name, sub_type))

        return sorted(types_all)
    
    def get_symbols_info(self, types=[]):
        if self.__symbols.empty: return self.__symbols
        if len(types) > 0:
            found = pd.Series(dtype='bool', index=self.__symbols.index, data=False)
            for type_code in types:
                splits = type_code.split('_')
                all_types = False
                if splits[0] == '*': all_types = True
                if len(splits) == 1:
                    if all_types:
                        found = pd.Series(dtype='bool', index=self.__symbols.index, data=True)
                    else:
                        found = found | (self.__symbols['type'] == splits[0])
                elif len(splits) == 2:
                    if all_types:
                        found = found | (self.__symbols['sub_type'] == splits[1])
                    else:
                        found = found | (self.__symbols['type'] == splits[0]) & (self.__symbols['sub_type'] == splits[1])
            return self.__symbols[found]
        return self.__symbols
    
    def get_profiles(self, update=False, forced=False):
        data = self.vault.get_data('profile', key_values=self.__symbols.index.to_list(), update=update, forced=forced)
        return data
    
    def get_charts(self, start_date=None, end_date=None, update=False, forced=False):
        data = self.vault.get_data('chart', key_values=self.__symbols.index.to_list(), update=update, forced=forced)['chart']

        if start_date or end_date:
            for symbol in data.keys():
                if start_date:
                    data[symbol] = data[symbol].loc[start_date:]
                if end_date:
                    data[symbol] = data[symbol].loc[:end_date]
        return data

    def get_fundamental(self, update=False, forced=False):
        data = self.vault.get_data('fundamental', key_values=self.__symbols.index.to_list(), update=update, forced=forced)
        return data
    
    def get_news(self, update=False, forced=False):
        data = self.vault.get_data('news', key_values=self.__symbols.index.to_list(), update=update, forced=forced)
        return data
    
    def get_analysis(self, update=False, forced=False):
        data = self.vault.get_data('analysis', key_values=self.__symbols.index.to_list(), update=update, forced=forced)
        return data
    
    # def add_us_market(self, update=False, forced=False):
    #     symbols_data = self.vault.get_data('us_symbols', update=update, forced=forced)

    #     # get us acronyms
    #     acronyms_us = set(symbols_data['mic'][symbols_data['mic']['cc'] == 'US']['acronym'].dropna().unique())
    #     acronyms_not_us = set(symbols_data['mic'][symbols_data['mic']['cc'] != 'US']['acronym'].dropna().unique())
    #     acronyms_us = acronyms_us - acronyms_not_us

    #     # get stocklist symbols with acronym in us
    #     symbols_us = set(symbols_data['stocklist'][symbols_data['stocklist']['acronym'].isin(acronyms_us)].index)

    #     # get tickers that are stocks, otc or indices, rename the indices symbols correctly
    #     symbols_us.update(symbols_data['tickers'][symbols_data['tickers']['market'].isin(['stocks', 'otc'])].index)
    #     symbols_us.update([('^'+x[2:]) for x in symbols_data['tickers'][symbols_data['tickers']['market'] == 'indices'].index])

    #     self.symbols = set(self.symbols)
    #     self.symbols.update(symbols_us)
    #     self.symbols = sorted(self.symbols)
    #     self.count = len(self.symbols)

    # def add_scraped(self):
    #     symbols = set()
    #     symbols.update(YahooF_Info().get_symbols())
    #     symbols.update(YahooF_Chart().get_symbols())
    #     symbols.update(YahooF_Fundamental().get_symbols())
    #     self.symbols = set(self.symbols)
    #     self.symbols.update(symbols)
    #     self.symbols = sorted(self.symbols)
    #     self.count = len(self.symbols)
