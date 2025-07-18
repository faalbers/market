import tkinter as tk
from tkinter import ttk
from ...tickers import Tickers
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pprint import pp
import pandas as pd
import numpy as np

class Fundamentals_GUI(tk.Toplevel):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.set_fundamentals(symbols)
        self.symbols = symbols

        self.title('Fundamentals Compare')
        self.geometry("1200x800")

        self.frame_fundamentals_holder = Frame_Fundamentals_holder(self)
        self.frame_fundamentals_holder.pack(expand=True, fill='both')
        
        frame_bottom_options = tk.Frame(self)
        frame_bottom_options.pack(side='bottom', fill='x')

        data_type = [
            'net profit margin',
            'operating profit margin',
            'liquidity',
            'cash position',
        ]
        self.data_type = tk.StringVar()
        self.data_type.set(data_type[0])
        tk.OptionMenu(frame_bottom_options, self.data_type, *data_type, command=self.data_type_changed).pack(side='left')

        self.frame_fundamentals = None
        self.refresh_frame_fundamentals()

    def data_type_changed(self, data_type):
        self.plot_compare()

    def set_fundamentals(self, symbols):
        # get compare charts
        tickers = Tickers(symbols)
        symbol_fundamentals = tickers.get_fundamentals()

        # get  trailing data
        trailing = symbol_fundamentals['trailing'].copy()
        trailing['net_profit_margin'] = np.nan
        if 'income_net' in trailing.columns and 'revenue_total' in trailing.columns:
            is_revenue = (trailing['revenue_total'] > 0.0) & (trailing['income_net'] <= trailing['revenue_total'])
            trailing.loc[is_revenue, 'net_profit_margin'] = \
                (trailing.loc[is_revenue, 'income_net'] / trailing.loc[is_revenue, 'revenue_total']) * 100
        trailing['operating_profit_margin'] = np.nan
        if 'income_operating' in trailing.columns and 'revenue_total' in trailing.columns:
            is_revenue = (trailing['revenue_total'] > 0.0) & (trailing['income_operating'] <= trailing['revenue_total'])
            trailing.loc[is_revenue, 'operating_profit_margin'] = \
                (trailing.loc[is_revenue, 'income_operating'] / trailing.loc[is_revenue, 'revenue_total']) * 100

        self.yearly = self.get_fundamentals(symbol_fundamentals, 'yearly')
        self.quarterly = self.get_fundamentals(symbol_fundamentals, 'quarterly')

        # add ttm to yearly
        if not self.yearly['net_profit_margin'].empty:
            self.yearly['net_profit_margin'].loc['ttm'] = trailing['net_profit_margin']
        if not self.yearly['operating_profit_margin'].empty:
            self.yearly['operating_profit_margin'].loc['ttm'] = trailing['operating_profit_margin']

    def get_fundamentals(self, symbol_fundamentals, period):
        print('fundamentals: %s' % period)
        fundamentals = {
            'net_profit_margin': pd.DataFrame(),
            'operating_profit_margin': pd.DataFrame(),
        }
        for symbol, period_symbol in symbol_fundamentals[period].items():
            if period_symbol.empty: continue
            period_symbol = period_symbol.dropna(how='all').copy()

            # add counts to index
            # period_symbol = period_symbol.iloc[::-1]
            if period == 'yearly':
                period_symbol.index = period_symbol.index.year
            elif period == 'quarterly':
                period_symbol.index = ['q%s' % (period_symbol.shape[0] - q - 1) for q in range(period_symbol.shape[0])]
            else: continue

            # add net_profit_margin
            period_symbol[symbol] = np.nan
            if 'income_net' in period_symbol.columns and 'revenue_total' in period_symbol.columns:
                is_revenue = (period_symbol['revenue_total'] > 0.0) & (period_symbol['income_net'] <= period_symbol['revenue_total'])
                period_symbol.loc[is_revenue, symbol] = \
                    (period_symbol.loc[is_revenue, 'income_net'] / period_symbol.loc[is_revenue, 'revenue_total']) * 100
            fundamentals['net_profit_margin'] = fundamentals['net_profit_margin'].merge(period_symbol[symbol], how='outer', left_index=True, right_index=True)
            
            # add operating_profit_margin
            period_symbol[symbol] = np.nan
            if 'income_operating' in period_symbol.columns and 'revenue_total' in period_symbol.columns:
                is_revenue = (period_symbol['revenue_total'] > 0.0) & (period_symbol['income_operating'] <= period_symbol['revenue_total'])
                period_symbol.loc[is_revenue, symbol] = \
                    (period_symbol.loc[is_revenue, 'income_operating'] / period_symbol.loc[is_revenue, 'revenue_total']) * 100
            fundamentals['operating_profit_margin'] = fundamentals['operating_profit_margin'].merge(period_symbol[symbol], how='outer', left_index=True, right_index=True)

        if period == 'quarterly':
            fundamentals['net_profit_margin'] = fundamentals['net_profit_margin'].sort_index(ascending=False)
            fundamentals['operating_profit_margin'] = fundamentals['operating_profit_margin'].sort_index(ascending=False)

        return fundamentals

    def plot_compare(self):
        if self.data_type.get() == 'net profit margin':
            data = self.yearly['net_profit_margin']
            symbols = [s for s in data.columns if s in self.symbols]
            data = data[symbols]
            y_label = 'Net Profit Margin %'
        elif self.data_type.get() == 'operating profit margin':
            data = self.yearly['operating_profit_margin']
            symbols = [s for s in data.columns if s in self.symbols]
            data = data[symbols]
            y_label = 'Operating Profit Margin %'
        else: return

        fig, ax = plt.subplots()
        if not data.empty:
            data.plot(ax=ax, kind='bar')
            ax.set_ylabel(y_label)
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
            # ax.bar(dividends.index, dividends, color='green', alpha=0.5, width=bar_width)
            # bar_width = dividends.shape[0] / 75.0
            # ax.bar(dividends.index, dividends, alpha=0.5, width=bar_width)
            # ax.axhline(y=0.0, color='black', linestyle='--', linewidth=1)
            # ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
            # for column in dividends.columns:
            #     annotate_x = dividends[column].index[-1]
            #     annotate_y = dividends[column].values[-1]
            #     ax.annotate(column, xy=(annotate_x, annotate_y), fontsize=8, xytext=(2, 2), textcoords='offset points')
        plt.tight_layout()
        self.frame_fundamentals.draw_figure(fig)
        plt.close(fig)

    def refresh_frame_fundamentals(self):
        if self.frame_fundamentals != None:
            self.frame_fundamentals.destroy()
        self.frame_fundamentals = Frame_Fundamentals(self.frame_fundamentals_holder, self.symbols)
        self.frame_fundamentals.pack(expand=True, fill='both')
        self.symbols = self.symbols[:1]
        self.plot_compare()

    def symbols_changed(self, symbols):
        self.symbols = symbols
        self.plot_compare()


