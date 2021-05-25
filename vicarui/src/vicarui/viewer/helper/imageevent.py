from typing import Tuple

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, MouseButton

from ...analysis import DataPacket
from ...support import log


class VicarEvent:
    line_has_data: bool = False
    fit_x_start: int = -1
    fit_x_end: int = -1
    fit_degree: int = 2
    dpkt: DataPacket

    def __init__(self, data: np.ndarray, data_axis: Axes, line_axis: Axes, area: Tuple[int, int]):
        self.data = data
        self.area = area

        from ...support import wrap_axes

        self.data_axis = wrap_axes(data_axis)
        self.line_axis = wrap_axes(line_axis)

        self.cid = data_axis.figure.canvas.mpl_connect('button_press_event', self)
        self.dpkt = DataPacket(data)

        self.err = None
        self.rect = None

    def __call__(self, event: MouseEvent):
        if event.canvas.cursor().shape() != 0:
            return
        if event.inaxes == self.line_axis and self.line_has_data:
            if self.err:
                self.err.remove()
                self.err = None
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

                d = self.dpkt.fit(
                    self.fit_x_start,
                    self.fit_x_end,
                    in_kwargs={'color': 'black', 'linewidth': 3},
                    out_kwargs={'color': 'gray', 'linewidth': 3}
                )

                self.line_axis.append_left(
                    d['FIT']['title']
                    + fr' mse: {d["FIT"]["mse"]}'
                    + '\n'
                    + d['BG']['title'] + fr' mse: {d["BG"]["mse"]}'
                )

                self.line_axis.add_line(d['FIT']['line'])
                self.line_axis.add_line(d['BG']['line'])
                self.err = self.line_axis.scatter(
                    d['BG']['out'][0],
                    d['BG']['out'][1],
                    c='white',
                    s=4,
                    marker='.'
                )

                self.line_axis.refresh()
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
            self.line_axis.figure.canvas.draw()
        elif event.inaxes == self.data_axis:
            self.clear_line_soft()
            if self.rect:
                self.rect.remove()
                self.rect = None
            if event.button in {MouseButton.LEFT, MouseButton.RIGHT}:
                width = self.area[0]
                window = self.area[1]
                row = int(event.ydata)
                col = int(event.xdata)
                log.debug(f"Click detected at {row},{col}")
                self.dpkt.configure(width, window, 2)
                vertical = event.button == MouseButton.RIGHT
                if self.line_axis.axes_modifier is not None:
                    self.line_axis.axes_modifier(self.line_axis, vertical=vertical)
                r = self.dpkt.select(
                    col,
                    row,
                    vertical=vertical,
                    lw=1,
                    fill=False,
                )
                if event.button == MouseButton.LEFT:
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
            self.line_axis.refresh()

    def clear_line_soft(self):
        self.line_axis.clear()
        self.line_axis.secondary_yaxis(location="right")

    def clear_line(self):
        self.clear_line_soft()
        self.line_has_data = False
        self.fit_x_start = -1
        self.fit_x_end = -1
        self.rect = None
        self.err = None

    def detach(self):
        try:
            self.data_axis.figure.canvas.mpl_disconnect(self.cid)
        except Exception as e:
            log.exception("Exception in detach", exc_info=e)
