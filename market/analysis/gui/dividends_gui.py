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
        self.set_dividends(symbols)
        self.symbols = symbols

        self.title('Dividends Compare')
        self.geometry("1200x800")

        self.frame_dividends_holder = Frame_Dividends_holder(self)
        self.frame_dividends_holder.pack(expand=True, fill='both')
        
        frame_bottom_options = tk.Frame(self)
        frame_bottom_options.pack(side='bottom', fill='x')

        # start_date_chart, end_date_chart = self.get_chart_dates()
        tk.Label(frame_bottom_options, text='Start Date:').pack(side='left')
        self.start_date = DateEntry(frame_bottom_options,
            selectmode='day', date_pattern="yyyy-mm-dd")
        self.start_date.bind("<<DateEntrySelected>>", self.date_changed)
        self.start_date.pack(side='left')
        
        tk.Label(frame_bottom_options, text='End Date:').pack(side='left')
        self.end_date = DateEntry(frame_bottom_options,
            selectmode='day', date_pattern="yyyy-mm-dd")
        self.end_date.bind("<<DateEntrySelected>>", self.date_changed)
        self.end_date.pack(side='left')

        date_range = [
            'range all',
            'range ttm',
            'range year to date',
            'range 3 years',
            'range 5 years',
        ]
        self.date_range = tk.StringVar()
        self.date_range.set(date_range[0])
        tk.OptionMenu(frame_bottom_options, self.date_range, *date_range, command=self.date_range_changed).pack(side='left')

        # self.auto_update_date = tk.BooleanVar()
        # self.auto_update_date.set(False)
        # tk.Checkbutton(frame_bottom_options, text='auto date', variable=self.auto_update_date).pack(side='left')

        # self.yearly_dividends = tk.BooleanVar()
        # self.yearly_dividends.set(False)
        # tk.Checkbutton(frame_bottom_options, text='yearly', variable=self.yearly_dividends, command=self.plot_compare).pack(side='left')
        sum_range = [
            'no sum',
            'sum ttm',
            'sum yearly',
        ]
        self.sum_range = tk.StringVar()
        self.sum_range.set(sum_range[0])
        tk.OptionMenu(frame_bottom_options, self.sum_range, *sum_range, command=self.sum_range_changed).pack(side='left')

        self.yield_dividends = tk.BooleanVar()
        self.yield_dividends.set(False)
        tk.Checkbutton(frame_bottom_options, text='yield', variable=self.yield_dividends, command=self.plot_compare).pack(side='left')

        self.frame_dividends = None
        self.refresh_frame_dividends()

    def set_dividends(self, symbols):
        # get compare charts
        tickers = Tickers(symbols)
        # charts = tickers.get_charts(update=update, forced=forced)
        symbol_charts = tickers.get_charts()

        # create compare and compare sector
        self.dividends = pd.DataFrame()
        self.dividend_yields = pd.DataFrame()
        for symbol, chart in symbol_charts.items():
            # stock splitted dividends
            dividends = chart[chart['Dividends'] > 0].copy()
            dividends['Yields'] = (dividends['Dividends'] / dividends['Adj Close']) * 100
            
            # add dividends
            self.dividends = self.dividends.merge(dividends['Dividends'], how='outer', left_index=True, right_index=True)
            self.dividends = self.dividends.rename(columns={'Dividends': symbol})
            
            # add dividend yields
            self.dividend_yields = self.dividend_yields.merge(dividends['Yields'], how='outer', left_index=True, right_index=True)
            self.dividend_yields = self.dividend_yields.rename(columns={'Yields': symbol})
        
        # create ttm dates for sum collection
        now = pd.Timestamp.now()
        today = pd.Timestamp(now.year, now.month, now.day) + pd.DateOffset(days=1)
        self.dates_ttm = pd.Series([(today - pd.DateOffset(years=y)) for y in range(10)]).iloc[::-1]

        # create yearly dates for sum collection
        last_year_day = pd.Timestamp(now.year, 1, 1)
        self.dates_yearly = pd.Series([(last_year_day - pd.DateOffset(years=y)) for y in range(10)]).iloc[::-1]

    def date_range_changed(self, date_range):
        self.set_dates()
        self.plot_compare()
    
    def sum_range_changed(self, sum_range):
        self.plot_compare()

    def set_dates(self):
        dividends = self.dividends[self.symbols]
        start_date = dividends.index[0]
        date_range = self.date_range.get()
        if date_range == 'range ttm':
            start_date = pd.Timestamp.now() - pd.DateOffset(months=12)
        elif date_range == 'range year to date':
            start_date = pd.Timestamp(pd.Timestamp.now().year, 1, 1)
        elif date_range == 'range 3 years':
            start_date = pd.Timestamp.now() - pd.DateOffset(years=3)
        elif date_range == 'range 5 years':
            start_date = pd.Timestamp.now() - pd.DateOffset(years=5)
        self.start_date.set_date(start_date)

    def get_dividends(self):
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        return self.dividends[self.symbols].loc[start_date:end_date].dropna(how='all').copy()

    def get_dividend_yields(self):
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        return self.dividend_yields[self.symbols].loc[start_date:end_date].dropna(how='all').copy()

    def plot_compare(self):
        if self.yield_dividends.get():
            dividends = self.get_dividend_yields()
            y_label = 'Yield %'
        else:
            dividends = self.get_dividends()
            y_label = 'amount/share $'
        # print(dividends)
        # now = pd.Timestamp.now()
        # print(dividends.groupby(dividends.index.map(lambda x: relativedelta(now, x).years)).sum())
        
        # dividends.index = dividends.index.date
        now = pd.Timestamp.now()
        last_year = now.year - 1

        # show by grouped range
        sum_range = self.sum_range.get()
        start_date = pd.Timestamp(self.start_date.get_date())
        end_date = pd.Timestamp(self.end_date.get_date())
        if sum_range == 'no sum':
            dividends.index = dividends.index.date
        if sum_range == 'sum ttm':
            # set lock dates to full sum ttm range
            start_date_ttm = self.dates_ttm[self.dates_ttm >= start_date].iloc[0]
            end_date_ttm = self.dates_ttm[self.dates_ttm <= (end_date + pd.DateOffset(days=1))].iloc[-1] - pd.DateOffset(days=1)
            dividends = dividends[start_date_ttm:end_date_ttm]
            
            # group by years ago
            dividends = dividends.groupby(dividends.index.map(lambda x: relativedelta(now, x).years)).sum()
            dividends.sort_index(ascending=False, inplace=True)
            dividends.index.name = 'year trailing'
        
        elif sum_range == 'sum yearly':
            # set lock dates to full sum yearly range
            start_date_yearly = self.dates_yearly[self.dates_yearly >= start_date].iloc[0]
            end_date_yearly = self.dates_yearly[self.dates_yearly <= (end_date + pd.DateOffset(days=1))].iloc[-1] - pd.DateOffset(days=1)
            dividends = dividends[start_date_yearly:end_date_yearly]
            
            # group by yearly range
            dividends = dividends.groupby(dividends.index.year).sum()
            dividends = dividends
            dividends.index.name = 'year'
        
        # if self.yearly_dividends.get():
        #     dividends = dividends.groupby(dividends.index.year).sum()
        # else:
        #     dividends.index = dividends.index.date

        fig, ax = plt.subplots()
        if not dividends.empty:
            dividends.plot(ax=ax, kind='bar')
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
        self.frame_dividends.draw_figure(fig)
        plt.close(fig)

    def refresh_frame_dividends(self):
        if self.frame_dividends != None:
            self.frame_dividends.destroy()
        self.frame_dividends = Frame_Dividends(self.frame_dividends_holder, self.symbols)
        self.frame_dividends.pack(expand=True, fill='both')
        # if self.auto_update_date.get():
        #     self.set_dates()
        self.symbols = self.symbols[:1]
        self.set_dates()
        self.plot_compare()

    def symbols_changed(self, symbols):
        self.symbols = symbols
        # if self.auto_update_date.get():
        #     self.set_dates()
        self.set_dates()
        self.plot_compare()

    def date_changed(self, event):
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
