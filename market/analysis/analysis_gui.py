from ..tickers import Tickers
from ..analysis import Analysis
import tkinter as tk
from pprint import pp
import pandas as pd

class Analysis_GUI:
    def __init__(self, symbols=[]):
        self.tickers = Tickers(symbols)
        self.analysis = Analysis(self.tickers)
        self.__root = tk.Tk()
        self.__build_gui()
        self.__root.mainloop()

    def __build_gui(self):
        # self.__root.geometry('550x100')
        self.__root.title('Market Analysis')

        filter_actions = tk.Frame(self.__root)
        self.filters_frame = Filters_Frame(self.__root, self)
        # self.filters_frame.grid_columnconfigure(0, minsize=500)
        
        self.add_filter = tk.Button(filter_actions, text='Add Filter', command=self.filters_frame.add_filter_frame)
        analyse = tk.Button(filter_actions, text='Analyse', command=self.analyze)
        empty_block = tk.Frame(filter_actions, width=400)
        self.add_filter.grid(row=0, column=0)
        analyse.grid(row=0, column=1)
        empty_block.grid(row=0, column=2)
        filter_actions.pack(anchor='w', padx=10, pady=10)
        self.filters_frame.pack(anchor='w', padx=10, pady=10)

    def reset_filters_frame(self):
        self.filters_frame.destroy()
        self.filters_frame = Filters_Frame(self.__root, self)
        self.add_filter.config(command=self.filters_frame.add_filter_frame)
        self.filters_frame.pack(anchor='w', padx=10, pady=10)

    def analyze(self):
        filters = self.filters_frame.get_filters()
        pp(filters)

class Filters_Frame(tk.Frame):
    def __init__(self, parent, gui):
        super().__init__(parent, highlightbackground="#70B41C", highlightthickness=2)
        self.parent = parent
        self.gui = gui
        self.analysis = self.gui.analysis

    def add_filter_frame(self):
        filter_frame = Filter_Frame(self, self.analysis)
        new_row = self.grid_size()[1]
        filter_frame.grid(row=new_row, column=0, sticky=tk.W)
    
    def remove_filter_frame(self, filter_frame_a):
        filter_frame_a.destroy()
        if len(self.winfo_children()) > 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(row=i)
        else:
            self.gui.reset_filters_frame()
    
    def get_filters(self):
        filters = []
        for filter_frame in self.winfo_children():
            filters.append(filter_frame.get_filter())
        return filters

class Filter_Frame(tk.Frame):
    def __init__(self, parent, analysis):
        super().__init__(parent)
        self.parent = parent
        self.analysis = analysis
        self.grid_columnconfigure(0, minsize=530)

        self.filter = Filter(self, self.analysis)
        self.filter.grid(row=0, column=0, sticky=tk.W)
        self.filter_or_frame = Filter_Or_Frame(self, self.analysis)
        self.filter_or_frame.grid(row=1, column=0, sticky=tk.E)

    def add_filter(self):
        self.filter_or_frame.add_filter()

    def remove_filter(self, filter_a):
        self.parent.remove_filter_frame(self)

    def reset_filter_or_frame(self):
        self.filter_or_frame.destroy()
        self.filter_or_frame = Filter_Or_Frame(self, self.analysis)
        self.filter_or_frame.grid(row=1, column=0, sticky=tk.E)

    def get_filter(self):
        filter = {}
        filter['and'] = self.filter.get_filter()
        filter['or'] = self.filter_or_frame.get_filters()
        return filter

class Filter_Or_Frame(tk.Frame):
    def __init__(self, parent, analysis):
        super().__init__(parent, highlightbackground="#2272C7", highlightthickness=2)
        self.parent = parent
        self.analysis = analysis

    def add_filter(self):
        filter = Filter(self, self.analysis)
        new_row = self.grid_size()[1]
        filter.grid(row=new_row, column=0, sticky=tk.E)
    
    def remove_filter(self, filter_a):
        # row_a = filter_a.grid_info()['row']
        filter_a.destroy()
        if len(self.winfo_children()) > 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(row=i)
        else:
            self.parent.reset_filter_or_frame()

    def get_filters(self):
        filters = []
        for filter in self.winfo_children():
            filters.append(filter.get_filter())
        return filters

class Filter(tk.Frame):
    def __init__(self, parent, analysis):
        super().__init__(parent)
        self.analysis = analysis
        
        remove = tk.Button(self, text='X', command=lambda: parent.remove_filter(self))
        remove.grid(row=0, column=0)
        
        add = tk.Button(self, text='+', command=parent.add_filter)
        add.grid(row=0, column=1)

        params = ['type','sub_type'] + sorted(set(self.analysis.data.columns).difference(['type','sub_type']))
        self.param_select = tk.StringVar()
        self.param_select.set(params[0])
        param = tk.OptionMenu(self, self.param_select, *params, command=self.param_changed)
        param.config(width=20)
        param.grid(row=0, column=2)
        
        functions = [
            '==',
            '!=',
            '>',
            '<',
            '>=',
            '<=',
        ]
        self.function_select = tk.StringVar()
        self.function_select.set(functions[0])
        function = tk.OptionMenu(self, self.function_select, *functions)
        function.config(width=3)
        function.grid(row=0, column=3)

        values = sorted(self.analysis.data['type'].dropna().unique())
        self.value_select = tk.StringVar()
        self.value_select.set(values[0])
        self.value = tk.OptionMenu(self, self.value_select, *values)
        self.value.config(width=30)
        self.value.grid(row=0, column=5)

    def param_changed(self, param):
        values = sorted(self.analysis.data[param].dropna().unique())
        self.value.destroy()
        if len(values) == 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(column=i)
        elif len(values) <= 200:
            self.value_select.set(values[0])
            self.value = tk.OptionMenu(self, self.value_select, *values)
            self.value.config(width=30)
            self.value.grid(row=0, column=5)
        else:
            self.value = tk.Entry(self, width=37)
            self.value.get
            self.value.grid(row=0, column=5)

    def get_filter(self):
        column = self.param_select.get()
        function = self.function_select.get()
        if isinstance(self.value, tk.Entry):
            value = self.value.get()
        else:
            value = self.value_select.get()
        return (column, function, value)

