import glob, datetime, time, os
from .statement import *
from pprint import pp
import pandas as pd
import numpy as np
from ..utils import *
from ..tickers import Tickers
from ..report import Report
import matplotlib.pyplot as plt
import yfinance as yf

class Portfolio():
    make_docs = True
    
    def __init__(self):
        # pd.set_option('display.max_rows', None)
        # pd.set_option('display.max_columns', None)
        if False:
            self.__make_accounts()
            storage.save(self.accounts, 'statement_accounts')
        else:
            self.accounts = storage.load('statement_accounts')   

    def make_reports(self):
        # gather holdings profile and charts data
        symbols = set()
        chart_start_date = datetime.datetime.now()
        chart_end_date = None
        for account_number, account_data in self.accounts.items():
            symbols.update(account_data['holdings'].keys())
            if account_data['start_date'] < chart_start_date:
                chart_start_date = account_data['start_date']
            if chart_end_date == None:
                chart_end_date = account_data['end_date']
            elif account_data['end_date'] > chart_end_date:
                chart_end_date = account_data['end_date']
        
        # get profiles
        tickers = Tickers(symbols)
        # tickers.update(['update'])
        profiles = tickers.get_profiles()
        
        # get charts
        if False:
            self.charts = {}
            for symbol in symbols:
                print('getting chart for %s' % symbol)
                self.charts[symbol] = self.__get_chart(symbol, chart_start_date, chart_end_date)
            storage.save(self.charts, 'statement_charts')
        else:
            self.charts = storage.load('statement_charts')

        # add Close Splits
        for symbol, chart in self.charts.items():
            if isinstance(chart, type(None)): continue
            splits = chart['Stock Splits'] != 0.0
            chart['Close Splits'] = np.nan
            chart.loc[splits,'Close Splits'] = chart.loc[splits,'Stock Splits']
            chart['Close Splits'] = chart['Close Splits'].fillna(1.0)
            chart['Close Splits'] = (chart['Close Splits'].iloc[::-1].cumprod().iloc[::-1]).shift(-1).ffill()
            chart['Close Splits'] = chart['Close'] * chart['Close Splits']
        # {'Open', 'Adj Close', 'Dividends', 'Stock Splits', 'Volume', 'High', 'Close', 'Capital Gains', 'Low'}
        
        # create account reports data
        self.test = set()
        account_reports = {}
        transaction_types = set()
        for account_number, account_data in self.accounts.items():
            # print(account_number)
            # if account_number != '239-766268': continue
            holdings_reports = account_reports[account_number] = {
                'broker': account_data['broker'],
                'start_date': account_data['start_date'],
                'end_date': account_data['end_date'],
                'statements': account_data['statements'],
                'holdings': {}
            }
            for symbol, symbol_data in account_data['holdings'].items():
                is_cusip = len(symbol) == 9

                # get symbol transactions in account
                if isinstance(symbol_data['transactions'], type(None)): continue
                transactions = symbol_data['transactions'].copy()
                transaction_types.update(transactions['type'].unique())

                report_data = holdings_reports['holdings'][symbol] = {
                    'name': None,
                    'type': None,
                    'info': None,
                    'total_cost': 0.0,
                    'total_profit': 0.0,
                    'tables': [],
                    'graphs_1': [],
                    'graphs_2': [],
                }
                if symbol in profiles:
                    report_data['name'] = profiles[symbol]['name']
                    report_data['info'] = profiles[symbol]['info']
                    if report_data['name'] == None:
                        report_data['name'] = symbol_data['name']
                else:
                    report_data['name'] = symbol_data['name']

                # TODO delete later, only needed during development
                transactions_info = {
                    'account_number': account_number,
                    'broker': account_data['broker'],
                    'statements': sorted(symbol_data['statements']),
                    'symbol': symbol,
                    'name':symbol_data['name'],
                }
                # handle per type of holding
                if symbol == 'QPUBQ': self.make_report_dsp(transactions, transactions_info, report_data)
                elif is_cusip:
                    if symbol_data['name'].startswith('UNITED STATES'): self.make_report_t_bill(transactions, transactions_info, report_data)
                    elif symbol_data['name'] == 'NH PORTFOLIO 2024 (FIDELITY FUNDS)': self.make_report_nh(transactions, transactions_info, report_data)
                    else:
                        pass
                        # TODO figure out what to do with these
                        # print(symbol_data['name'])
                        # print(transactions)
                elif symbol.endswith('XX'): self.make_report_mm(transactions, transactions_info, report_data)
                elif symbol.endswith('X'): self.make_report_mf(transactions, transactions_info, report_data)
                elif len(symbol) <= 5: self.make_report_stock(transactions, transactions_info, report_data)
                else:
                    pass
                    # TODO figure out what to do with these
                    # print(symbol_data['name'])
                    # print(transactions)
        # pp(transaction_types)
        pp(self.test)

        # make docs
        if not self.make_docs: return
        for account_number, account_data in account_reports.items():
            # report_name = '%s_%s_%s_%s' % (account_number, account_data['broker'], account_data['start_date'].strftime('%Y_%m_%d'), account_data['end_date'].strftime('%Y_%m_%d'))
            report_name = '%s_%s_%s' % (account_data['end_date'].strftime('%Y_%m_%d'), account_number, sorted(account_data['broker'])[0])
            r = Report(report_name)
            r.addParagraph('%s (%s) (%s - %s)' % (
                account_number,
                sorted(account_data['broker'])[0],
                account_data['start_date'].strftime('%Y/%m/%d'),
                account_data['end_date'].strftime('%Y/%m/%d')), r.getStyle('Heading1'))

            # create holdings tables
            r.addParagraph('Holdings', r.getStyle('Heading2'))
            holdings = sorted(account_data['holdings'])
            rows = []
            for symbol in holdings:
                symbol_data = account_data['holdings'][symbol]
                row_data = {'symbol': symbol,
                    'name': symbol_data['name'],
                    'type': symbol_data['type'],
                }
                rows.append(row_data)
            holdings_table = pd.DataFrame(rows)
            r.addTable(holdings_table)

            # create statements
            r.addParagraph('Statements', r.getStyle('Heading2'))
            for statement in account_data['statements']:
                full_path = os.path.abspath(statement['statement'])
                full_path = full_path.replace('\\', '/')
                base_name = os.path.basename(statement['statement'])
                html_link = '<a href="%s"><font color="blue">%s</font></a>' % (full_path, base_name)
                statement_text = '<p>%s to %s: %s</p>' % (statement['start_date'].date(),statement['end_date'].date(), html_link)
                r.addParagraph(statement_text)
            
            r.addPageBreak()

            for symbol in holdings:
                symbol_data = account_data['holdings'][symbol]
                r.addParagraph('%s (%s) (%s)' % (symbol_data['name'], symbol, symbol_data['type']), r.getStyle('Heading2'))
                if symbol_data['info'] != None: r.addParagraph(symbol_data['info'])

                # if 'quantity_fig' in symbol_data:
                #     r.addChartFigure(symbol_data['quantity_fig'])
                for table in symbol_data['tables']:
                    r.addTable(table, round=2)
                for graph in symbol_data['graphs_1']:
                    r.addParagraph(graph['title']+':', r.getStyle('Heading3'))
                    r.addChartFigure(graph['fig'])
                if len(symbol_data['graphs_2']) > 0:
                    r.addPageBreak()
                for graph in symbol_data['graphs_2']:
                    r.addParagraph(graph['title']+':', r.getStyle('Heading3'))
                    r.addChartFigure(graph['fig'])
                r.addPageBreak()

            r.buildDoc()

    def handle_transactions_viz(self, transactions_viz, info):
        # add close to dates
        chart = None
        if not isinstance(self.charts[info['symbol']], type(None)):
            date_range = pd.date_range(transactions_viz.index[0], transactions_viz.index[-1])
            chart = pd.DataFrame(index=date_range)
            chart = chart.join(self.charts[info['symbol']]['Close Splits']).ffill().bfill()
            transactions_viz['close'] = chart.loc[transactions_viz.index]
        else:
            transactions_viz['close'] = np.nan

        # omit types
        is_omit = ['name change', 'adjustment']
        is_omit = transactions_viz['type'].isin(is_omit)
        transactions_viz = transactions_viz[~is_omit].copy()

        # calculate amount if nan or zero. If nan and price or close available, amount is negative from quantity
        is_calc_amount = [
            'account transfer', 'transfer of assets', 'ira intrl trnsfr out', 'r&d', 'receive securities', 'deliver securities', 'ira intrl trnsfr in',
            'sale', 'sold', 'you sold', 'conversion', 'ira distribution', 
            'bought', 'you bought', 
            'reinvestment', 'div reinvestment', 'dividend reinvestment', 'reinvest', 
            'journal', 
            'stock spin-off', 
        ]
        is_calc_amount = transactions_viz['type'].isin(is_calc_amount)
        is_zero = transactions_viz['amount'] == 0.0
        is_nan = transactions_viz['amount'].isna()
        is_calc_amount = is_calc_amount & (is_nan | is_zero)
        is_price = transactions_viz['price'].notna()
        is_calc_amount_price = is_calc_amount & is_price
        is_calc_amount_close = is_calc_amount & ~is_price
        is_close = transactions_viz['close'].notna()
        is_calc_amount_close = is_calc_amount_close & is_close
        if is_calc_amount_price.any():
            transactions_viz.loc[is_calc_amount_price, 'amount'] = \
                -(transactions_viz.loc[is_calc_amount_price, 'quantity'] * transactions_viz.loc[is_calc_amount_price, 'price'])

        if is_calc_amount_close.any():
            transactions_viz.loc[is_calc_amount_close, 'amount'] = \
                -(transactions_viz.loc[is_calc_amount_close, 'quantity'] * transactions_viz.loc[is_calc_amount_close, 'close'])
        
        # get cost
        # if symbol is not 'DIS', add amount of 'transfer into account',
        is_cost = [
            'r&d', 'transfer of assets', 'receive securities', 'ira intrl trnsfr in',
            'you bought', 'bought', 
            'stock spin-off', 'journal',
        ]
        if info['symbol'] != 'DIS':
            is_cost.append('transfer into account')
        is_cost = transactions_viz['type'].isin(is_cost)
        is_negative = transactions_viz['amount'] < 0.0
        is_cost = is_cost & is_negative
        transactions_viz['cost'] = 0.0
        transactions_viz.loc[is_cost, 'cost'] = \
            -(transactions_viz.loc[is_cost, 'amount']  + transactions_viz.loc[is_cost, 'transaction_cost'].fillna(0.0))
        
        # get revenue
        # if symbol is not 'DIS', add amount of 'transfer out of account',
        # if amount is positive, add as revenue
        # 'merger' was not amount fixed above,only add if positive valid value
        is_revenue = [
            'account transfer', 'ira intrl trnsfr out', 'deliver securities', 'ira distribution', 
            'sale', 'sold', 'you sold', 'conversion', 
            'cash-in-lieu', 'cash in lieu', 'return of capital', 'journal', 'merger',
        ]
        if info['symbol'] != 'DIS':
            is_revenue.append('transfer out of account')
        is_revenue = transactions_viz['type'].isin(is_revenue)
        is_positive = transactions_viz['amount'] > 0.0
        is_revenue = is_revenue & is_positive
        transactions_viz['revenue'] = 0.0
        transactions_viz.loc[is_revenue, 'revenue'] = transactions_viz.loc[is_revenue, 'amount']

        # get capital gains
        is_capital_gains = [
            'long-term cap gain', 'long term cap gain', 'long term cap', 'lt cap gain distribution',
            'short-term cap gain', 'st capital gain', 'st cap gain distribution',
            'capital gain',
        ]
        is_capital_gains = transactions_viz['type'].isin(is_capital_gains)
        transactions_viz['capital_gains'] = 0.0
        transactions_viz.loc[is_capital_gains, 'capital_gains'] = transactions_viz.loc[is_capital_gains, 'amount']
        
        # get dividends
        is_dividends = [
            'dividend', 'dividend received', 'qualified dividend', 'taxable dividend',
        ]
        is_dividends = transactions_viz['type'].isin(is_dividends)
        transactions_viz['dividends'] = 0.0
        transactions_viz.loc[is_dividends, 'dividends'] = transactions_viz.loc[is_dividends, 'amount']
        
        # get reinvestments
        is_reinvestments = [
            'reinvestment', 'div reinvestment', 'dividend reinvestment', 'reinvest',
        ]
        is_reinvestments = transactions_viz['type'].isin(is_reinvestments)
        transactions_viz['reinvestments'] = 0.0
        transactions_viz.loc[is_reinvestments, 'reinvestments'] = -transactions_viz.loc[is_reinvestments, 'amount']
        
        # handle cumulatives
        cumulative_columns = [
            'type',
            'quantity', 'quantity_total', 'cost', 'cost_total', 'revenue', 'close',
            'capital_gains', 'dividends', 'reinvestments'
        ]
        cumulatives = transactions_viz[cumulative_columns].copy()

        # get totals
        is_totals = cumulatives['type'] == 'totals'

        # fix quantity with quantity_total
        if transactions_viz['quantity_total'].notnull().any():
            cumulatives['quantity_sum'] = cumulatives['quantity'].fillna(0.0).cumsum()
            # fix first quantity on totals and redo quantity_sum
            first_total = (is_totals.cumsum() == 1) & is_totals
            cumulatives.loc[first_total, 'quantity'] = \
                cumulatives.loc[first_total, 'quantity_total'] - cumulatives.loc[first_total, 'quantity_sum']
            cumulatives.loc[first_total, 'cost'] = \
                cumulatives.loc[first_total, 'quantity'] * cumulatives.loc[first_total, 'close'].fillna(0.0)
            
            cumulatives = cumulatives.drop('quantity_sum', axis=1)
        cumulatives = cumulatives.drop(['quantity_total', 'close'], axis=1)

        # fix cost with cost_total
        if transactions_viz['cost_total'].notnull().any():
            cumulatives['cost_sum'] = cumulatives['cost'].cumsum()
            # fix first quantity on totals and redo quantity_sum
            first_total = (is_totals.cumsum() == 1) & is_totals
            cumulatives.loc[first_total, 'cost'] = \
                cumulatives.loc[first_total, 'cost_total'] - cumulatives.loc[first_total, 'cost_sum']
            cumulatives = cumulatives.drop('cost_sum', axis=1)
        cumulatives = cumulatives.drop('cost_total', axis=1)

        # create returns
        cumulatives['returns'] = cumulatives['capital_gains'] + cumulatives['dividends']
        cumulatives = cumulatives.drop(['capital_gains', 'dividends'], axis=1)

        # clean up cumulatives , group sum date indices and cumsum them
        cumulatives = cumulatives.drop('type', axis=1)
        cumulatives['quantity'] = cumulatives['quantity'].fillna(0.0)
        cumulatives = cumulatives.groupby(level=0).sum()
        cumulatives = cumulatives.cumsum()

        # finally we add total gain
        cumulatives['total_gain'] = cumulatives['revenue'] + cumulatives['returns'] \
            - cumulatives['cost'] - cumulatives['reinvestments']
        cumulatives = cumulatives.drop('reinvestments', axis=1)

        # handle actions
        actions = transactions_viz[['capital_gains', 'dividends', 'reinvestments']].copy()
        actions = actions.groupby(level=0).sum()

        return (cumulatives, actions)

    def make_report_t_bill(self, transactions, info, report_data):
        # United States Treasury Bill
        report_data['type'] = 'us treasury bill'
        # return

        transactions_viz = transactions.copy()

        # fix the bought ones. Price was in 100.00 instead of 1.00
        is_bought = (transactions_viz['type'] == 'bought') & (transactions_viz['price'] > 1.0)
        transactions_viz.loc[is_bought, 'price'] = transactions_viz.loc[is_bought, 'price'] / 100.0
        transactions_viz.loc[is_bought, 'amount'] = -(transactions_viz.loc[is_bought, 'quantity'] * transactions_viz.loc[is_bought, 'price'])

        # fix conversion types
        is_conversion = transactions_viz['type'] == 'conversion'
        transactions_viz.loc[is_conversion, 'amount'] = -transactions_viz.loc[is_conversion, 'quantity']
    
        # find cost, redeem and gain
        cost_types = ['transferred from', 'transfer into account', 'you bought', 'bought']
        cost_types = transactions_viz['type'].isin(cost_types)
        redeem_types = ['redeemed', 'redemption', 'transferred to', 'conversion']
        redeem_types = transactions_viz['type'].isin(redeem_types)

        cost = -(transactions_viz[cost_types]['amount'].iloc[0])
        redeem = transactions_viz[redeem_types]['amount'].iloc[0]
        gain = redeem - cost
        table = pd.DataFrame([ { 'cost': cost, 'redeem': redeem, 'gain': gain, } ])
        report_data['tables'].append(table)
    
    def make_report_nh(self, transactions, info, report_data):
        # 529 College Investing Plan
        report_data['type'] = '529'
        # self.test.update(transactions['type'].unique())
        pass

    def make_report_mm(self, transactions, info, report_data):
        # Money Market Fund
        report_data['type'] = 'money market fund'
        # self.test.update(transactions['type'].unique())
        pass

    def make_report_mf(self, transactions, info, report_data):
        # Mutual Fund
        report_data['type'] = 'mutual fund'

        self.make_report_equity(transactions, info, report_data)

    def make_report_equity(self, transactions, info, report_data):
        # do_a = info['account_number'] == '20960513' and info['symbol'] == 'RYBHX'
        do_a = info['symbol'] == 'RYBHX'
        # do_a = info['account_number'] == '354-526486-204'
        # if not do_a: return

        # create vizualization dataframe
        transactions_viz = transactions.copy()
        cumulatives, actions = self.handle_transactions_viz(transactions_viz, info)
        
        # make docs
        if not self.make_docs: return

        # create date range
        date_range = pd.date_range(cumulatives.index[0], cumulatives.index[-1])
        # date_range = pd.date_range('2024-11-01', '2024-12-30')
        transactions_viz_all = pd.DataFrame(index=date_range)

        # add cumulatives
        transactions_viz_all = transactions_viz_all.join(cumulatives).ffill().bfill()

        # add actions
        transactions_viz_all = transactions_viz_all.join(actions).fillna(0)

        # add chart data
        if not isinstance(self.charts[info['symbol']], type(None)):
            transactions_viz_all = transactions_viz_all.join(self.charts[info['symbol']]['Close Splits']).ffill().bfill()
            if 'Dividends' in self.charts[info['symbol']]:
                transactions_viz_all = transactions_viz_all.join(self.charts[info['symbol']]['Dividends']).fillna(0.0)
                transactions_viz_all['Dividends'] = transactions_viz_all['Dividends'] * transactions_viz_all['quantity'].shift(1)
            if 'Capital Gains' in self.charts[info['symbol']]:
                transactions_viz_all = transactions_viz_all.join(self.charts[info['symbol']]['Capital Gains']).fillna(0.0)
                transactions_viz_all['Capital Gains'] = transactions_viz_all['Capital Gains'] * transactions_viz_all['quantity'].shift(1)
        else:
            transactions_viz_all['Close Splits'] = np.nan
            transactions_viz_all['Dividends'] = np.nan
            transactions_viz_all['Capital Gains'] = np.nan
        
        # add value
        transactions_viz_all['value'] = transactions_viz_all['quantity'] * transactions_viz_all['Close Splits']

        # add value to 'total_gain'
        transactions_viz_all['total_gain'] = transactions_viz_all['total_gain'] + transactions_viz_all['value']

        # make 'total_cost'
        transactions_viz_all['total_cost'] = transactions_viz_all['cost'] - transactions_viz_all['revenue']

        graph = { 'title': '<font color="green">Cost</font> / <font color="blue">Value</font>' }
        fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.6))
        ax1.plot(transactions_viz_all['total_cost'], color='green')
        ax1.plot(transactions_viz_all['value'], color='blue')
        ax1.set_ylabel('$ amount')
        ax1.tick_params('x', labelsize=6)
        ax1.tick_params('y', colors='black')
        ax1.grid(True)
        graph['fig'] = fig
        plt.close(fig)
        report_data['graphs_1'].append(graph)

        if (transactions_viz_all['returns'] > 0.0).any():
            graph = { 'title': '<font color="blue">Returns (Dividends + Capital Gains)</font>' }
            fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.6))
            ax1.plot(transactions_viz_all['returns'], color='blue')
            ax1.set_ylabel('$ amount')
            ax1.tick_params('x', labelsize=6)
            ax1.tick_params('y', colors='black')
            ax1.grid(True)
            ax1.axhline(y=0.0, color='green', linestyle='--')
            graph['fig'] = fig
            plt.close(fig)
            report_data['graphs_1'].append(graph)

        graph = { 'title': '<font color="blue">Total Gain</font>' }
        fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.6))
        ax1.plot(transactions_viz_all['total_gain'], color='blue')
        ax1.set_ylabel('$ amount')
        ax1.tick_params('x', labelsize=6)
        ax1.tick_params('y', colors='black')
        ax1.grid(True)
        ax1.axhline(y=0.0, color='green', linestyle='--')
        graph['fig'] = fig
        plt.close(fig)
        report_data['graphs_1'].append(graph)

        if (transactions_viz_all['dividends'] > 0.0).any():
            graph = { 'title': '<font color="green">Reported Dividends</font> / <font color="blue">Received Dividents</font>' }
            fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.8))
            bar_width = transactions_viz_all.shape[0] / 75.0
            ax1.bar(transactions_viz_all.index, transactions_viz_all['Dividends'], color='green', alpha=0.5, width=bar_width)
            ax1.bar(transactions_viz_all.index, transactions_viz_all['dividends'], color='blue', alpha=0.5, align='edge', width=bar_width)
            ax1.set_ylabel('$ amount')
            ax1.tick_params('x', labelsize=6)
            ax1.tick_params('y', colors='black')
            ax1.grid(True)
            graph['fig'] = fig
            plt.close(fig)
            report_data['graphs_2'].append(graph)
        
        if (transactions_viz_all['capital_gains'] > 0.0).any():
            graph = { 'title': '<font color="green">Reported Capital Gains</font> / <font color="blue">Received Capital Gains</font>' }
            fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.8))
            bar_width = transactions_viz_all.shape[0] / 75.0
            ax1.bar(transactions_viz_all.index, transactions_viz_all['Capital Gains'], color='green', alpha=0.5, width=bar_width)
            ax1.bar(transactions_viz_all.index, transactions_viz_all['capital_gains'], color='blue', alpha=0.5, align='edge', width=bar_width)
            ax1.set_ylabel('$ amount')
            ax1.tick_params('x', labelsize=6)
            ax1.tick_params('y', colors='black')
            ax1.grid(True)
            graph['fig'] = fig
            plt.close(fig)
            report_data['graphs_2'].append(graph)

        if (transactions_viz_all['reinvestments'] > 0.0).any():
            graph = { 'title': '<font color="blue">Reinvested</font>' }
            fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.8))
            bar_width = transactions_viz_all.shape[0] / 75.0
            ax1.bar(transactions_viz_all.index, transactions_viz_all['reinvestments'], color='blue', align='edge', width=bar_width)
            ax1.set_ylabel('$ amount')
            ax1.tick_params('x', labelsize=6)
            ax1.tick_params('y', colors='black')
            ax1.grid(True)
            graph['fig'] = fig
            plt.close(fig)
            report_data['graphs_2'].append(graph)

    def make_report_dsp(self, transactions, info, report_data):
        # FDIC-insured Deposit Sweep Program core position
        report_data['type'] = 'deposit sweep program'
        # self.test.update(transactions['type'].unique())
        pass
    
    def make_report_stock(self, transactions, info, report_data):
        # Stock
        report_data['type'] = 'stock'
        
        self.make_report_equity(transactions, info, report_data)

        return
        do_a = info['account_number'] == '20964911' and info['symbol'] == 'AIRN'
        # do_a = info['symbol'] == 'SOLV'
        # do_a = info['account_number'] == '20964911'
        # do_a = 'Scottrade' in info['broker']
        # do_a = info['account_number'].startswith('XX')
        # do_b = info['account_number'] == '230-317600' and info['symbol'] == 'VBK'
        # if not (do_a or do_b): return
        # if not do_a: return

        # create vizualization dataframe
        transactions_viz = transactions.copy()

        cumulatives, actions = self.handle_transactions_viz(transactions_viz, info)
        
        # make docs
        if not self.make_docs: return

        # create date range
        date_range = pd.date_range(cumulatives.index[0], cumulatives.index[-1])
        # date_range = pd.date_range('2024-11-01', '2024-12-30')
        transactions_viz_all = pd.DataFrame(index=date_range)

        # add cumulatives
        transactions_viz_all = transactions_viz_all.join(cumulatives).ffill().bfill()

        # add actions
        transactions_viz_all = transactions_viz_all.join(actions).fillna(0)

        # add chart data
        if not isinstance(self.charts[info['symbol']], type(None)):
            transactions_viz_all = transactions_viz_all.join(self.charts[info['symbol']]['Close Splits']).ffill().bfill()
            transactions_viz_all = transactions_viz_all.join(self.charts[info['symbol']]['Dividends']).fillna(0.0)
            transactions_viz_all['Dividends'] = transactions_viz_all['Dividends'] * transactions_viz_all['quantity'].shift(1)
        else:
            transactions_viz_all['Close Splits'] = np.nan
            transactions_viz_all['Dividends'] = np.nan
        
        # add value
        transactions_viz_all['value'] = transactions_viz_all['quantity'] * transactions_viz_all['Close Splits']

        # add value to 'total_gain'
        transactions_viz_all['total_gain'] = transactions_viz_all['total_gain'] + transactions_viz_all['value']

        graph = { 'title': '<font color="green">Cost</font> / <font color="blue">Value</font>' }
        fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.8))
        ax1.plot(transactions_viz_all['cost'], color='green')
        ax1.plot(transactions_viz_all['value'], color='blue')
        ax1.set_ylabel('$ amount')
        ax1.tick_params('x', labelsize=6)
        ax1.tick_params('y', colors='black')
        ax1.grid(True)
        graph['fig'] = fig
        plt.close(fig)
        report_data['graphs_1'].append(graph)

        graph = { 'title': '<font color="blue">Total Gain ( including value and return )</font>' }
        fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.8))
        ax1.plot(transactions_viz_all['total_gain'], color='blue')
        ax1.set_ylabel('$ amount')
        ax1.tick_params('x', labelsize=6)
        ax1.tick_params('y', colors='black')
        ax1.grid(True)
        ax1.axhline(y=0.0, color='green', linestyle='--')
        graph['fig'] = fig
        plt.close(fig)
        report_data['graphs_1'].append(graph)

        if (transactions_viz_all['dividends'] > 0.0).any():
            graph = { 'title': '<font color="green">Reported Dividends</font> / <font color="blue">Received Dividents</font>' }
            fig, ax1 = plt.subplots(dpi=300, figsize=(7, 2.8))
            bar_width = transactions_viz_all.shape[0] / 75.0
            ax1.bar(transactions_viz_all.index, transactions_viz_all['Dividends'], color='green', alpha=0.5, width=bar_width)
            ax1.bar(transactions_viz_all.index, transactions_viz_all['dividends'], color='blue', alpha=0.5, align='edge', width=bar_width)
            ax1.set_ylabel('$ amount')
            ax1.tick_params('x', labelsize=6)
            ax1.tick_params('y', colors='black')
            ax1.grid(True)
            graph['fig'] = fig
            plt.close(fig)
            report_data['graphs_2'].append(graph)


    def __get_chart(self, symbol, chart_start_date, chart_end_date):
        while True:
            try:
                ticker = yf.Ticker(symbol)
                chart = ticker.history(start=chart_start_date.strftime("%Y-%m-%d"), end=chart_end_date.strftime("%Y-%m-%d"),auto_adjust=False)
            except Exception as e:
                if str(e) == 'Too Many Requests. Rate limited. Try after a while.':
                    print('Rate Limeit: wait 60 seconds')
                    time.sleep(60)
                    continue
                else:
                    return None
            if chart.shape[0] == 0:
                return None
            chart.index = chart.index.tz_localize(None)
            return chart

    def __make_accounts(self):
        # parset statements
        self.__parse_statements()
        
        # gather all securities and their symbol and cusip
        securities = {}
        for broker_name, broker_data in self.statement_accounts.items():
            for account_number, account_data_list in broker_data.items():
                for account_data in account_data_list:
                    for security, security_data in account_data['holdings'].items():
                        if not security in securities:
                            securities[security] = {'symbol': set(), 'cusip': set()}
                        if security_data['symbol'] != None: securities[security]['symbol'].add(security_data['symbol'])
                        if security_data['cusip'] != None: securities[security]['cusip'].add(security_data['cusip'])

        # fill in symbol or cusip for securities without one
        for security, security_data in securities.items():
            if (len(security_data['symbol']) + len(security_data['cusip'])) == 0:
                for security_match, security_match_data in securities.items():
                    if security_match in security:
                        if len(security_match_data['symbol']) > 0:
                            security_data['symbol'] = security_match_data['symbol']
                            break
                        elif len(security_match_data['cusip']) > 0:
                            security_data['cusip'] = list(security_match_data['cusip'])[0]
                            break

        # create a symbols list with shortest security name
        symbols = {}
        for security, security_data in securities.items():
            found_symbols = set()
            if len(security_data['symbol']) > 0:
                found_symbols = security_data['symbol']
            elif len(security_data['cusip']) > 0:
                found_symbols = security_data['cusip']
            if len(found_symbols) > 0:
                for symbol in found_symbols:
                    if not symbol in symbols:
                        symbols[symbol] = security
                    else:
                        if len(security) < len(symbols[symbol]):
                            symbols[symbol] = security

        self.accounts = {}
        for broker_name, broker_data in self.statement_accounts.items():
            for account_number, statements in broker_data.items():
                # join account number names
                if account_number == 'XXXX-2261': account_number = '6304-2261'
                elif account_number == 'XXXX-7273': account_number = '3558-7273'
                elif account_number == '156-109380-518': account_number = '814-109380-296'
                
                # create account if needed
                if not account_number in self.accounts:
                    self.accounts[account_number] = {'broker': set(), 'holdings': {}, 'statements': []}
                
                # we add multiple broker names because there can be different versions of same broker statements
                self.accounts[account_number]['broker'].add(broker_name)
                
                # create a dated statements dictionary with end date keys
                dated_statements = {}
                for statement in statements:
                    dated_statements[statement['end_date']] = statement
                

                last_end_date = None
                # sort the end dates and fill in the start and end dates for this account
                sorted_dated_statements = sorted(dated_statements)
                self.accounts[account_number]['start_date'] = dated_statements[sorted_dated_statements[0]]['start_date']
                self.accounts[account_number]['end_date'] = dated_statements[sorted_dated_statements[-1]]['end_date']

                # go through sorted statements and get transactions
                last_end_date = None
                for end_date in sorted_dated_statements:
                    statement = dated_statements[end_date]

                    # add statement info to account
                    self.accounts[account_number]['statements'].append(
                        {'start_date': statement['start_date'], 'end_date': statement['end_date'], 'statement': statement['statement']}
                    )

                    date_gap = True
                    if last_end_date != None and (statement['start_date'] - last_end_date) == datetime.timedelta(days=1):
                        date_gap = False
                    last_end_date = end_date

                    # go through each security in each statement
                    for security, security_data in statement['holdings'].items():
                        # TODO re check moneymarket, does not make any sense
                        # skip the ones with None quantity (money market I can't get ammount or value from)
                        
                        # if 'quantity' in security_data and security_data['quantity'] == None: continue
                        
                        # find symbol or cusip for security
                        symbol = security_data['symbol']
                        if symbol == None:
                            if security in securities:
                                if len(securities[security]['symbol']) > 0:
                                    symbol = list(securities[security]['symbol'])[0]
                                elif len(securities[security]['cusip']) > 0:
                                    symbol = list(securities[security]['cusip'])[0]
                        
                        if symbol != None:
                            # create symbol holding data if needed
                            if not symbol in self.accounts[account_number]['holdings']:
                                self.accounts[account_number]['holdings'][symbol] = {
                                    'name': symbols[symbol],
                                    'transactions': None,
                                    'statements': set(),
                                    'last_quantity': 0, 'current_quantity': 0, 'last_total_cost': None, 'current_total_cost': None}
                            
                            symbol_data = self.accounts[account_number]['holdings'][symbol]

                            symbol_data['statements'].add('%s: %s' % (broker_name, statement['statement']))
                            
                            symbol_data['current_quantity'] = 0
                            if 'quantity' in security_data:
                                symbol_data['current_quantity'] = security_data['quantity']
                            else:
                                symbol_data['current_quantity'] = 0
                            
                            symbol_data['total_cost'] = None
                            if 'total_cost' in security_data:
                                symbol_data['current_total_cost'] = security_data['total_cost']
                            else:
                                symbol_data['current_total_cost'] = None
                            
                            # print(statement['statement'])
                            self.__add_transactions(security_data['transactions'], account_number, symbol, statement)
                            
                            symbol_data['last_quantity'] = symbol_data['current_quantity']
                            symbol_data['last_total_cost'] = symbol_data['current_total_cost']
                
                # make sure all columns are filled
                for symbol, symbol_data in self.accounts[account_number]['holdings'].items():
                    if not isinstance(symbol_data['transactions'], type(None)):
                        for colum in ['quantity', 'amount', 'price', 'transaction_cost', 'quantity_total', 'cost_total']:
                            if not colum in symbol_data['transactions'].columns:
                                symbol_data['transactions'][colum] = np.nan

        storage.save(self.accounts, 'statement_accounts')

    def __add_transactions(self, transactions, account_number, symbol, statement):
        holding = self.accounts[account_number]['holdings'][symbol]
        if len(transactions) > 0:
            # rename transaction types
            for transaction in transactions:
                transaction['type'] = transaction['type'].lower()
            transactions = pd.DataFrame(transactions)
            
            # add columns if missing
            if not 'quantity' in transactions.columns:
                transactions['quantity'] = np.nan
            if not 'amount' in transactions.columns:
                transactions['amount'] = np.nan
            if not 'price' in transactions.columns:
                transactions['price'] = np.nan
            if not 'transaction_cost' in transactions.columns:
                transactions['transaction_cost'] = np.nan
            transactions = transactions[['transaction_date', 'type', 'quantity', 'amount', 'price', 'transaction_cost']]

            # fill all nan values with zeros
            transactions.loc[transactions['quantity'].isna(), 'quantity'] = 0.0

            # sort by date
            transactions = transactions.sort_values(by='transaction_date')

            quantity_transactions = transactions[transactions['quantity'] != 0.0].copy()
            non_quantity_transactions = transactions[transactions['quantity'] == 0.0].copy()

            if len(quantity_transactions) > 0:
                # set all amounts that could be None to nan
                amount_calc = quantity_transactions['amount'].isna()
                if quantity_transactions[amount_calc].shape[0] > 0:
                    quantity_transactions.loc[amount_calc, 'amount'] = np.nan
                
                # make sure quantity and amount is float64 and sign is correct
                quantity_transactions['quantity'] = quantity_transactions['quantity'].astype('float64')
                quantity_transactions['amount'] = quantity_transactions['amount'].astype('float64')
                amount_calc = np.sign(quantity_transactions['amount']) == np.sign(quantity_transactions['quantity'])
                if quantity_transactions[amount_calc].shape[0] > 0:
                    quantity_transactions.loc[amount_calc, 'amount'] = -quantity_transactions.loc[amount_calc, 'amount']
                
            if len(non_quantity_transactions) > 0:
                # filter out types
                not_handled = [
                    'interest earned', 'corporate action', 'reverse split', 'receive securities', 'fee', 'service fee', 'sold',
                ]
                non_quantity_transactions = non_quantity_transactions[~non_quantity_transactions['type'].isin(not_handled)]
                
                # set quantity and price to nan
                non_quantity_transactions['quantity'] = np.nan
                non_quantity_transactions['price'] = np.nan
                
            # concat both `quantity_transactions` and `non_quantity_transactions`
            if len(quantity_transactions) == 0:
                new_transactions = non_quantity_transactions.copy()
            else:
                new_transactions = quantity_transactions.copy()
                if len(non_quantity_transactions) > 0:
                    new_transactions = pd.concat([new_transactions, non_quantity_transactions])
            
            # add totals
            new_transactions['quantity_total'] = np.nan
            new_transactions['cost_total'] = np.nan
            totals = {'transaction_date': statement['end_date'], 'type': 'totals', 'quantity_total': np.nan, 'cost_total': np.nan}
            if holding['current_quantity'] != None and holding['current_quantity'] > 0:
                totals['quantity_total'] = holding['current_quantity']
            if holding['current_total_cost'] != None:
                totals['cost_total'] = holding['current_total_cost']
            new_transactions = new_transactions._append(totals, ignore_index=True)

            # sort by date and make it the index
            new_transactions = new_transactions.sort_values(by='transaction_date')
            new_transactions.set_index('transaction_date', inplace=True)

            # concat to existing transactions
            if isinstance(holding['transactions'], type(None)):
                holding['transactions'] = new_transactions.dropna(axis=1, how='all').copy()
            else:
                holding['transactions'] = pd.concat([holding['transactions'].dropna(axis=1, how='all'), new_transactions.dropna(axis=1, how='all')])
        else:
            pass
            # still add totals
            # totals = {'transaction_date': statement['end_date'], 'type': 'totals', 'quantity_total': np.nan, 'cost_total': np.nan}
            totals = {'type': 'totals', 'quantity_total': np.nan, 'cost_total': np.nan}
            if holding['current_quantity'] != None and holding['current_quantity'] > 0:
                totals['quantity_total'] = holding['current_quantity']
            if holding['current_total_cost'] != None:
                totals['cost_total'] = holding['current_total_cost']
            totals = pd.DataFrame({statement['end_date']: totals}).T
            totals['quantity_total'] = totals['quantity_total'].astype('float64')
            totals['cost_total'] = totals['cost_total'].astype('float64')
            if isinstance(holding['transactions'], type(None)):
                holding['transactions'] = totals.dropna(axis=1, how='all').copy()
            else:
                holding['transactions'] = pd.concat([holding['transactions'].dropna(axis=1, how='all'), totals.dropna(axis=1, how='all')])
    
    def __get_statements(self):
        self.statement_accounts = storage.load('statement_accounts')

    def __parse_statements(self):
        # get statements
        # TODO organize statement pdf collection
        pdf_files = []
        # pdf_files = glob.glob('test_statements/*.pdf')
        # pdf_files = glob.glob('database/statements/*.pdf')
        
        pdf_files += glob.glob('database/statements_ms/*.pdf')
        pdf_files += glob.glob('database/statements_fi/*.pdf')
        pdf_files += glob.glob('database/statements_st/*.pdf')
        pdf_files += glob.glob('database/statements_ml/*.pdf')
        
        # pdf_files = ['database/statements_ms\\RO_2023_09.pdf']

        # print('pdf files: %d' % len(pdf_files))
        citi = [
            'Citigroup Global Markets',
            'Account carried by Citigroup Global Markets',
        ]
        
        company_statements = []
        for pdf_file in pdf_files:
            statement = Statement(pdf_file)
            company_statement = None

            morgan_stanley = False
            for page_num, blocks in statement.get_blocks().items():
                for block in blocks:
                    # if pdf_file == 'database/statements_st\\STRO_2006_04.pdf':
                    #     print(block)
                    if 'Morgan Stanley' in block[0]:
                        morgan_stanley = True
                    elif morgan_stanley and block[0] == 'Account Summary':
                        company_statement = Morgan_Stanley(statement)
                    elif block[0] in ['Account At A Glance', 'Portfolio At A Glance']:
                        company_statement = Etrade(statement)
                    elif block[0].startswith('INVESTMENT REPORT'):
                        company_statement = Fidelity(statement)
                    elif block[0].startswith('Investment Report'):
                        company_statement = Fidelity_V2(statement)
                    elif 'Citigroup' in block[0]:
                        company_statement = Citi(statement)
                    elif block[0].startswith('Schwab'):
                        if block[0].startswith('Schwab Retirement Plan Services'):
                            pass # Not doing Schwab, no good info
                            # company_statement = Schwab(statement)
                        else:
                            pass # Not doing Schwab, no good info
                            # company_statement = Schwab_V2(statement)
                    elif 'SCOTTRADE, INC' in block:
                        if block.index('SCOTTRADE, INC') == 0:
                            company_statement = Scottrade(statement)
                        else:
                            company_statement = Scottrade_V2(statement)
                    elif block[0].startswith('Merrill Lynch'):
                        company_statement = Merrill_Lynch(statement)
                    elif block[0].startswith('All brokerage accounts are held at Merrill Lynch'):
                        company_statement = Merrill_Lynch_V2(statement)
                    if company_statement != None: break
                if company_statement != None: break
            if company_statement == None:
                if morgan_stanley:
                    pass
                    # company_statement = Morgan_Stanley_SB(statement)
                else:
                    pass
                    # print('UNKNOWNs: %s' % (pdf_file))
                    # for page_num, blocks in statement.get_blocks().items():
                    #     for block in blocks:
                    #         print('\t%s' % block[0])

            else:
                company_statements.append(company_statement)

        
        print('statements: %d' % len(company_statements))

        self.statement_accounts = {}
        for company_statement in company_statements:
            if not company_statement.name in self.statement_accounts:
                self.statement_accounts[company_statement.name] = {}
            for account_number, account_data in company_statement.accounts.items():
                if not account_number in self.statement_accounts[company_statement.name]:
                    self.statement_accounts[company_statement.name][account_number] = []
                self.statement_accounts[company_statement.name][account_number].append(account_data)

        # storage.save(self.statement_accounts, 'statement_accounts')
