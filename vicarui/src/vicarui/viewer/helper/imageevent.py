from typing import Tuple, Callable

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, MouseButton
from matplotlib.ticker import FuncFormatter, AutoMinorLocator

from ...analysis import DataPacket
from ...logging import log
from ...support import sci_4, sci_n


class VicarEvent:
    line_has_data: bool = False
    fit_x_start: int = -1
    fit_x_end: int = -1
    fit_degree: int = 2
    dpkt: DataPacket

    def __init__(self, data: np.ndarray, data_axis: Axes, line_axis: Axes, area: Callable[[], Tuple[int, int]]):
        self.data = data
        self.area = area

        from ...support import wrap_axes

        self.data_axis = wrap_axes(data_axis)
        self.line_axis = wrap_axes(line_axis)

        self.cid = data_axis.figure.canvas.mpl_connect('button_press_event', self)
        self.dpkt = DataPacket(data)

        self.outliers = list()
        self.rect = None
        self.redraw = False

    def data_axis_handler(self, x: float, y: float, btn: MouseButton):
        self.clear_line_soft()
        if self.rect:
            self.rect.remove()
            self.rect = None
        if btn in {MouseButton.LEFT, MouseButton.RIGHT}:
            width = self.area()[0]
            window = self.area()[1]
            row = int(y)
            col = int(x)
            log.debug(f"Click detected at {row},{col}")
            self.dpkt.configure(width, window, 2)
            vertical = btn == MouseButton.RIGHT
            if self.line_axis.axes_modifier is not None:
                self.line_axis.axes_modifier(self.line_axis, vertical=vertical)
            r = self.dpkt.select(
                col,
                row,
                vertical=vertical,
                lw=1,
                fill=False,
            )
            if btn == MouseButton.LEFT:
                r.set_color('b')
                self.line_axis.set_left(f"HORIZONTAL slice with HEIGHT: {row - width} <= y <= {row + width}")
                self.dpkt.scatter(self.line_axis, s=8, c='b')
            else:
                r.set_color('r')
                self.line_axis.set_left(f"VERTICAL slice with WIDTH: {col - width} <= x <= {col + width}")
                self.dpkt.scatter(self.line_axis, s=8, c='r')
            self.rect = self.data_axis.add_patch(r)
            self.line_has_data = True
        else:
            self.line_has_data = False
        if self.redraw:
            self.line_axis.refresh()
            self.redraw = False

    def _fit(self):
        bg, fg = self.dpkt.fit(
            self.fit_x_start,
            self.fit_x_end,
            in_kwargs={'color': 'black', 'linewidth': 3},
            out_kwargs={'color': 'gray', 'linewidth': 3}
        )

        self.line_axis.append_left(
            fg.title
            + fr' mse: ${sci_4(fg.mse)}$'
            + fg.additional
            + '\n'
            + bg.title
            + fr' mse: ${sci_4(bg.mse)}$'
            + bg.additional
        )

        self.line_axis.add_line(fg.line)
        self.line_axis.add_line(bg.line)
        if bg.outliers is not None:
            self.outliers.append(
                self.line_axis.scatter(
                    *bg.outliers,
                    c='white',
                    s=4,
                    marker='.'
                )
            )
        if fg.outliers is not None:
            self.outliers.append(
                self.line_axis.scatter(
                    *fg.outliers,
                    c='white',
                    s=4,
                    marker='.'
                )
            )

    def __call__(self, event: MouseEvent):
        if event.canvas.cursor().shape() != 0:
            return
        if event.inaxes == self.line_axis and self.line_has_data:
            self.redraw = True
            for outlier in self.outliers:
                outlier.remove()
            self.outliers.clear()
            if event.button == MouseButton.LEFT and self.fit_x_start == -1 and self.fit_x_end == -1:
                self.fit_x_start = event.xdata
                self.line_axis.set_left(self.line_axis.get_first_left())
                self.line_axis.append_left("set end ")
            elif event.button == MouseButton.LEFT and self.fit_x_end == -1:
                self.fit_x_end = event.xdata
                if self.fit_x_start == self.fit_x_end:
                    return
                elif self.fit_x_end < self.fit_x_start:
                    temp = self.fit_x_end
                    self.fit_x_end = self.fit_x_start
                    self.fit_x_start = temp
                self.line_axis.set_left(self.line_axis.get_first_left())
                self._fit()
            else:
                if event.button == MouseButton.LEFT:
                    self.fit_x_start = event.xdata
                    self.line_axis.set_left(self.line_axis.get_first_left())
                    self.line_axis.append_left("set end ")
                else:
                    self.fit_x_start = -1
                    self.line_axis.set_left(self.line_axis.get_first_left())
                    self.line_axis.append_left("set start ")
                self.fit_x_end = -1
                self.line_axis.clear_lines()
        elif event.inaxes == self.data_axis:
            self.data_axis_handler(event.xdata, event.ydata, event.button)
        if self.redraw:
            self.line_axis.refresh()
            self.redraw = False

    def clear_line_soft(self):
        self.redraw = True
        self.line_axis.clear()
        self.line_axis.grid(alpha=0.4)
        self.line_axis.grid(which='minor', linestyle='--', alpha=0.2)
        ax2 = self.line_axis.secondary_yaxis(location="right")
        ax2.set_yticklabels([])
        ax2.yaxis.set_minor_locator(AutoMinorLocator(4))
        self.line_axis.minorticks_on()
        self.line_axis.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${sci_n(x, 1)}$"))

    def clear_line(self):
        self.clear_line_soft()
        self.line_has_data = False
        self.fit_x_start = -1
        self.fit_x_end = -1
        self.rect = None
        self.outliers.clear()

    def detach(self):
        try:
            self.data_axis.figure.canvas.mpl_disconnect(self.cid)
        except Exception as e:
            log.exception("Exception in detach", exc_info=e)
