import tkinter as tk
from tkinter import messagebox
from typing import Optional

import matplotlib.pyplot as plt
from astropy.visualization import ImageNormalize, ZScaleInterval, HistEqStretch, BaseStretch
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import vicarutil as vu
from filelist import FileList
from vicarui.stretch.stretchers import make_panel, get_stretch


def _print():
    print("working")


def run():
    root: tk.Tk = tk.Tk()
    root.title("VicarUI")
    root.geometry("1080x480")

    fl = FileList(root)
    fl.grid(row=0, column=0, sticky="nsew")

    fig: plt.Figure = plt.figure()
    stretch_pane, o = make_panel(root)

    def imshow(file):
        vd = vu.read_image(file)
        fig.clf(keep_observers=True)
        im = fig.add_subplot(111)
        st: Optional[BaseStretch] = None
        try:
            st = get_stretch(o, vd.data[0])
        except Exception as e:
            pass
        if st is not None:
            im.imshow(
                vd.data[0],
                cmap="gray",
                norm=ImageNormalize(interval=ZScaleInterval(), stretch=st)
            )
        else:
            im.imshow(
                vd.data[0],
                cmap="gray",
                norm=ImageNormalize(interval=ZScaleInterval())
            )
        canvas.draw()

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            plt.close("all")
            root.destroy()

    fl.set_show_call(imshow)
    stretch_pane.grid(row=0, column=1, sticky="nsew")

    panel: tk.Frame = tk.Frame(root)
    panel.grid(row=0, column=2, sticky="nsew")

    root.grid_columnconfigure(0, weight=15, minsize=200)
    root.grid_columnconfigure(1, weight=15, minsize=300)
    root.grid_columnconfigure(2, weight=70)
    root.grid_rowconfigure(0, weight=1)

    canvas = FigureCanvasTkAgg(fig, master=panel)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == '__main__':
    import cProfile

    cProfile.run('run()')
