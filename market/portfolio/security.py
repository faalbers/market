import pandas as pd
import numpy as np
from ..tickers import Tickers
from datetime import datetime

pd.options.mode.copy_on_write = True

class Security():

    def __init__(self, symbol, name, transactions, chart):
        self.symbol = symbol
        self.name = name
        self.transactions = transactions
        self.chart = chart

        # stransform shares and price on stock splits
        stock_splits = self.transactions.loc[self.transactions['action'] == 'StkSplit']
        for index, row in stock_splits.iterrows():
            split_mult = row['shares']
            last_index = self.transactions.index.get_loc(index)
            temp_transactions = self.transactions.iloc[:last_index].loc[self.transactions['action'] != 'StkSplit']
            multi_indices = temp_transactions.index
            self.transactions.loc[multi_indices, 'shares'] = self.transactions.loc[multi_indices, 'shares'] * split_mult
            self.transactions.loc[multi_indices, 'price'] = self.transactions.loc[multi_indices, 'price'] / split_mult

        # add close to transactions
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        found_close = False
        if not self.chart.empty:
            df_close = self.chart[['close']].loc[self.transactions.index[0]:]
            df_close = df_close.reindex(pd.date_range(start=self.transactions.index[0], end=today, freq='D'))
            df_close = df_close.infer_objects(copy=False).ffill()
            df_close = df_close.infer_objects(copy=False).bfill()
            df_close.loc[self.transactions.index]['close']
            self.transactions['close'] = df_close.loc[self.transactions.index]['close']
            found_close = True
        else:
            self.transactions['close'] = np.nan
        
        # fill in price and amount from close
        if found_close:
            is_nan = self.transactions['amount'].isna()
            if is_nan.any():
                self.transactions.loc[is_nan, 'price'] = self.transactions.loc[is_nan, 'close']
                self.transactions.loc[is_nan, 'amount'] = self.transactions.loc[is_nan, 'price'] *self.transactions.loc[is_nan, 'shares']

    def get_current(self):
        # make a copy because we will manipulate a bit
        transactions = self.transactions.copy()
        transactions['shares_cumsum'] = transactions['shares'].fillna(0).cumsum()
        transactions['amount_cumsum'] = transactions['amount'].fillna(0).cumsum()

        current = {'shares': np.nan, 'invested': np.nan, 'value': np.nan, 'cap. gain': np.nan, 'price': np.nan}
        current['shares'] = transactions['shares_cumsum'].iloc[-1]
        
        if not self.chart.empty: current['price'] = self.chart['close'].iloc[-1]

        current['invested'] = transactions['amount_cumsum'].iloc[-1]
        
        if not self.chart.empty:
            current['value'] = current['shares'] * current['price']
            current['cap. gain'] = current['value'] - current['invested']
        current = pd.Series(current, name=self.symbol)

        # print()
        # print(transactions)
        # print(current)

        return current
    