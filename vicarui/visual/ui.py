import tkinter as tk
from tkinter import messagebox

import matplotlib.pyplot as plt
from astropy.visualization import ImageNormalize, ZScaleInterval, HistEqStretch
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from filelist import FileList

import vicarutil as vu


def _print():
    print("working")


if __name__ == '__main__':
    root: tk.Tk = tk.Tk()
    root.title("VicarUI")
    root.geometry("640x480")

    fig: plt.Figure = plt.figure()
    im = fig.add_subplot(111)


    def imshow(file):
        vd = vu.read_image(file)
        im.imshow(
            vd.data[0],
            cmap="gray",
            norm=ImageNormalize(interval=ZScaleInterval(), stretch=HistEqStretch(vd.data[0]))
        )
        canvas.draw()


    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            plt.close("all")
            root.destroy()


    fl = FileList(root)
    fl.grid(row=0, column=0, sticky="nsew")
    fl.set_show_call(imshow)

    panel: tk.Frame = tk.Frame(root)
    panel.grid(row=0, column=1, sticky="nsew")

    root.grid_columnconfigure(0, weight=30, minsize=200)
    root.grid_columnconfigure(1, weight=70)
    root.grid_rowconfigure(0, weight=1)

    root.grid_rowconfigure(0, )

    canvas = FigureCanvasTkAgg(fig, master=panel)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
