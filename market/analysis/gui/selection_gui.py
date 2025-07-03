import tkinter as tk
from tkinter import ttk
from pprint import pp
import numpy as np
from .charts_gui import Charts_GUI

class Analysis_Selection_GUI(tk.Toplevel):
    def __init__(self, parent, symbols, columns):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.symbols = symbols
        self.data = self.analysis.data.loc[self.symbols].reset_index() # this also creates a copy

        self.title('Market Analysis Selection (%s)' % len(symbols))

        # add data view
        self.frame_data = Frame_Data_Tree(self, self.data, columns)
        self.frame_data.pack(padx=10,pady=10, fill=tk.BOTH, expand=True)

        # action buttons frame
        frame_actions = tk.Frame(self)
        # frame_actions.pack(anchor='w', padx=10, pady=10)
        frame_actions.pack(padx=10,pady=10, fill=tk.BOTH, expand=True)

        # add actions
        action_a = tk.Button(frame_actions, text='Charts', command=self.charts)
        action_a.grid(row=0, column=0)
        # action_b = tk.Button(frame_actions, text='Charts Sectors', command=self.charts_sectors)
        # action_b.grid(row=0, column=1)

    def charts(self):
        symbols = self.frame_data.get_symbols()
        if len(symbols) == 0: return
        Charts_GUI(self, symbols)

    # def charts_sectors(self):
    #     symbols = self.frame_data.get_symbols()
    #     if len(symbols) == 0: return
    #     Charts_Sectors_Compare_GUI(self, symbols)

    def action_b(self):
        print('Action B')

class Frame_Data_Tree(tk.Frame):
    def __init__(self, parent, data, columns):
        super().__init__(parent, highlightbackground="#4232F7", highlightthickness=2)
        self.parent = parent
        self.data = data
        
        scroll_columns = {c: (c in columns) for c in self.data.columns}
        self.frame_scroll_columns = Frame_Scroll_Columns(self, scroll_columns)
        self.frame_scroll_columns.pack(side='left', fill=tk.BOTH)

        self.frame_tree = Frame_Tree(self, self.data, columns)
        self.frame_tree.pack(side='left', fill=tk.BOTH, expand=True)

    def columns_changed(self, columns):
        self.frame_tree.change_columns(columns)

    def get_symbols(self):
        return self.frame_tree.get_symbols()

class Frame_Tree(tk.Frame):
    def __init__(self, parent, data, columns):
        super().__init__(parent)
        self.parent = parent
        self.data = data
        self.columns = list(columns)
        self.sort_list = []
        self.sort_descending = False
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview', fieldbackground="#593C3C")

        self.tree_refresh()

    def tree_refresh(self):
        # self.sort_list = []
        # self.sort_descending = False
        for widget in self.winfo_children():
            widget.destroy()

        tree_scroll = tk.Scrollbar(self)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(self, yscrollcommand=tree_scroll.set, selectmode='extended')
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.tree['columns'] = self.columns
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.heading('#0', text='', anchor=tk.W)

        # Bind Ctrl+A to select all
        self.tree.bind('<Control-a>', self.select_all)
        self.tree.bind('<Key>', self.key_pressed)
        self.tree.bind('<KeyRelease>', self.key_released)
        if len(self.columns) > 0:
            column_width = int(1200 / len(self.columns))
            for column in self.columns:
                self.tree.column(column, anchor=tk.W, width=column_width)
                # self.tree.heading(column, text=column, anchor=tk.W, command = lambda _col=column: self.sort_tree_new(_col, False))
                self.tree.heading(column, text=column, anchor=tk.W, command = lambda _col=column: self.sort_tree(_col))

            for symbol, row in self.data[self.columns].iterrows():
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

    def key_pressed(self, event):
        if event.char == '-': self.sort_descending = True

    def key_released(self, event):
        if event.char == '-': self.sort_descending = False

    def sort_tree(self, column):
        sort_descending = self.sort_descending
        
        # reset header names
        for sort_column in self.sort_list: self.tree.heading(column, text=sort_column)
        
        if column in self.sort_list:
            self.sort_list.remove(column)
        else:
            self.sort_list.append(column)
        
        # sort and set header names
        if len(self.sort_list) > 0:
            sort_descending = self.sort_descending
            self.data.sort_values(by=self.sort_list, ascending=not self.sort_descending, inplace=True)
            self.tree_refresh()

            for i, column in enumerate(self.sort_list):
                sign = '+'
                if sort_descending: sign = '-'
                new_text = '%s %s(%s)' % (column, sign, i)
                self.tree.heading(column, text=new_text)

    def change_columns(self, columns):
        self.columns = columns
        self.sort_list = []
        self.sort_descending = False
        self.tree_refresh()

    def get_symbols(self):
        symbols = []
        for selected_item in self.tree.selection():
            data = self.tree.item(selected_item, 'values')
            symbols.append(data[0])
        return symbols

class Frame_Scroll_Columns(ttk.Frame):
    def __init__(self, parent, columns):
        super().__init__(parent)
        self.parent = parent

        self.canvas = tk.Canvas(self)
        self.canvas.pack(side='left', fill='both')

        self.frame_checkboxes = tk.Frame(self)
        self.canvas.create_window((0,0), window=self.frame_checkboxes, anchor='nw')

        widest_check = 0
        height_check = 0
        self.columns_state = {}
        for column in columns:
            self.columns_state[column] = tk.IntVar()
            self.columns_state[column].set(1)
            check_button = tk.Checkbutton(self.frame_checkboxes, text=column,
                variable=self.columns_state[column], command=self.check_changed)
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
            current_column = event.widget.cget('text')
            state_inverse = abs((self.columns_state[current_column].get())-1)
            for column, column_state in self.columns_state.items():
                if column == current_column: continue
                column_state.set(state_inverse)
    
    def check_changed(self):
        self.parent.columns_changed(self.get_columns())
    
    def get_columns(self):
        return [column for column, column_state in self.columns_state.items() if column_state.get() == 1]

