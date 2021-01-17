import os
import sys
import tkinter as tk
from tkinter.filedialog import askdirectory
from typing import Callable, Optional


class FileList(tk.Frame):

    def __init__(self, master: tk.Tk):
        super().__init__(master)
        self.__make()
        self.__img_list: tk.Listbox
        self.__lbl_list: tk.Listbox
        self.__current_dir: str
        self.__show_call: Optional[Callable] = None

    def __make(self):
        bf: tk.Frame = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
        bf.grid(row=0, column=0, sticky="nw")

        tk.Button(bf, text="Select", command=self.__select).grid(row=0, column=0)
        tk.Button(bf, text="Load", command=self.__load).grid(row=0, column=1)
        tk.Button(bf, text="Show label", command=self.__show_lbl).grid(row=0, column=2)

        tk.Label(self, text="Images").grid(row=1, column=0, sticky="nw", ipadx=2, ipady=2)

        self.__img_list = tk.Listbox(self, selectmode=tk.SINGLE, bg="gray")
        self.__img_list.grid(row=2, column=0, sticky="nsew")

        tk.Label(self, text="Labels").grid(row=3, column=0, sticky="nw")

        self.__lbl_list = tk.Listbox(self, selectmode=tk.SINGLE, bg="gray")
        self.__lbl_list.grid(row=4, column=0, sticky="nsew", ipadx=2, ipady=2)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(4, weight=1)

    def __select(self):
        _dir = askdirectory(initialdir=sys.argv[0][0:sys.argv[0].rindex('/')])
        if _dir == '':
            return
        self.__current_dir = _dir
        self.__img_list.delete(0, tk.END)
        img = 0
        lbl = 0
        for f in os.listdir(_dir):
            if f.lower().endswith('.lbl'):
                self.__lbl_list.insert(img, f)
                lbl += 1
            if f.lower().endswith('.img'):
                self.__img_list.insert(img, f)
                img += 1

    def __load(self):
        if self.__show_call is not None:
            if len(self.__img_list.curselection()) != 0:
                self.__show_call(self.__current_dir + "/" + self.__img_list.selection_get())

    def set_show_call(self, value: Callable):
        self.__show_call = value

    def __show_lbl(self):
        pass
