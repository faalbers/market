import tkinter as tk
from ...tickers import Tickers
from ...analysis import Analysis
from .selection_gui import Analysis_Selection_GUI
import pandas as pd
from pprint import pp

class Analysis_GUI(tk.Tk):
    def __init__(self, symbols=[]):
        super().__init__()
        self.tickers = Tickers(symbols)
        self.analysis = Analysis(self.tickers)
        self.__build_gui()
        self.mainloop()

    def __build_gui(self):
        # self.geometry('550x100')
        self.title('Market Analysis')

        # action buttons frame
        frame_actions = tk.Frame(self)
        frame_actions.pack(anchor='w', padx=10, pady=10)

        # filters frame
        self.frame_filters = Frame_Filters(self)
        self.frame_filters.pack(anchor='w', padx=10, pady=10)

        # add actions
        self.button_add_filter = tk.Button(frame_actions, text='Add Filter', command=self.frame_filters.add_frame_filter)
        self.button_add_filter.grid(row=0, column=0)
        analyse = tk.Button(frame_actions, text='Analyse', command=self.analyze)
        analyse.grid(row=0, column=1)
        frame_empty = tk.Frame(frame_actions, width=400)
        frame_empty.grid(row=0, column=2)

    def reset_frame_filters(self):
        self.frame_filters.destroy()
        self.frame_filters = Frame_Filters(self)
        self.button_add_filter.config(command=self.frame_filters.add_frame_filter)
        self.frame_filters.pack(anchor='w', padx=10, pady=10)

    def get_filtered(self):
        filters = self.frame_filters.get_filters()
        select = pd.Series(True, index=self.analysis.data.index)
        for filter in filters:
            or_filters = [filter['and']] + filter['or']
            or_select = pd.Series(False, index=self.analysis.data.index)
            for or_filter in or_filters:
                column = or_filter[0]
                function = or_filter[1]
                value = or_filter[2]
                if value.isnumeric():
                    value = int(value)
                elif value.replace('.', '').isnumeric():
                    value = float(value)
                
                if function == '==':
                    or_select = or_select | (self.analysis.data[column] == value)
                
                if function == '!=':
                    or_select = or_select | (self.analysis.data[column] != value)
                    
                if function == '>':
                    or_select = or_select | (self.analysis.data[column] > value)
                    
                if function == '<':
                    or_select = or_select | (self.analysis.data[column] < value)
                    
                if function == '>=':
                    or_select = or_select | (self.analysis.data[column] >= value)
                    
                if function == '<=':
                    or_select = or_select | (self.analysis.data[column] <= value)
                    
            select = select & or_select

        return self.analysis.data[select].index
    
    def analyze(self):
        print('analyze')
        symbols = self.get_filtered()
        Analysis_Selection_GUI(self, symbols)

class Frame_Filters(tk.Frame):
    def __init__(self, parent):
        # super().__init__(parent, highlightbackground="#70B41C", highlightthickness=2)
        super().__init__(parent)
        self.analysis = parent.analysis
        self.parent = parent

    def add_frame_filter(self):
        # add filter to filters
        frame_filter = Frame_Filter(self)
        new_row = self.grid_size()[1]
        frame_filter.grid(row=new_row, column=0, sticky=tk.W)

    def remove_frame_filter(self, frame_filter_a):
        frame_filter_a.destroy()
        if len(self.winfo_children()) > 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(row=i)
        else:
            self.parent.reset_frame_filters()

    def get_filters(self):
        filters = []
        for frame_filter in self.winfo_children():
            filters.append(frame_filter.get_filter())
        return filters

class Frame_Filter(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.parent = parent

        # make wide enough se we can see hierachy of or filters
        self.grid_columnconfigure(0, minsize=530)

        # as filter AND to filter
        self.filter = Filter(self)
        self.filter.grid(row=0, column=0, sticky=tk.W)

        # add OR filters frame to filter
        self.frame_filter_or = Frame_Filter_OR(self)
        self.frame_filter_or.grid(row=1, column=0, sticky=tk.E)

    def add_filter(self):
        self.frame_filter_or.add_filter()
    
    def remove_filter(self, filter_a):
        self.parent.remove_frame_filter(self)
    
    def reset_frame_filter_or(self):
        self.frame_filter_or.destroy()
        self.frame_filter_or = Frame_Filter_OR(self)
        self.frame_filter_or.grid(row=1, column=0, sticky=tk.E)

    def get_filter(self):
        filter = {}
        filter['and'] = self.filter.get_filter()
        filter['or'] = self.frame_filter_or.get_filters()
        return filter

class Frame_Filter_OR(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.parent = parent
    
    def add_filter(self):
        filter = Filter(self)
        new_row = self.grid_size()[1]
        filter.grid(row=new_row, column=0, sticky=tk.E)
    
    def remove_filter(self, filter_a):
        filter_a.destroy()
        if len(self.winfo_children()) > 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(row=i)
        else:
            self.parent.reset_frame_filter_or()

    def get_filters(self):
        filters = []
        for filter in self.winfo_children():
            filters.append(filter.get_filter())
        return filters

class Filter(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.analysis = parent.analysis

        # remove filter from parentbutton
        remove = tk.Button(self, text='X', command=lambda: parent.remove_filter(self))
        remove.grid(row=0, column=0)

        # add filter to parent button
        add = tk.Button(self, text='+', command=parent.add_filter)
        add.grid(row=0, column=1)

        # add param option menu
        params = ['type','sub_type'] + sorted(set(self.analysis.data.columns).difference(['type','sub_type']))
        self.param_select = tk.StringVar()
        self.param_select.set(params[0])
        param = tk.OptionMenu(self, self.param_select, *params, command=self.param_changed)
        param.config(width=20)
        param.grid(row=0, column=2)

        # add function option menu
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

        # add value option menu
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
