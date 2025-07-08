import tkinter as tk
from tkcalendar import DateEntry
from tkinter import ttk
from ...tickers import Tickers
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Charts_GUI(tk.Toplevel):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.set_charts(symbols)
        self.set_charts_sectors(symbols)
        self.symbols = symbols
        self.sector = 'N/A'

        # print(self.charts)
        # print(self.charts_sectors)
        # print(self.sector_symbols)

        self.title('Charts Compare')
        self.geometry("1200x800")

        frame_top_options = tk.Frame(self)
        frame_top_options.pack(fill='x')

        self.frame_chart_holder = Frame_Chart_holder(self)
        self.frame_chart_holder.pack(expand=True, fill='both')
        
        frame_bottom_options = tk.Frame(self)
        frame_bottom_options.pack(side='bottom', fill='x')
        
        tk.Label(frame_top_options, text='Sector:').pack(side='left')
        sectors = ['N/A'] + sorted(self.charts_sectors.columns)
        sector_select = tk.StringVar()
        sector_select.set(sectors[0])
        sector = tk.OptionMenu(frame_top_options, sector_select, *sectors, command=self.sector_changed)
        sector.pack(side='left')

        self.frame_chart = None

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

        self.auto_update_date = tk.BooleanVar()
        self.auto_update_date.set(True)
        tk.Checkbutton(frame_bottom_options, text='auto date', variable=self.auto_update_date).pack(side='left')
        
        self.sector_relative = tk.BooleanVar()
        tk.Checkbutton(frame_bottom_options, text='sector relative',
            variable=self.sector_relative,
            command=self.sector_relative_changed).pack(side='left')
        
        self.end_date.pack(side='left')
        self.refresh_frame_chart()

    def sector_relative_changed(self):
        self.plot_compare()
        
    def set_dates(self):
        charts = self.charts[self.symbols].ffill().dropna()
        start_date = charts.index[0]
        end_date = charts.index[-1]
        self.start_date.set_date(start_date)
        self.end_date.set_date(end_date)

    def refresh_frame_chart(self):
        if self.frame_chart != None:
            self.frame_chart.destroy()
        self.frame_chart = Frame_Chart(self.frame_chart_holder, self.symbols, self.sector)
        self.frame_chart.pack(expand=True, fill='both')
        if self.auto_update_date.get():
            self.set_dates()
        self.plot_compare()

    def get_charts(self):
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        return self.charts[self.symbols].ffill().dropna().loc[start_date:end_date].copy()

    def plot_compare(self):
        compare = self.get_charts()
        compare = compare / compare.iloc[0]
        if self.sector_relative.get() and self.sector != 'N/A':
            compare = compare.merge(self.charts_sectors[self.sector], how='inner', left_index=True, right_index=True)
            compare[self.sector] = compare[self.sector] / compare[self.sector].iloc[0]
            compare = compare.sub(compare[self.sector], axis=0)
            compare = compare.drop(self.sector, axis=1)
        else:
            compare = compare - 1.0

        fig, ax = plt.subplots()
        if not compare.empty:
            compare.plot(ax=ax)
            ax.axhline(y=0.0, color='black', linestyle='--', linewidth=1)
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
            for column in compare.columns:
                annotate_x = compare[column].index[-1]
                annotate_y = compare[column].values[-1]
                ax.annotate(column, xy=(annotate_x, annotate_y), fontsize=8, xytext=(2, 2), textcoords='offset points')
        plt.tight_layout()
        self.frame_chart.draw_figure(fig)
        plt.close(fig)

    def symbols_changed(self, symbols):
        self.symbols = symbols
        if self.auto_update_date.get():
            self.set_dates()
        self.plot_compare()

    def sector_changed(self, sector):
        self.sector= sector
        self.symbols = self.sector_symbols[sector]
        self.refresh_frame_chart()
    
    def date_changed(self, event):
        self.plot_compare()

    def set_charts(self, symbols):
        # get compare charts
        tickers = Tickers(symbols)
        # charts = tickers.get_charts(update=update, forced=forced)
        symbol_charts = tickers.get_charts()

        # create compare and compare sector
        self.charts = pd.DataFrame()
        for symbol, chart in symbol_charts.items():
            # add compare
            adj_close = chart['Adj Close']
            self.charts = self.charts.merge(adj_close, how='outer', left_index=True, right_index=True)
            self.charts = self.charts.rename(columns={'Adj Close': symbol})

    def set_charts_sectors(self, symbols):
        # get sector charts
        sectors_found = self.analysis.loc[symbols, 'sector'].dropna().unique()
        sectors = {
            'XLV': 'Healthcare',
            'XLB': 'Basic Materials',
            'XLK': 'Technology',
            'XLF': 'Financial Services',
            'XLI': 'Industrials',
            'XLRE': 'Real Estate',
            'XLC': 'Communication Services',
            'XLU': 'Utilities',
            'XLE': 'Energy',
            'XLP': 'Consumer Defensive',
            'XLY': 'Consumer Cyclical',
            # 'SPY': 'S&P500',
        }
        sector_tickers = Tickers(list(sectors.keys()))
        sector_charts = sector_tickers.get_charts()
        self.charts_sectors = pd.DataFrame()
        self.sector_symbols = {}
        for sector_symbol, sector in sectors.items():
            if sector not in sectors_found: continue
            self.sector_symbols[sector] = []
            if not sector_symbol in sector_charts:
                raise Exception('sector ticker not found: %s' % sector_symbol)
            self.charts_sectors = self.charts_sectors.merge(sector_charts[sector_symbol]['Adj Close'], how='outer', left_index=True, right_index=True)
            self.charts_sectors = self.charts_sectors.rename(columns={'Adj Close': sector})
        
        for symbol, sector in self.analysis.loc[symbols]['sector'].dropna().items():
            self.sector_symbols[sector].append(symbol)
        self.sector_symbols['N/A'] = symbols

class Frame_Chart_holder(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    def symbols_changed(self, symbols):
        self.parent.symbols_changed(symbols)

class Frame_Chart(ttk.Frame):
    def __init__(self, parent, symbols, sector):
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
            self.symbols_state[symbol].set(1)
            check_button = tk.Checkbutton(self.frame_checkboxes, text=symbol,
                variable=self.symbols_state[symbol], command=self.check_changed)
            check_button.bind('<MouseWheel>', self.mouse_scroll)
            check_button.bind('<ButtonRelease-1>', self.check_released)
            check_button.pack(anchor='w')
            if check_button.winfo_reqwidth() > widest_check: widest_check = check_button.winfo_reqwidth()
            height_check += check_button.winfo_reqheight()
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
