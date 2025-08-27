import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from ...tickers import Tickers
from ...analysis import Analysis
from .selection_gui import Analysis_Selection_GUI
import pandas as pd
from pprint import pp
import pickle

class Analysis_GUI(tk.Tk):
    def __init__(self, symbols=[], update=False, forced=False, cache_update=False):
        super().__init__()
        self.analysis = Analysis(symbols)
        self.analysis_data = self.analysis.get_data()

        if self.analysis_data.empty:
            print('No data available to analyse')
            return
        
        # self.option_add("*Font", ("Helvetica", 14))
        # self.option_add("*FontSize", 18)
        # self.option_add("*Dialog.msg.font", ("Helvetica", 14))
        self.__build_gui()
        self.mainloop()

    def __build_gui(self):
        self.title('Market Analysis')

        # action buttons frame
        frame_actions = tk.Frame(self)
        frame_actions.pack(anchor='w', fill='x', padx=10, pady=10)

        # filters frame
        self.frame_filters = Frame_Filters(self)
        self.frame_filters.pack(anchor='w', padx=10, pady=10)

        # add actions
        self.button_add_filter = tk.Button(frame_actions, text='Add Filter', command=self.frame_filters.add_frame_filter)
        self.button_add_filter.pack(side='left')
        self.button_save_filters = tk.Button(frame_actions, text='Save Filters', command=self.save_filters)
        self.button_save_filters.pack(side='left')
        self.button_load_filters = tk.Button(frame_actions, text='Load Filters', command=self.load_filters)
        self.button_load_filters.pack(side='left')
        tk.Frame(frame_actions).pack(side='left', expand=True)
        
        analyse = tk.Button(frame_actions, text='Analyse', command=self.analyze)
        analyse.pack(side='right')

        self.resize_window()

    def resize_window(self):
        self.update_idletasks()
        height = self.frame_filters.winfo_reqheight() + 70
        self.geometry(f"700x{height}")

    def reset_frame_filters(self):
        self.frame_filters.destroy()
        
        self.frame_filters = Frame_Filters(self)
        self.button_add_filter.config(command=self.frame_filters.add_frame_filter)
        self.frame_filters.pack(anchor='w', padx=10, pady=10)

        self.resize_window()

    def save_filters(self):
        filters = self.frame_filters.get_filters()
        if len(filters) == 0:
            messagebox.showinfo('Save Filters', 'No filters to save')
        else:
            file = filedialog.asksaveasfile(filetypes=[('FILTER', '*.filt')], defaultextension='.filt', mode='wb')
            if file != None:
                pickle.dump(filters, file, protocol=pickle.HIGHEST_PROTOCOL)
                file.close()
    
    def load_filters(self):
        file = filedialog.askopenfile(filetypes=[('FILTER', '*.filt')], defaultextension='.filt', mode='rb')
        if file != None:
            filters = pickle.load(file)
            file.close()
            self.reset_frame_filters()
            self.frame_filters.set_filters(filters)

    def get_filtered(self):
        filters = self.frame_filters.get_filters()
        select = pd.Series(True, index=self.analysis_data.index)
        columns = set()
        for filter in filters:
            or_filters = [filter['and']] + filter['or']
            or_select = pd.Series(False, index=self.analysis_data.index)
            for or_filter in or_filters:
                column = or_filter[0]
                columns.add(column)
                function = or_filter[1]
                value = or_filter[2]
                if value.isnumeric():
                    value = int(value)
                elif value.replace('.', '').isnumeric():
                    value = float(value)
                
                if column == self.analysis_data.index.name:
                    test_series = self.analysis_data.index
                else:
                    test_series = self.analysis_data[column]
                
                if function == '==':
                    or_select = or_select | (test_series == value)
                
                if function == '!=':
                    or_select = or_select | (test_series != value)
                    
                if function == '>':
                    or_select = or_select | (test_series > value)
                    
                if function == '<':
                    or_select = or_select | (test_series < value)
                    
                if function == '>=':
                    or_select = or_select | (test_series >= value)
                    
                if function == '<=':
                    or_select = or_select | (test_series <= value)
                    
                if function == 'contains':
                    or_select = or_select | (test_series.str.lower().str.contains(value.lower().replace('^', r'\^')))
                    
                if function == 'startswith':
                    or_select = or_select | (test_series.str.lower().str.startswith(value.lower()))
                    
                if function == 'endswith':
                    or_select = or_select | (test_series.str.lower().str.endswith(value.lower()))
                    
                if function == 'isna':
                    or_select = or_select | (test_series.isna())
                    
                if function == 'notna':
                    or_select = or_select | (test_series.notna())
                    
            select = select & or_select

        return (self.analysis_data[select].index, columns)
    
    def analyze(self):
        symbols, columns = self.get_filtered()
        if len(columns) == 0:
            columns = ['symbol','name']
        else:
            columns.discard('symbol')
            columns.discard('name')
            columns = ['symbol','name'] + [c for c in self.analysis_data.columns if c in columns]
        Analysis_Selection_GUI(self, symbols, columns)

