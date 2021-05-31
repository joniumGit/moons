from collections import deque
from typing import Optional, Dict

import numpy as np
from matplotlib.pyplot import Rectangle, Line2D, Axes
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import PolynomialFeatures

from .pipe import Pipe, ransac
from .second_degree import additional_2nd_deg_info


def reg_to_title(reg: Pipe, prefix: str) -> str:
    return fr"{prefix} ${reg.poly_str}$"


class DataPacket(object):
    __slots__ = 'data', 'x_data', 'y_data', 'width', 'window', 'degree', 'x_max', 'y_max', 'vertical'

    data: np.ndarray

    x_data: Optional[np.ndarray]
    y_data: Optional[np.ndarray]

    x_max: int
    y_max: int

    width: int
    window: int
    degree: int

    def __init__(self, data: np.ndarray):
        super(DataPacket, self).__init__()
        self.data = data

        self.x_max = len(data[0]) - 1
        self.y_max = len(data) - 1

        self.x_data = None
        self.y_data = None

        self.vertical = False

    def configure(self, width: int = 0, window: int = 100, degree: int = 2):
        self.width = width
        self.window = window
        self.degree = degree

    def select(self, x: int, y: int, vertical: bool = False, **kwargs) -> Rectangle:
        if vertical:
            xs = max(0, y - self.window)
            xe = min(self.y_max, y + self.window + 1)
            self.x_data = np.arange(xs, xe, 1)
            self.y_data = np.average(
                self.data[xs:xe, max(0, x - self.width):min(self.x_max, x + self.width + 1)],
                axis=1
            )
            self.vertical = True
            return Rectangle(
                (max(0, x - self.width), xs),
                min(self.x_max, x + self.width + 1) - max(0, x - self.width) - 1,
                xe - xs - 1,
                **kwargs
            )
        else:
            xs = max(0, x - self.window)
            xe = min(self.x_max, x + self.window + 1)
            self.x_data = np.arange(xs, xe, 1)
            self.y_data = np.average(
                self.data[max(0, y - self.width):min(self.y_max, y + self.width + 1), xs:xe].T,
                axis=1
            )
            self.vertical = False
            return Rectangle(
                (xs, max(0, y - self.width)),
                xe - xs - 1,
                min(self.y_max, y + self.width + 1) - max(0, y - self.width) - 1,
                **kwargs
            )

    def scatter(self, ax: Axes, **kwargs):
        ax.scatter(self.x_data, self.y_data, **kwargs)

    def fit(self, x_start: float, x_end: float, in_kwargs=None, out_kwargs=None, suppress: bool = False) -> Dict:
        if out_kwargs is None:
            out_kwargs = dict()
        if in_kwargs is None:
            in_kwargs = dict()
        x_in = deque()
        y_in = deque()

        x_out = deque()
        y_out = deque()

        for x, y in zip(self.x_data, self.y_data):
            if x_start <= x <= x_end:
                x_in.append(x)
                y_in.append(y)
            else:
                x_out.append(x)
                y_out.append(y)

        nx_out = np.arange(x_out[0], x_out[-1], 0.25)

        x_in = np.asarray(x_in)[..., None]
        x_out = np.asarray(x_out)[..., None]
        y_in = np.asarray(y_in)
        y_out = np.asarray(y_out)

        # BG
        bg = Pipe(
            transforms=[PolynomialFeatures(self.degree, include_bias=False)],
            reg=ransac(min_samples=int(np.sqrt(len(y_out))))
        )
        pipe = bg.line.fit(x_out, y_out)
        pred_y_out = pipe.predict(nx_out[..., None])

        # FG
        fg = Pipe(transforms=[PolynomialFeatures(self.degree, include_bias=False)])
        pipe = fg.line.fit(x_in, y_in)

        if self.degree == 2:
            add, roots = additional_2nd_deg_info(bg, fg, suppress)
            if len(roots) == 2 and np.alltrue(np.isreal(roots)):
                nx_in = np.linspace(roots[1], roots[0])
            else:
                nx_in = np.arange(x_in[0], x_in[-1], 0.25)
        else:
            add = ''
            nx_in = np.arange(x_in[0], x_in[-1], 0.25)

        pred_y_in = pipe.predict(nx_in[..., None])

        from .tex import sci_4
        bg_title = reg_to_title(bg, 'BG: ')
        fg_title = reg_to_title(fg, 'FIT:')

        fg_mse = f'${sci_4(mean_squared_error(y_in, pipe.predict(x_in)))}$'
        bg_err = sci_4(mean_squared_error(y_out, pipe.predict(x_out)))
        bg_mse = f'${bg_err}$' + add

        return {
            'BG': {
                'out': (x_out[np.logical_not(bg.reg.inlier_mask_)], y_out[np.logical_not(bg.reg.inlier_mask_)]),
                'title': bg_title,
                'line': Line2D(nx_out, pred_y_out, **out_kwargs),
                'mse': bg_mse,
                'equation': bg.eq
            },
            'FIT': {
                # 'out': (x_in[np.logical_not(fg.reg.inlier_mask_)], y_in[np.logical_not(fg.reg.inlier_mask_)]),
                'title': fg_title,
                'line': Line2D(nx_in, pred_y_in, **in_kwargs),
                'mse': fg_mse,
                'equation': fg.eq
            }
        }
