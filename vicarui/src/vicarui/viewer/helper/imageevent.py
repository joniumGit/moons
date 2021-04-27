from typing import Tuple

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, MouseButton

from ...analysis import DataPacket
from ...support import logging as log


class VicarEvent:
    line_has_data: bool = False
    fit_x_start: int = -1
    fit_x_end: int = -1
    fit_degree: int = 2
    dpkt: DataPacket

    TITLE_ARGS = {'loc': 'left', 'fontsize': 'small', 'pad': 2, 'fontfamily': 'monospace'}

    def __init__(self, data: np.ndarray, data_axis: Axes, line_axis: Axes, area: Tuple[int, int]):
        self.data = data
        self.area = area
        self.data_axis = data_axis
        self.line_axis = line_axis
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
            title = self.line_axis.get_title(loc='left').split("\n")[0]
            if event.button == MouseButton.LEFT and self.fit_x_start == -1 and self.fit_x_end == -1:
                self.fit_x_start = event.xdata
                self.line_axis.set_title(title + " \nset end ", **VicarEvent.TITLE_ARGS)
            elif event.button == MouseButton.LEFT and self.fit_x_end == -1:
                self.fit_x_end = event.xdata
                if self.fit_x_start == self.fit_x_end:
                    return
                elif self.fit_x_end < self.fit_x_start:
                    temp = self.fit_x_end
                    self.fit_x_end = self.fit_x_start
                    self.fit_x_start = temp

                self.line_axis.set_title(title, **VicarEvent.TITLE_ARGS)

                d = self.dpkt.fit(
                    self.fit_x_start,
                    self.fit_x_end,
                    in_kwargs={'color': 'black', 'linewidth': 3},
                    out_kwargs={'color': 'gray', 'linewidth': 3}
                )

                self.line_axis.set_title(
                    self.line_axis.get_title(loc='left')
                    + '\n'
                    + d['FIT']['title'] + fr' mse: {d["FIT"]["mse"]}'
                    + '\n'
                    + d['BG']['title'] + fr' mse: {d["BG"]["mse"]}',
                    **VicarEvent.TITLE_ARGS
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

                self.line_axis.figure.canvas.draw()
            else:
                if event.button == MouseButton.LEFT:
                    self.fit_x_start = event.xdata
                    self.line_axis.set_title(title + "\nset end ", **VicarEvent.TITLE_ARGS)
                else:
                    self.fit_x_start = -1
                    self.line_axis.set_title(title + "\nset start ", **VicarEvent.TITLE_ARGS)
                self.fit_x_end = -1
                if len(self.line_axis.lines) != 0:
                    self.line_axis.lines.pop(1)
                    self.line_axis.lines.pop(0)
            self.line_axis.figure.canvas.draw()
        elif event.inaxes == self.data_axis:
            self.line_axis.clear()
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
                r = self.dpkt.select(
                    col,
                    row,
                    vertical=event.button == MouseButton.RIGHT,
                    lw=1,
                    fill=False,
                )
                if event.button == MouseButton.LEFT:
                    r.set_color('b')
                    self.line_axis.set_title(
                        f"HORIZONTAL slice with HEIGHT: {row - width} <= y <= {row + width}",
                        **VicarEvent.TITLE_ARGS
                    )
                    self.dpkt.scatter(self.line_axis, s=8, c='b')
                else:
                    r.set_color('r')
                    self.line_axis.set_title(
                        f"VERTICAL slice with WIDTH: {col - width} <= x <= {col + width}",
                        **VicarEvent.TITLE_ARGS
                    )
                    self.dpkt.scatter(self.line_axis, s=8, c='r')
                self.rect = self.data_axis.add_patch(r)
                self.line_has_data = True
            else:
                self.line_has_data = False
            self.line_axis.figure.canvas.draw()
            self.line_axis.figure.canvas.flush_events()

    def clear_line(self):
        self.line_axis.clear()
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
