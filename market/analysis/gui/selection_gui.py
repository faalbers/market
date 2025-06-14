import tkinter as tk
from tkinter import ttk
from pprint import pp

class Analysis_Selection_GUI(tk.Toplevel):
    def __init__(self, parent, symbols):
        super().__init__(parent)
        self.analysis = parent.analysis
        self.symbols = symbols
        self.data = self.analysis.data.loc[self.symbols].reset_index() # this creates a copy

        self.title('Market Analysis Selection (%s)' % self.data.shape[0])

        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview', fieldbackground="#593C3C")

        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(padx=10,pady=10, fill=tk.BOTH, expand=True)

        self.tree_refresh()

    def tree_refresh(self):
        for widget in self.tree_frame.winfo_children():
            widget.destroy()

        tree_scroll = tk.Scrollbar(self.tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=tree_scroll.set, selectmode='extended')
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        columns = self.data.columns.tolist()
        self.tree['columns'] = self.data.columns.tolist()
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.heading('#0', text='', anchor=tk.W)
        
        for column in columns:
            self.tree.column(column, anchor=tk.W, width=120)
            self.tree.heading(column, text=column, anchor=tk.W, command = lambda _col=column: self.sort_tree(_col, False))

        for symbol, row in self.data.iterrows():
            self.tree.insert('', 'end', values=list(row.values))

    def sort_tree(self, column, reverse):
        self.data.sort_values(by=column, ascending=not reverse, inplace=True)
        self.tree_refresh()
        self.tree.heading(column, command=lambda _col=column: self.sort_tree(_col, not reverse))
