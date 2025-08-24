import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from ...tickers import Tickers
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dateutil.relativedelta import relativedelta

class Dividends_GUI(tk.Toplevel):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.analysis_data = parent.analysis_data
        self.set_dividends(symbols)
        self.symbols = symbols

        self.title('Dividends Compare')
        self.geometry("1200x800")

        self.frame_dividends_holder = Frame_Dividends_holder(self)
        self.frame_dividends_holder.pack(expand=True, fill='both')
        
        frame_bottom_options = tk.Frame(self)
        frame_bottom_options.pack(side='bottom', fill='x')

        date_range = [
            'yearly',
            'ttm',
            'last year',
            'last ttm',
            'all',
        ]
        self.date_range = tk.StringVar()
        self.date_range.set(date_range[0])
        tk.OptionMenu(frame_bottom_options, self.date_range, *date_range, command=self.date_range_changed).pack(side='left')

        self.frame_dividends = None
        self.refresh_frame_dividends()

    def set_dividends(self, symbols):
        # get compare charts
        tickers = Tickers(symbols)
        
        charts = tickers.get_vault_charts()
        self.dividends = self.analysis.get_dividend_yields(charts)

    def date_range_changed(self, date_range):
        self.plot_compare()
    
    def get_dividends(self):
        date_range = self.date_range.get()
        y_label = 'Yield %'
        now = pd.Timestamp.now()
        last_year = now.year - 1
        if date_range == 'all':
            x_label = 'Date'
            dividends = self.dividends['all']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
            dividends.index = dividends.index.date
        elif date_range == 'last ttm':
            x_label = 'Date'
            dividends = self.dividends['all']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
            start_date = now.normalize() - pd.DateOffset(years=1) + pd.DateOffset(days=1)
            dividends = dividends.loc[start_date:]
            dividends.index = dividends.index.date
        elif date_range == 'last year':
            x_label = 'Date'
            dividends = self.dividends['all']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
            dividends = dividends[dividends.index.year == last_year]
            dividends.index = dividends.index.date
        elif date_range == 'ttm':
            x_label = 'Year ttm'
            dividends = self.dividends['ttm']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
        elif date_range == 'yearly':
            x_label = 'Year'
            dividends = self.dividends['yearly']
            dividends = dividends[[c for c in self.symbols if c in dividends.columns]].copy()
            dividends.dropna(axis=0, how='all', inplace=True)
        
        return dividends, x_label, y_label

    def plot_compare(self):
        dividends, x_label, y_label = self.get_dividends()

        fig, ax = plt.subplots()
        if not dividends.empty:
            dividends.plot(ax=ax, kind='bar')
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
            # ax.legend(['%s ($%s)' % (c, round(self.analysis_data.loc[c, 'price'], 2)) for c in dividends.columns])
        plt.tight_layout()
        self.frame_dividends.draw_figure(fig)
        plt.close(fig)

    def refresh_frame_dividends(self):
        if self.frame_dividends != None:
            self.frame_dividends.destroy()
        self.frame_dividends = Frame_Dividends(self.frame_dividends_holder, self.symbols)
        self.frame_dividends.pack(expand=True, fill='both')
        self.symbols = self.symbols[:1]
        self.plot_compare()

    def symbols_changed(self, symbols):
        self.symbols = symbols
        self.plot_compare()

class Frame_Dividends_holder(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def symbols_changed(self, symbols):
        self.parent.symbols_changed(symbols)

class Frame_Dividends(ttk.Frame):
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
