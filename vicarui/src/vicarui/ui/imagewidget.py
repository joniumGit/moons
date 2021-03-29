from pathlib import Path
from typing import Callable

from PySide2 import QtWidgets as qt
from astropy.visualization import ImageNormalize, ZScaleInterval, HistEqStretch
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavBar
from matplotlib.figure import Figure

from vicarutil.image import VicarImage, read_image


class FigureWrapper(FigureCanvasQTAgg):

    def __init__(self, width=7.5, height=7.5, dpi=125):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes: Axes = self.fig.add_subplot(111)
        super(FigureWrapper, self).__init__(self.fig)
        self.axes.set_title("Image View")

    def clear(self):
        self.fig.clf(keep_observers=True)
        self.axes: Axes = self.fig.add_subplot(111)
        self.axes.invert_yaxis()

    def show_image(self, image: VicarImage):
        self.axes.imshow(image.data[0],
                         norm=ImageNormalize(interval=ZScaleInterval(), stretch=HistEqStretch(image.data[0])),
                         cmap="gray")
        self.axes.invert_yaxis()
        self.draw()


class PlotWidget(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)
        self.fig = FigureWrapper()
        self.tools = NavBar(self.fig, self)

        self.frame = qt.QFrame()
        sub_layout = qt.QVBoxLayout()
        sub_layout.addWidget(self.fig)
        self.frame.setMinimumWidth(700)
        self.frame.setMinimumHeight(700)
        self.frame.setLayout(sub_layout)

        layout = qt.QVBoxLayout()
        layout.addWidget(self.frame)
        layout.addWidget(self.tools)

        self.setLayout(layout)

    def show_image(self, image: VicarImage):
        self.fig.clear()
        self.fig.show_image(image)

    def init_vicar_callback(self) -> Callable[[Path], None]:
        return lambda p: self.show_image(read_image(p))


class StretchWidget(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(StretchWidget, self).__init__(*args, **kwargs)


class IntervalWidget(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(IntervalWidget, self).__init__(*args, **kwargs)
