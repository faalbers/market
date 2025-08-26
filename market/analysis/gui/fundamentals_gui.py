import tkinter as tk
from tkinter import ttk
from ...tickers import Tickers
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pprint import pp
import pandas as pd
import numpy as np
import talib as ta


class Fundamentals_GUI(tk.Toplevel):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.analysis_data = parent.analysis_data
        self.set_fundamentals(symbols)
        self.symbols = symbols

        self.title('Fundamentals Compare')
        self.geometry("1200x800")

        self.frame_fundamentals_holder = Frame_Fundamentals_holder(self)
        self.frame_fundamentals_holder.pack(expand=True, fill='both')
        
        frame_bottom_options = tk.Frame(self)
        frame_bottom_options.pack(side='bottom', fill='x')

        data_type = [
            'current ratio',
            'cash ratio',
            'gross profit margin',
            'operating profit margin',
            'profit margin',
            'net profit margin',
        ]
        self.data_type = tk.StringVar()
        self.data_type.set(data_type[0])
        tk.OptionMenu(frame_bottom_options, self.data_type, *data_type, command=self.data_type_changed).pack(side='left')
        
        data_period = [
            'yearly',
            'quarterly',
        ]
        self.data_period = tk.StringVar()
        self.data_period.set(data_period[0])
        tk.OptionMenu(frame_bottom_options, self.data_period, *data_period, command=self.data_period_changed).pack(side='left')

        self.frame_fundamentals = None
        self.refresh_frame_fundamentals()

    def data_type_changed(self, data_type):
        self.plot_compare()

    def data_period_changed(self, data_type):
        self.plot_compare()

    def set_fundamentals(self, symbols):
        # get compare fundamentals
        tickers = Tickers(symbols)
        fundamentals = tickers.get_vault_fundamentals()
        self.fundamentals = {}
        self.fundamentals['yearly'] = self.analysis.get_fundamentals(fundamentals, 'yearly')
        self.fundamentals['quarterly'] = self.analysis.get_fundamentals(fundamentals, 'quarterly')
        fundamentals_ttm = self.analysis.get_fundamentals_ttm(fundamentals)
        for parameter, data in self.fundamentals['yearly'].items():
            if parameter in fundamentals_ttm.index:
                param_ttm = fundamentals_ttm.loc[parameter].dropna()
                if not param_ttm.empty:
                    if not data.empty:
                        data.loc['ttm'] = param_ttm
                    else:
                        data.loc['ttm'] = pd.DataFrame(param_ttm).T

    def plot_compare(self):
        data_type = self.data_type.get()
        data_period = self.data_period.get()
        data = self.fundamentals[data_period][data_type].copy()
        if not data.empty and data_period == 'quarterly':
            data.index = data.index.date
        symbols = [s for s in data.columns if s in self.symbols]
        data = data[symbols]
        data.dropna(axis=0, how='all', inplace=True)
        
        fig, ax = plt.subplots()
        if not data.empty:
            data.plot(ax=ax, kind='bar')
            ax.set_ylabel(data_type + ' %')
            ax.grid(True, linestyle='--', linewidth=0.5, color='gray')
        plt.tight_layout()
        self.frame_fundamentals.draw_figure(fig)
        plt.close(fig)

    def refresh_frame_fundamentals(self):
        print('refresh_frame_fundamentals')
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
