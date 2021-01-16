import os
import tkinter as tk
from tkinter.filedialog import askdirectory


class FileList(tk.Frame):

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.__make()
        self.list: tk.Listbox

    def __make(self):
        bf: tk.Frame = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
        bf.pack(fill=tk.X, expand=True, anchor=tk.N + tk.W)
        tk.Button(bf, text="Select", command=self.__select).grid(row=0, column=0)
        tk.Button(bf, text="Load", command=self.__load).grid(row=0, column=1)
        tk.Label(self, text="Images").pack(anchor=tk.W)
        self.list = tk.Listbox(self)
        self.list.pack(expand=True, fill=tk.BOTH, anchor=tk.N + tk.W)

    def __select(self):
        print("select")
        dir = askdirectory()
        self.list.delete(0, tk.END)
        img = []
        lbl = []
        i = 0
        for f in os.listdir(dir):
            if f.lower().endswith('.lbl'):
                lbl.append(f)
            if f.lower().endswith('.img'):
                img.append(f)
                self.list.insert(i, f)
                i += 1
        print("Images:")
        print(img)
        print("Labels:")
        print(lbl)

    def __load(self):
        print("load")