class Filters_old(tk.Frame):
    def __init__(self, parent, analysis):
        super().__init__(parent, highlightbackground="grey", highlightthickness=2)
        self.analysis = analysis

    def add(self):
        filter = Filter(self, self.analysis)
        new_row = self.grid_size()[1]
        filter.grid(row=new_row, column=0, sticky=tk.W+tk.E)

    def remove(self, filter_a):
        row_a = filter_a.grid_info()['row']
        filter_a.destroy()
        for i, widget in enumerate(self.winfo_children()):
            widget.grid_configure(row=i)

    def move_up(self, filter_a):
        row_a = filter_a.grid_info()['row']
        if row_a == 0: return
        row_b = row_a - 1
        for filter_b in self.winfo_children():
            if filter_b.grid_info()['row'] == row_b:
                filter_a.grid_remove()
                filter_b.grid_remove()
                filter_a.grid(row=row_b, column=0)
                filter_b.grid(row=row_a, column=0)
                break


    def move_down(self, filter_a):
        row_a = filter_a.grid_info()['row']
        row_last = self.grid_size()[1]-1
        if row_a == row_last: return
        row_b = row_a + 1
        for filter_b in self.winfo_children():
            if filter_b.grid_info()['row'] == row_b:
                filter_a.grid_remove()
                filter_b.grid_remove()
                filter_a.grid(row=row_b, column=0)
                filter_b.grid(row=row_a, column=0)
                break

    def get_tickers(self):
        filter_settings = {}
        for filter in self.winfo_children():
            row = filter.grid_info()['row']
            filter_settings[row] = filter.get_filter_settings()
        
        # create filter
        filter = pd.Series(True, index=self.analysis.data.index)
        for row in sorted(filter_settings):
            column = filter_settings[row][0]
            function = filter_settings[row][1]
            value = filter_settings[row][2]
            if value.isnumeric():
                value = int(value)
            elif value.replace('.', '').isnumeric():
                value = float(value)
            
            if function == '==':
                filter = filter & (self.analysis.data[column] == value)
        print(self.analysis.data[filter])

class Filter_old(tk.Frame):
    def __init__(self, parent, analysis):
        super().__init__(parent)
        self.analysis = analysis

        self.up = tk.Button(self, text='↑', command=lambda: parent.move_up(self))
        self.up.grid(row=0, column=0)
        
        self.down = tk.Button(self, text='↓', command=lambda: parent.move_down(self))
        self.down.grid(row=0, column=1)
        
        self.remove = tk.Button(self, text='X', command=lambda: parent.remove(self))
        self.remove.grid(row=0, column=2)

        params = ['type','sub_type'] + sorted(set(self.analysis.data.columns).difference(['type','sub_type']))
        self.param_select = tk.StringVar()
        self.param_select.set(params[0])
        self.param = tk.OptionMenu(self, self.param_select, *params, command=self.param_changed)
        self.param.config(width=20)
        self.param.grid(row=0, column=3)

        functions = [
            '==',
            '!=',
            '>',
            '<',
            '>=',
            '<=',
        ]
        self.function_select = tk.StringVar()
        self.function_select.set(functions[0])
        self.function = tk.OptionMenu(self, self.function_select, *functions)
        self.function.config(width=3)
        self.function.grid(row=0, column=4)

        values = sorted(self.analysis.data['type'].dropna().unique())
        self.value_select = tk.StringVar()
        self.value_select.set(values[0])
        self.value = tk.OptionMenu(self, self.value_select, *values)
        self.value.config(width=30)
        self.value.grid(row=0, column=5)

    def param_changed(self, param):
        values = sorted(self.analysis.data[param].dropna().unique())
        self.value.destroy()
        if len(values) == 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(column=i)
        elif len(values) <= 200:
            self.value_select.set(values[0])
            self.value = tk.OptionMenu(self, self.value_select, *values)
            self.value.config(width=30)
            self.value.grid(row=0, column=5)
        else:
            self.value = tk.Entry(self, width=37)
            self.value.get
            self.value.grid(row=0, column=5)

    def get_filter_settings(self):
        column = self.param_select.get()
        function = self.function_select.get()
        if isinstance(self.value, tk.Entry):
            value = self.value.get()
        else:
            value = self.value_select.get()
        return (column, function, value)
            