class Frame_Fundamentals_holder(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def symbols_changed(self, symbols):
        self.parent.symbols_changed(symbols)

class Frame_Fundamentals(ttk.Frame):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.parent = parent

        frame_symbols = Frame_Symbols(self, symbols)
        frame_symbols.pack(side='left', fill='y')
        self.frame_graph = Frame_Graph(self)
        self.frame_graph.pack(side='left', expand=True, fill='both')
    
    def symbols_changed(self, symbols):
        self.parent.symbols_changed(symbols)
    
    def draw_figure(self, fig):
        self.frame_graph.draw_figure(fig)


class Frame_Symbols(ttk.Frame):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.parent = parent

        self.canvas = tk.Canvas(self)
        self.canvas.pack(side='left', fill='both')

        self.frame_checkboxes = tk.Frame(self)
        self.canvas.create_window((0,0), window=self.frame_checkboxes, anchor='nw')

        widest_check = 0
        height_check = 0
        self.symbols_state = {}
        for symbol in symbols:
            self.symbols_state[symbol] = tk.IntVar()
            # self.symbols_state[symbol].set(1)
            check_button = tk.Checkbutton(self.frame_checkboxes, text=symbol,
                variable=self.symbols_state[symbol], command=self.check_changed)
            check_button.bind('<MouseWheel>', self.mouse_scroll)
            check_button.bind('<ButtonRelease-1>', self.check_released)
            check_button.pack(anchor='w')
            if check_button.winfo_reqwidth() > widest_check: widest_check = check_button.winfo_reqwidth()
            height_check += check_button.winfo_reqheight()
        self.symbols_state[symbols[0]].set(1)
        self.canvas.config(width=widest_check)
        self.canvas.config(scrollregion=(0,0,widest_check, height_check))

        scrollbar = ttk.Scrollbar(self, orient = 'vertical', command=self.scroll_update)
        self.canvas.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

    def scroll_update(self, *params):
        if self.canvas.winfo_height() <= self.frame_checkboxes.winfo_height():
            self.canvas.yview(*params)
    
    def mouse_scroll(self, event):
        if self.canvas.winfo_height() <= self.frame_checkboxes.winfo_height():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

    def check_released(self, event):
        if event.state & 0x0001:
            # With shift , change state of them
            current_symbol = event.widget.cget('text')
            state_inverse = abs((self.symbols_state[current_symbol].get())-1)
            for symbol, symbol_state in self.symbols_state.items():
                if symbol == current_symbol: continue
                symbol_state.set(state_inverse)
    
    def check_changed(self):
        self.parent.symbols_changed(self.get_symbols())
    
    def get_symbols(self):
        return [symbol for symbol, symbol_state in self.symbols_state.items() if symbol_state.get() == 1]

class Frame_Graph(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.canvas = None

    def draw_figure(self, fig):
        if self.canvas != None:
            self.canvas.get_tk_widget().destroy()
            del(self.canvas)

        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