class Frame_Filters(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.analysis_data = parent.analysis_data
        self.parent = parent

    def add_frame_filter(self, filter={'and': (), 'or': []}):
        # add filter to filters
        frame_filter = Frame_Filter(self, filter)
        new_row = self.grid_size()[1]
        frame_filter.grid(row=new_row, column=0, sticky=tk.W)
        self.parent.resize_window()

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
    
    def set_filters(self, filters):
        for filter in filters:
            self.add_frame_filter(filter)

    def resize_window(self):
        self.parent.resize_window()

class Frame_Filter(tk.Frame):
    def __init__(self, parent, filter={'and': (), 'or': []}):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.analysis_data = parent.analysis_data
        self.parent = parent

        # make wide enough se we can see hierachy of or filters
        self.grid_columnconfigure(0, minsize=650)

        # as filter AND to filter
        self.filter = Filter(self, filter['and'])
        self.filter.grid(row=0, column=0, sticky=tk.W)

        # add OR filters frame to filter
        self.frame_filter_or = Frame_Filter_OR(self, filter['or'])
        self.frame_filter_or.grid(row=1, column=0, sticky=tk.E)

    def add_filter(self):
        self.frame_filter_or.add_filter()
        self.parent.resize_window()
    
    def remove_filter(self, filter_a):
        self.parent.remove_frame_filter(self)
        self.parent.resize_window()
    
    def reset_frame_filter_or(self):
        self.frame_filter_or.destroy()
        self.frame_filter_or = Frame_Filter_OR(self)
        self.frame_filter_or.grid(row=1, column=0, sticky=tk.E)

    def get_filter(self):
        filter = {}
        filter['and'] = self.filter.get_filter()
        filter['or'] = self.frame_filter_or.get_filters()
        return filter

    def resize_window(self):
        self.parent.resize_window()
    
class Frame_Filter_OR(tk.Frame):
    def __init__(self, parent, filters=[]):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.analysis_data = parent.analysis_data
        self.parent = parent
        for filter in filters:
            self.add_filter(filter)
    
    def add_filter(self, filter=()):
        filter = Filter(self, filter)
        new_row = self.grid_size()[1]
        filter.grid(row=new_row, column=0, sticky=tk.E)
        self.parent.resize_window()
    
    def remove_filter(self, filter_a):
        filter_a.destroy()
        if len(self.winfo_children()) > 0:
            for i, widget in enumerate(self.winfo_children()):
                widget.grid_configure(row=i)
        else:
            self.parent.reset_frame_filter_or()
        self.parent.resize_window()

    def get_filters(self):
        filters = []
        for filter in self.winfo_children():
            filters.append(filter.get_filter())
        return filters

class Filter(tk.Frame):
    def __init__(self, parent, filter=()):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.analysis_data = parent.analysis_data
        self.parent = parent

        # remove filter from parentbutton
        remove = tk.Button(self, text='X', command=lambda: parent.remove_filter(self))
        remove.grid(row=0, column=0)

        # add filter to parent button
        add = tk.Button(self, text='+', command=parent.add_filter)
        add.grid(row=0, column=1)

        # # add param option menu
        # params = [self.analysis_data.index.name] + ['type','sub_type'] + sorted(set(self.analysis_data.columns).difference(['type','sub_type']))
        # # params = ['type','sub_type'] + sorted(set(self.analysis_data.columns).difference(['type','sub_type']))
        # self.param_select = tk.StringVar()
        # if len(filter) > 0:
        #     self.param_select.set(filter[0])
        # else:
        #     self.param_select.set(params[0])
        # param = tk.OptionMenu(self, self.param_select, *params, command=self.param_changed)
        # param.config(width=25)
        # param.grid(row=0, column=2)

        # add param option menu
        first_params = ['type','sub_type', 'sector', 'industry']
        params = [self.analysis_data.index.name] + first_params + sorted(set(self.analysis_data.columns).difference(first_params))
        self.param_select = tk.StringVar()
        if len(filter) > 0:
            self.param_select.set(filter[0])
        else:
            self.param_select.set(params[0])
        # self.param_last = self.param_select
        self.param_select.trace('w', self.param_changed)
        self.param = ttk.Combobox(self, textvariable=self.param_select, values=params, width=45, state='readonly')
        self.param_shift = False
        self.param_last = self.param_select.get()
        self.param.grid(row=0, column=2)

        # add function option menu
        functions = [
            '==',
            '!=',
            '>',
            '<',
            '>=',
            '<=',
            'contains',
            'startswith',
            'endswith',
            'isna',
            'notna',
        ]
        self.function_select = tk.StringVar()
        if len(filter) > 0:
            self.function_select.set(filter[1])
        else:
            self.function_select.set(functions[0])
        function = tk.OptionMenu(self, self.function_select, *functions, command=self.function_changed)
        function.config(width=7)
        function.grid(row=0, column=3)

        # add value option menu
        self.value_select = tk.StringVar()
        if len(filter) > 0:
            self.value = tk.Entry(self, width=37)
            self.value.insert(tk.END, filter[2])
            self.value.grid(row=0, column=5)
        else:
            self.value = None
            self.param_changed(self.param_select.get())

    def param_changed(self, *args):
        if not isinstance(self.value, type(None)):
            self.value.destroy()
            self.value = None
        function = self.function_select.get()
        param = self.param_select.get()
        self.param_last = param
        if param == self.analysis_data.index.name:
            values = sorted(self.analysis_data.index)
        else:
            values = sorted(self.analysis_data[param].dropna().unique())
        # if len(values) == 0:
        #     for i, widget in enumerate(self.winfo_children()):
        #         widget.grid_configure(column=i)
        
        if function in ['contains', 'startswith', 'endswith']:
            self.value = tk.Entry(self, width=37)
            self.value.grid(row=0, column=5)
        elif len(values) <= 200:
            if isinstance(values[0], str):
                self.value_select.set(values[0])
                self.value = ttk.Combobox(self, textvariable=self.value_select, values=values, width=30, state='readonly')
                self.value.grid(row=0, column=5)
            else:
                self.value = tk.Entry(self, width=37)
                self.value.grid(row=0, column=5)
        else:
            self.value = tk.Entry(self, width=37)
            self.value.grid(row=0, column=5)

    def function_changed(self, function):
        self.param_changed(self.param_select.get())

    def get_filter(self):
        column = self.param_select.get()
        function = self.function_select.get()
        if isinstance(self.value, tk.Entry):
            value = self.value.get()
        else:
            value = self.value_select.get()
        return (column, function, value)

