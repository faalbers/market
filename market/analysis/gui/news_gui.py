import tkinter as tk
from tkinter import ttk
from ...tickers import Tickers
import pandas as pd
from pprint import pp
import numpy as np
import webbrowser

class News_GUI(tk.Toplevel):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.analysis_data = parent.analysis_data
        self.symbols = symbols
        self.set_news(symbols)

        self.title('News')
        self.geometry("1200x800")

        self.frame_news_holder = Frame_News_holder(self)
        self.frame_news_holder.pack(expand=True, fill='both')
        
        frame_bottom_options = tk.Frame(self)
        frame_bottom_options.pack(side='bottom', fill='x')

        self.test = tk.BooleanVar()
        self.test.set(True)
        tk.Checkbutton(frame_bottom_options, text='test', variable=self.test).pack(side='left')

        self.frame_news = None
        self.refresh_frame_news()

    def set_news(self, symbols):
        tickers = Tickers(symbols)
        news = tickers.get_news()
        self.news = {}
        if 'news_polygon' in news:
            for symbol, symbol_news in news['news_polygon'].items():
                self.news[symbol] = symbol_news
        if 'news_finviz' in news:
            for symbol, symbol_news in news['news_finviz'].items():
                if not symbol in self.news:
                    self.news[symbol] = symbol_news
                else:
                    self.news[symbol] = pd.concat([self.news[symbol], symbol_news])
        
        # sort descending dates and limit to 100
        for symbol in self.news:
            self.news[symbol].sort_index(ascending=False, inplace=True)
            self.news[symbol] = self.news[symbol].head(100)

    def refresh_frame_news(self):
        if self.frame_news != None:
            self.frame_news.destroy()
        self.frame_news = Frame_News(self.frame_news_holder, self.symbols, self.news)
        self.frame_news.pack(expand=True, fill='both')

class Frame_News_holder(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

class Frame_News(ttk.Frame):
    def __init__(self, parent, symbols, news):
        super().__init__(parent)
        self.parent = parent

        self.frame_tree = Frame_Tree(self, news)
        frame_symbols = Frame_Symbols(self, symbols)
        frame_symbols.pack(side='left', fill='y')
        self.frame_tree.pack(side='left', expand=True, fill='both')
    
    def symbol_changed(self, symbol):
        # self.parent.symbol_changed(symbol)
        self.frame_tree.symbol_changed(symbol)
    
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
        self.check_changed()

    def scroll_update(self, *params):
        if self.canvas.winfo_height() <= self.frame_checkboxes.winfo_height():
            self.canvas.yview(*params)
    
    def mouse_scroll(self, event):
        if self.canvas.winfo_height() <= self.frame_checkboxes.winfo_height():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

    def check_released(self, event):
        for symbol, symbol_state in self.symbols_state.items():
            symbol_state.set(0)
    
    def check_changed(self):
        self.parent.symbol_changed(self.get_symbol())
    
    def get_symbol(self):
        for symbol, symbol_state in self.symbols_state.items():
            if symbol_state.get() == 1: return symbol

class Frame_Tree(ttk.Frame):
    def __init__(self, parent, news):
        super().__init__(parent)
        self.parent = parent
        self.news = news

        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview', fieldbackground="#593C3C")

    def symbol_changed(self, symbol):
        self.symbol = symbol
        for widget in self.winfo_children():
            widget.destroy()

        if not symbol in self.news: return
        news = self.news[self.symbol].reset_index().copy()
        self.url = news['url'].copy()
        news.loc[news['url'].str.startswith('http'), 'url'] = '*'
        news.loc[~(news['url'] == '*'), 'url'] = ''
        news = news[['date', 'url', 'title']]

        tree_scroll = tk.Scrollbar(self)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(self, yscrollcommand=tree_scroll.set, selectmode='extended')
        self.tree.bind('<Control-a>', self.select_all)
        self.tree.bind('<Button-3>', self.right_click)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.tree['columns'] = news.columns.tolist()
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.heading('#0', text='', anchor=tk.W)

        # # Bind Ctrl+A to select all
        # self.tree.bind('<Control-a>', self.select_all)
        # self.tree.bind('<Key>', self.key_pressed)
        # self.tree.bind('<KeyRelease>', self.key_released)
        if len(news.columns) > 0:
            for column in news.columns:
                if column == 'date': self.tree.column(column, anchor=tk.W, width=120, minwidth=120, stretch=tk.NO)
                elif column == 'url': self.tree.column(column, anchor=tk.W, width=20, minwidth=20, stretch=tk.NO)
                else: self.tree.column(column, anchor=tk.W, stretch=tk.YES)
                # self.tree.heading(column, text=column, anchor=tk.W, command = lambda _col=column: self.sort_tree_new(_col, False))
                self.tree.heading(column, text=column, anchor=tk.W)

            for symbol, row in news.iterrows():
                values = []
                for value in row.values:
                    if isinstance(value, float):
                        value = np.round(value, 2)
                    values.append(value)
                self.tree.insert('', 'end', values=values)
        self.tree.focus_set()

    def select_all(self, event=None):
        children = self.tree.get_children()
        self.tree.selection_set(children)

    def right_click(self, event=None):
        for selected_item in self.tree.selection():
            index = self.tree.index(selected_item)
            url = self.url[index]
            if not url.startswith('http'): continue
            webbrowser.open(url)
