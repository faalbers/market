from .security import Security
import pandas as pd
import numpy as np
from ..report import Report
from ..tickers import Tickers
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pprint import pp

pd.options.mode.copy_on_write = True

class Portfolio():
    def __init__(self, name, df_transactions):
        self.name = name
        self.transactions = df_transactions[['action', 'shares', 'amount', 'security', 'symbol','price']]

        # greate securities
        self.securities = []
        symbols = self.transactions['symbol'].dropna().unique()
        tickers = Tickers(symbols)
        # tickers.update(['profile', 'chart'])
        profiles = tickers.get_profiles()
        charts = tickers.get_chart()
        for symbol in symbols:
            # get name
            name = None
            if symbol in profiles: name = profiles[symbol]['name']
            
            # get transactions
            transactions = self.transactions
            transactions = self.transactions.loc[self.transactions['symbol'] == symbol]
            transactions = transactions[['action', 'shares', 'amount', 'price']]

            # get chart starting from first transaction day
            chart = pd.DataFrame()
            if symbol in charts:
                chart = charts[symbol].loc[transactions.index[0]:]
            
            security = Security(symbol, name, transactions, chart)
            self.securities.append(security)

            # print(security.symbol, security.name, self.transactions.shape, chart.shape)


    def get_security_symbols(self):
        return sorted(set(self.transactions['symbol'].dropna().to_list()))
    
    # def get_securities(self):
    #     symbols = self.transactions['symbol'].dropna().unique()
    #     tickers = Tickers(symbols)
    #     profiles = tickers.get_profiles()
    #     charts = tickers.get_chart()

    #     securities = []
    #     for symbol in symbols:
    #         # get name
    #         name = None
    #         if symbol in profiles: name = profiles[symbol]['name']
            
    #         # get transactions
    #         transactions = self.transactions
    #         transactions = self.transactions.loc[self.transactions['symbol'] == symbol]
    #         transactions = transactions[['action', 'shares', 'amount', 'price']]

    #         # get chart
    #         chart = pd.DataFrame()
    #         if symbol in charts:
    #             chart = charts[symbol].loc[transactions.index[0]:]
            
    #         security = Security(symbol, name, transactions, chart)
    #         securities.append(security)

    #     return securities

    def add_report(self, report):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # if self.name != 'ETRADE_Trust': return

        # create intro page

        # get current security states
        securities_current = pd.DataFrame(columns=['shares', 'price', 'alloc %','invested', 'value', 'cap. gain', 'cap. gain %', 'name'])
        securities = {}
        for security in self.securities:
            securities[security.symbol] = security
            current = security.get_current()
            current['name'] = security.name
            securities_current.loc[current.name] = current

        # remove the ones with no chart price
        securities_current = securities_current[~securities_current['price'].isna()]
        if securities_current.empty:
            report.addParagraph('%s:  %s' % (self.name, datetime.now().strftime("%Y-%m-%d")), report.getStyle('Heading2'))
            report.addParagraph('No investments to report', report.getStyle('Normal'))
            return

        # get open investments and sorted by invested
        securities_open = securities_current[securities_current['shares'] > 0.001]
        securities_open = securities_open.sort_values('invested', ascending=False)

        #calculate cap. gain %
        securities_open['cap. gain %'] = (securities_open['cap. gain'] / securities_open['invested']) * 100.0

        # calculate allocation
        securities_open['alloc %'] = (securities_open['invested'] / securities_open['invested'].sum()) * 100.0

        # # drop some columns
        # securities_open.drop(['shares', 'price'], axis=1, inplace=True)

        # move index to first column
        securities_open.index.name = 'symbol'
        securities_open.reset_index(inplace=True)

        # drop unneeded columns
        securities_open.drop(['shares', 'price'], axis=1, inplace=True)

        # add totals to open investments
        if not securities_open.empty:
            totals = {'symbol': '', 'alloc %': '', 'invested': '', 'value': '', 'cap. gain': '', 'cap. gain %': '', 'name': 'TOTAL', }
            totals['invested'] = securities_open['invested'].sum()
            totals['value'] = securities_open['value'].sum()
            totals['cap. gain'] = securities_open['cap. gain'].sum()
            totals['cap. gain %'] = (totals['cap. gain'] / totals['invested']) * 100.0
            securities_open.loc[securities_open.shape[0]] = totals
        
        # get closed investments and reset index
        securities_closed = securities_current[securities_current['shares'] <= 0.001]
        securities_closed = securities_closed.sort_values('invested', ascending=False)
        
        # move index to first column
        securities_closed.index.name = 'symbol'
        securities_closed.reset_index(inplace=True)

        # drop some columns
        securities_closed.drop(['shares', 'alloc %', 'price', 'value', 'cap. gain %'], axis=1, inplace=True)

        # add totals to open investments
        if not securities_closed.empty:
            totals = {'symbol': '', 'invested': '', 'cap. gain': '', 'name': 'TOTAL', }
            totals['invested'] = securities_closed['invested'].sum()
            totals['cap. gain'] = securities_closed['cap. gain'].sum()
            securities_closed.loc[securities_closed.shape[0]] = totals
        
        # create intro page report
        report.addParagraph('%s:  %s' % (self.name, today.strftime("%Y-%m-%d")), report.getStyle('Heading2'))

        if not securities_open.empty:
            report.addParagraph('Open Investments (with shares):', report.getStyle('Heading3'))
            report.addTable(securities_open, 2)
            report.addSpace(0.1)
        if not securities_closed.empty:
            report.addParagraph('Closed Investments (no shares):', report.getStyle('Heading3'))
            report.addTable(securities_closed, 2)
        
        report.addPageBreak()

        # get sorted open and closed securities
        securities_open = securities_open['symbol'].to_list()[:-1]
        securities_closed = securities_closed['symbol'].to_list()[:-1]
        securities_all = securities_open + securities_closed

        # add security pages
        # for security in self.securities:
        for symbol in securities_all:
            security = securities[symbol]

            # if security.symbol != 'VZ': continue
            # print()
            # print(symbol, security.name)
            
            # start making history
            history = security.transactions[security.transactions['action'] != 'StkSplit'].copy() # remove stocksplits
            history = history.dropna(subset=['shares']) # drop actions with no shares
            history = history[['shares', 'amount']]
            
            # sum multi dates together
            history = history.groupby(history.index).sum()

            # expand history to all days since first investing
            history = history.reindex(pd.date_range(start=history.index.min(), end=today, freq='D'))
            history['shares'] = history['shares'].fillna(0).cumsum()
            history['amount'] = history['amount'].fillna(0).cumsum()

            # get close date for all dates since first investing
            if security.chart.empty: continue # don't handle if no chart data
            close = security.chart[['close']].loc[history.index.min():].copy()
            close = close.reindex(pd.date_range(start=history.index.min(), end=today, freq='D'))
            close = close.infer_objects(copy=False).ffill()
            close = close.infer_objects(copy=False).bfill()

            # add close price to transaction dates
            history['close'] = close.loc[history.index,'close']

            # # check discrepancy between price bought and price close
            # price_bought = history.iloc[0]['amount'] / history.iloc[0]['shares']
            # price_close = history.iloc[0]['close']
            # discrepancy = abs(price_bought - price_close) / max(price_bought, price_close).round(2)

            # calculate shares value
            history['value'] = history['shares'] * history['close']

            # add price growth and capital gain
            history['price %'] = (history['close'] / history['close'].iloc[0] - 1) * 100
            history['cap. gain'] = history['value'] - history['amount']
            history['cap. gain %'] = (history['cap. gain'] / history['amount']) * 100.0

            # add posted dividends to history
            history['dividend'] = np.nan
            if 'dividend' in security.chart.columns:
                dividend = security.chart['dividend'].loc[history.index.min():].copy().dropna()
                if not dividend.empty:
                    dividend = dividend.reindex(pd.date_range(start=history.index.min(), end=today, freq='D'))
                    history['dividend'] = dividend

            # add received dividends to history
            history['dividend_received'] = np.nan
            dividend_received = security.transactions[security.transactions['action'] == 'Div'].copy()['amount']
            dividend_received = dividend_received.groupby(dividend_received.index).sum()
            if not dividend_received.empty:
                dividend_received = dividend_received.reindex(pd.date_range(start=history.index.min(), end=today, freq='D')).fillna(0)
                history['dividend_received'] = (history['dividend_received'].fillna(0) + dividend_received).replace(0, np.nan)
            dividend_reinvest = security.transactions[security.transactions['action'] == 'ReinvDiv'].copy()['amount']
            dividend_reinvest = dividend_reinvest.groupby(dividend_reinvest.index).sum()
            if not dividend_reinvest.empty:
                dividend_reinvest = dividend_reinvest.reindex(pd.date_range(start=history.index.min(), end=today, freq='D')).fillna(0)
                history['dividend_received'] = (history['dividend_received'].fillna(0) + dividend_reinvest).replace(0, np.nan)
            
            # add to report
            report.addParagraph('%s: %s' % (security.symbol, security.name), report.getStyle('Heading2'))
            
            # plot price %, invested $
            fig, ax1 = plt.subplots(figsize=(8, 2.8))
            ax1.plot(history['price %'], linewidth=1, color='blue')
            ax1.grid(axis='x')
            ax1.axhline(y=0, color='blue', linewidth=1, linestyle='--')
            ax1.set_ylabel('price %', color='blue')
            ax1.tick_params('y', colors='blue')
            ax1.tick_params('x', labelsize=8)
            
            ax2 = ax1.twinx()
            ax2.plot(history['amount'], color='green')
            ax2.set_ylabel('invested $', color='green')
            ax2.tick_params('y', colors='green')
            ax2.set_ylim([0, history['amount'].max()*1.1])
            # ax2.axhline(y=0, color='green', linewidth=1, linestyle='--')

            report.addChartFigure(fig)
            plt.close(fig)

            # plot cap. gain $, cap. gain %
            fig, ax1 = plt.subplots(figsize=(8, 2.8))
            ax1.plot(history['cap. gain'], linewidth=1, color='blue')
            ax1.grid(True)
            ax1.set_ylabel('cap. gain $', color='blue')
            ax1.axhline(y=0, color='blue', linewidth=1, linestyle='--')
            ax1.tick_params('y', colors='blue')
            ax1.tick_params(axis='x', labelsize=8)

            ax2 = ax1.twinx()
            ax2.plot(history['cap. gain %'], linewidth=1, color='green')
            ax2.set_ylabel('cap. gain %', color='green')
            ax2.tick_params('y', colors='green')

            report.addChartFigure(fig)
            plt.close(fig)

            # plot dividend data
            if history['dividend'].notna().any():
                fig, ax1 = plt.subplots(figsize=(8, 2.8))
                # dividend = history['dividend'].infer_objects(copy=False).fillna(0)
                dividend = history['dividend'].infer_objects(copy=False).fillna(0)
                bar_width = dividend.shape[0] / 100.0
                ax1.bar(dividend.index, dividend, width=bar_width, color='red', alpha=0.5,zorder=5)
                ax1.grid(True)
                ax1.set_ylabel('dividend $/share posted', color='red')
                ax1.tick_params('y', colors='red')
                ax1.tick_params(axis='x', labelsize=8)

                if history['dividend_received'].notna().any():
                    dividend_received = history['dividend_received'].infer_objects(copy=False).fillna(0)
                    ax2 = ax1.twinx()
                    ax2.bar(dividend.index, dividend_received, width=bar_width, color='green', alpha=0.5, zorder=10)
                    ax2.set_ylabel('dividend received $', color='green')
                    ax2.tick_params('y', colors='green')

                report.addChartFigure(fig)
                plt.close(fig)

                # if 'dividend_received' in history.columns:
                #     print(history['dividend_received'].dropna())

            report.addPageBreak()

    def add_report_old(self, report):
        securities = self.get_securities()
        for security in securities:
            print(security.symbol)
            security.get_current()
        return
        # # report = Report('test')
        # # add to report
        # report.addParagraph(self.name, report.getStyle('Heading2'))
        # report.addPageBreak()

        # get first date of transactions
        first_date = self.transactions.iloc[0]['date'].date().isoformat()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # get security symbols and timeseries data
        symbols = self.get_security_symbols()
        tickers = Tickers(symbols)
        profiles = tickers.get_profiles()
        charts = tickers.get_chart(first_date)

        # nothing to report if there are no securities
        if len(charts) == 0: return

        # get all ecurities that are not found in charts
        symbols_not_handled = set(symbols).difference(set(charts.keys()))


        # go through all securities that are found in charts
        for symbol, df_chart in charts.items():
            if symbol in ['^IRX']:
                symbols_not_handled.add(symbol)
                continue
            
            # if not symbol in ['USNQX', 'ANET', 'DFCIX']: continue
            # if not symbol in ['VITAX']: continue
            
            # get transactions and seperate stock splits
            df_transactions = self.transactions.loc[self.transactions['symbol'] == symbol]
            df_transactions.set_index('date', inplace=True)
            df_stock_splits = df_transactions.loc[df_transactions['action'] == 'StkSplit']
            df_transactions = df_transactions.loc[df_transactions['action'] != 'StkSplit']
            if not df_stock_splits.empty:
                split_mult = df_stock_splits['shares'].cumprod().iloc[-1]
            else:
                split_mult = 1.0

            # get symbol share transactions and split mult if needed
            df_history = df_transactions[['shares', 'amount', 'price']]
            if split_mult > 1.0: df_history['shares'] = df_history['shares'] * split_mult
            
            # get close date for all dates since first investing
            df_close = df_chart[['close']].loc[df_history.index.min():]
            if df_close['close'].unique().shape[0] == 1:
                symbols_not_handled.add(symbol)
                continue
            df_close = df_close.reindex(pd.date_range(start=df_history.index.min(), end=today, freq='D'))
            df_close = df_close.infer_objects(copy=False).ffill()
            df_close = df_close.infer_objects(copy=False).bfill()

            # add close price to transaction dates
            df_history['close'] = df_close.loc[df_history.index,'close']

            # fix nan amounts with shares * close
            df_history['amount'] = df_history['amount'].fillna(df_history['shares'] * df_history['close'])
            
            # drop unneeded columns from history
            df_history = df_history[['shares', 'amount']]

            # sum multi dates together
            df_history = df_history.groupby(df_history.index).sum()

            # expand history to all days since first investing
            df_history = df_history.reindex(pd.date_range(start=df_history.index.min(), end=today, freq='D'))
            df_history['shares'] = df_history['shares'].fillna(0).cumsum()
            df_history['amount'] = df_history['amount'].fillna(0).cumsum()

            # add close price to history
            df_history['close'] = df_close.loc[df_history.index,'close']

            # check discrepancy between price bought and price close
            price_bought = df_history.iloc[0]['amount'] / df_history.iloc[0]['shares']
            price_close = df_history.iloc[0]['close']
            discrepancy = abs(price_bought - price_close) / max(price_bought, price_close)
            if discrepancy > 0.05:
                # data not feasible
                symbols_not_handled.add(symbol)
                continue

            # calculate shares value
            df_history['value'] = df_history['shares'] * df_history['close']

            print()
            print(symbol, self.name)
            # print(df_history)
            print(price_bought, price_close, discrepancy)

            df_history['price %'] = (df_history['close'] / df_history['close'].iloc[0] - 1) * 100
            df_history['revenue'] = df_history['value'] - df_history['amount']

            # add to report
            report.addParagraph('%s: %s' % (symbol, profiles[symbol]['name']), report.getStyle('Heading2'))

            fig, ax1 = plt.subplots(figsize=(7, 2.8))
            ax1.plot(df_history['price %'], linewidth=1, color='blue')
            ax1.grid(axis='x')
            ax1.axhline(y=0, color='blue', linewidth=1, linestyle='--')
            # ax1.set_xlabel('date')
            ax1.set_ylabel('price %', color='blue')
            ax1.tick_params('y', colors='blue')
            ax1.tick_params('x', labelsize=8)

            ax2 = ax1.twinx()
            ax2.plot(df_history['shares'], color='green')
            ax2.set_ylabel('shares', color='green')
            ax2.tick_params('y', colors='green')
            ax2.set_ylim([0, df_history['shares'].max()*1.1])
            ax2.axhline(y=0, color='green', linewidth=1, linestyle='--')
            # scale = 2
            # ax2.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: x * scale))
            # ax2.grid(True)

            # plt.tight_layout()
            report.addChartFigure(fig)
            plt.close(fig)

            fig, ax1 = plt.subplots(figsize=(7, 2.8))
            ax1.plot(df_history['revenue'], linewidth=1, color='orange')
            ax1.grid(True)
            ax1.set_ylabel('revenue', color='orange')
            ax1.axhline(y=0, color='red', linewidth=0.5, linestyle='--')
            ax1.tick_params(axis='x', labelsize=8)

            # plt.tight_layout()
            report.addChartFigure(fig)
            plt.close(fig)
            
            report.addPageBreak()



        # # report.addPageBreak()
