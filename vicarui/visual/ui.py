import tkinter as tk
from filelist import FileList


def _print():
    print("working")


if __name__ == '__main__':
    root: tk.Tk = tk.Tk()
    root.title("VicarUI")
    root.geometry("640x480")
    tk.Button(root, text="Btn", command=_print).pack()
    tk.Button(root, text="Exit", command=root.destroy).pack()
    tk.Frame(root).pack(fill=tk.BOTH, expand=True)
    FileList(root).pack(fill=tk.BOTH, anchor=tk.S)
    root.mainloop()
