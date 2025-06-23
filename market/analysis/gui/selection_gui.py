import tkinter as tk
from tkinter import ttk
from pprint import pp
import numpy as np

class Analysis_Selection_GUI(tk.Toplevel):
    def __init__(self, parent, symbols, columns):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.symbols = symbols
        self.data = self.analysis.data.loc[self.symbols].reset_index() # this also creates a copy

        self.title('Market Analysis Selection (%s)' % len(symbols))

        # add data view
        frame_data = Frame_Data_Tree(self, self.data, columns)
        frame_data.pack(padx=10,pady=10, fill=tk.BOTH, expand=True)

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

class Frame_Scroll_Columns(ttk.Frame):
    def __init__(self, parent, columns):
        super().__init__(parent)
        self.parent = parent

        scrollbar = ttk.Scrollbar(self, orient='vertical')
        scrollbar.pack(side='right', fill='y', expand=False)
        canvas = tk.Canvas(self,
            bd=0,
            highlightthickness=0,
            width=200,
            yscrollcommand=scrollbar.set
        )
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=canvas.yview)

        interior = Frame_Columns(self, columns)
        interior.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        interior_id = canvas.create_window(0, 0, window=interior, anchor='nw')

    def columns_changed(self, columns):
        self.parent.columns_changed(columns)

class Frame_Columns(tk.Frame):
    def __init__(self, parent, columns):
        super().__init__(parent)
        self.parent = parent
        self.from_widget = None
        self.to_widget = None

        self.colums_state = {}
        for column, state in columns.items():
            self.colums_state[column] = tk.IntVar()
            if state: self.colums_state[column].set(1)
            check_button = tk.Checkbutton(self, text=column, variable=self.colums_state[column], command=self.check_changed)
            # check_button.focus_force()
            new_row = self.grid_size()[1]
            check_button.grid(row=new_row, column=0, sticky=tk.W)
            check_button.bind('<ButtonPress-1>', self.check_pressed)
            check_button.bind('<B1-Motion>', self.check_motion)
            check_button.bind('<ButtonRelease-1>', self.check_released)
            # check_button.bind('<Control-a>', self.check_all)
        self.dummy = tk.Frame(self)
        self.dummy.grid(row=new_row+1, column=0)

    def check_pressed(self, event):
        self.from_widget = event.widget
        self.to_widget = event.widget
        self.from_widget.focus_set()

    def check_motion(self, event):
        x = event.x_root - self.winfo_rootx()
        y = event.y_root - self.winfo_rooty()
        self.to_column, self.to_row = self.grid_location(x, y)
        for widget in self.winfo_children():
            info = widget.grid_info()
            if info["row"] == self.to_row and info["column"] == self.to_column:
                if widget != self.to_widget:
                    self.to_widget = widget
                    self.from_widget.config(bg='yellow')
                    self.to_widget.focus_set()
                return

    def check_released(self, event):
        self.from_widget.config(bg='SystemButtonFace')
        self.dummy.focus_set()
        if self.from_widget != self.to_widget:
            from_row = self.from_widget.grid_info()['row']
            to_row = self.to_widget.grid_info()['row']
            self.from_widget.grid_forget()
            self.to_widget.grid_forget()
            self.from_widget.grid(row=to_row, column=0, sticky=tk.W)
            self.to_widget.grid(row=from_row, column=0, sticky=tk.W)
            self.check_changed()
        elif event.state & 0x0001:
            # With shift , change state of them
            current_column = self.from_widget.cget('text')
            current_column_state_inverse = abs((self.colums_state[current_column].get())-1)
            for column, column_state in self.colums_state.items():
                if column == current_column: continue
                column_state.set(current_column_state_inverse)
    
    def check_changed(self):
        columns = {}
        for widget in self.winfo_children():
            if not isinstance(widget, tk.Checkbutton): continue
            column = widget.cget('text')
            if self.colums_state[column].get() == 0: continue
            columns[widget.grid_info()['row']] = widget.cget('text')
        columns = [columns[x] for x in sorted(columns)]
        self.parent.columns_changed(columns)
