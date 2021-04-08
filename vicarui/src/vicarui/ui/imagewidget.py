from pathlib import Path
from typing import Callable, Optional

import numpy as np
from PySide2 import QtWidgets as qt
from astropy.visualization import ImageNormalize, ZScaleInterval, HistEqStretch
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavBar
from matplotlib.figure import Figure
from vicarutil.analysis import set_info, br_reduction
from vicarutil.image import VicarImage, read_image

from ..support import logging as log


class VicarEvent:

    def __init__(self, data: np.ndarray, data_axis: Axes, line_axis: Axes):
        self.data = data
        self.data_axis = data_axis
        self.line_axis = line_axis
        self.cid = data_axis.figure.canvas.mpl_connect('button_press_event', self)

    def __call__(self, event: MouseEvent):
        if event.inaxes == self.data_axis:
            width = 1
            window = 100
            row = int(event.ydata)
            col = int(event.xdata)
            row_max = len(self.data) - 1
            col_max = len(self.data[0]) - 1
            log.debug(f"Click detected at {row},{col}")
            if width <= row <= row_max - width and width <= col <= col_max - width:
                if event.button == MouseButton.LEFT:
                    self.line_axis.clear()
                    self.line_axis.set_title(f"{row - width} <= y <= {row + width}")
                    start = max(0, col - window)
                    end = min(col_max, col + window) + 1
                    x = np.arange(start, end, 1)
                    y = np.average(
                        self.data[row - width:row + width, start:end].T,
                        axis=1
                    )
                    self.line_axis.scatter(x, y, s=8, c='b')
                elif event.button == MouseButton.RIGHT:
                    self.line_axis.clear()
                    self.line_axis.set_title(f"{col - width} <= x <= {col + width}")
                    start = max(0, row - window)
                    end = min(row_max, row + window) + 1
                    x = np.arange(start, end, 1)
                    y = np.average(
                        self.data[start:end, col - width:col + width],
                        axis=1
                    )
                    self.line_axis.scatter(x, y, s=8, c='r')
                else:
                    self.line_axis.clear()
            else:
                self.line_axis.clear()
            self.line_axis.figure.canvas.draw()
            self.line_axis.figure.canvas.flush_events()

    def detach(self):
        try:
            self.data_axis.figure.canvas.mpl_disconnect(self.cid)
        except Exception as e:
            log.exception("Exception in detach", exc_info=e)


class FigureWrapper(FigureCanvasQTAgg):
    event_handler: Optional[VicarEvent] = None

    def __init__(self, width=7.5, height=7.5, dpi=125):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(FigureWrapper, self).__init__(self.fig)

    def clear(self):
        if self.event_handler is not None:
            self.event_handler.detach()
            self.event_handler = None
        self.fig.clf(keep_observers=True)

    def show_image(self, image: VicarImage):
        data_axis: Axes = self.fig.add_subplot(3, 3, (2, 6))
        og_axis = self.fig.add_subplot(331)
        bg_axis = self.fig.add_subplot(334)
        line_axis = self.fig.add_subplot(3, 3, (7, 9))

        data_axis.set_title("reduced + HistEQ")
        og_axis.set_title("original")
        bg_axis.set_title("background")
        line_axis.set_title("line")

        try:
            title = set_info(image, axes=data_axis)
            self.fig.suptitle(title)
        except Exception as e:
            log.exception("Failed to set info", exc_info=e)

        data, mask = br_reduction(image)
        og_axis.imshow(image.data[0], cmap="gray")
        bg_axis.imshow(mask, cmap="coolwarm")

        normalizer = ImageNormalize(
            interval=ZScaleInterval(),
            stretch=HistEqStretch(data)
        )
        data_axis.imshow(
            data,
            norm=normalizer,
            cmap="gray",
            aspect="equal"
        )
        data_axis.minorticks_on()

        for x in self.fig.axes:
            if x != line_axis:
                x.invert_yaxis()

        data = normalizer(data)

        self.event_handler = VicarEvent(data, data_axis, line_axis)
        self.figure.set_tight_layout('true')
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
