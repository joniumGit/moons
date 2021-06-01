from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np
from matplotlib.pyplot import Rectangle, Line2D, Axes
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import PolynomialFeatures

from .second_degree import additional_2nd_deg_info, roots_2nd_deg
from ...support import Pipe, ransac


@dataclass(frozen=True)
class Result:
    equation: np.ndarray
    title: str = ""
    additional: str = ""
    mse: Optional[float] = None
    line: Optional[Line2D] = None
    outliers: Tuple[np.ndarray, np.ndarray] = None


def reg_to_title(reg: Pipe, prefix: str) -> str:
    return fr"{prefix} {reg.poly_str}"


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

    def _collect_data(self, x_start: float, x_end: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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

        x_in = np.asarray(x_in)
        x_out = np.asarray(x_out)
        y_in = np.asarray(y_in)
        y_out = np.asarray(y_out)

        return x_in, x_out, y_in, y_out

    def _bg(self, min_samples: int):
        return Pipe(
            transforms=[PolynomialFeatures(self.degree, include_bias=False)],
            reg=ransac(min_samples=min_samples, max_iter=100)
        )

    def _fg(self):
        return Pipe(transforms=[PolynomialFeatures(self.degree, include_bias=False)])

    def _pipes(self, x_start: float, x_end: float, full: bool = True) -> Union[
        Tuple[Pipe, Pipe, np.ndarray, np.ndarray, float, float, Tuple[np.ndarray, np.ndarray]],
        Tuple[Pipe, Pipe],
    ]:
        x_in, x_out, y_in, y_out = self._collect_data(x_start, x_end)

        bg = self._bg(int(np.sqrt(len(y_out))))
        fg = self._fg()
        bg.line.fit(x_out[..., None], y_out)
        fg.line.fit(x_in[..., None], y_in)

        if full:
            nx_out: np.ndarray
            nx_in: np.ndarray

            nx_out = np.linspace(x_out[0], x_out[-1], num=np.max((100, len(x_out) // 2)))
            num_in = np.max((100, len(x_in) // 2))
            if self.degree == 2:
                roots = roots_2nd_deg(bg.eq, fg.eq)
                if len(roots) == 2 and np.alltrue(np.isreal(roots)):
                    nx_in = np.linspace(roots[1], roots[0], num=num_in)
                else:
                    nx_in = np.linspace(x_in[0], x_in[-1], num=num_in)
            else:
                nx_in = np.linspace(x_in[0], x_in[-1], num=num_in)

            mse_bg = mean_squared_error(y_out, bg.line.predict(x_out[..., None]))
            mse_fg = mean_squared_error(y_in, bg.line.predict(x_in[..., None]))

            outliers = np.logical_not(bg.reg.inlier_mask_)
            outliers: Tuple[np.ndarray, np.ndarray] = (x_out[outliers], y_out[outliers])

            return bg, fg, nx_out, nx_in, mse_bg, mse_fg, outliers
        else:
            return bg, fg

    def fit(
            self,
            x_start: float,
            x_end: float,
            in_kwargs=None,
            out_kwargs=None,
            simple: bool = False
    ) -> Tuple[Result, Result]:
        if simple:
            bg, fg = self._pipes(x_start, x_end, full=False)
            return Result(equation=bg.eq), Result(equation=fg.eq)
        else:
            if out_kwargs is None:
                out_kwargs = dict()
            if in_kwargs is None:
                in_kwargs = dict()

            bg: Pipe
            fg: Pipe
            bg, fg, nx_out, nx_in, bg_mse, fg_mse, outliers = self._pipes(x_start, x_end)

            if self.degree == 2:
                add, _ = additional_2nd_deg_info(bg, fg)
            else:
                add = ''

            bg_title = reg_to_title(bg, 'BG: ')
            fg_title = reg_to_title(fg, 'FIT:')

            return Result(
                equation=bg.eq,
                title=bg_title,
                mse=bg_mse,
                line=Line2D(nx_out, bg.line.predict(nx_out[..., None]), **out_kwargs),
                additional=add,
                outliers=outliers
            ), Result(
                equation=fg.eq,
                title=fg_title,
                mse=fg_mse,
                line=Line2D(nx_in, fg.line.predict(nx_in[..., None]), **in_kwargs)
            )
