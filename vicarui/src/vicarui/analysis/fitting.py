from collections import deque
from typing import Optional, Dict, Tuple

import numpy as np
from matplotlib.pyplot import Rectangle, Line2D, Axes
from sklearn.linear_model import RANSACRegressor, LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures


def reg_to_title(regressor, prefix: str) -> str:
    from .tex import sci_4
    a = regressor.coef_[2]
    a = sci_4(a, plus_sign=True) + r"\cdot x^2"
    b = regressor.coef_[1]
    b = sci_4(b, plus_sign=True) + r"\cdot x"
    c = regressor.intercept_
    c = sci_4(c, plus_sign=True)
    return fr"{prefix} ${a}{b}{c}$"


def additional_info(a: float, b: float, c: float, m: float, n: float, p: float) -> Tuple[str, np.ndarray]:
    from .tex import sci_4
    out = "  "
    x_val = -0.5 * (n - b) / (m - a)
    d = (m - a) * np.power(x_val, 2) + (n - b) * x_val + p - c
    out += r"    $\Delta_{max}=" f" {sci_4(d)}, x={x_val:3.2f}$"
    eq = [m - a, n - b, p - c]
    roots = np.roots(eq)
    if len(roots) == 2 and np.alltrue(np.isreal(roots)):
        integral = 1 / 3 * (m - a) * (
                np.power(roots[0], 3) - np.power(roots[1], 3)
        ) + 1 / 2 * (n - b) * (
                           np.power(roots[0], 2) - np.power(roots[1], 2)
                   ) + (p - c) * (
                           roots[0] - roots[1]
                   )
        out += fr"  $\int\Delta={sci_4(integral)}, x_0={roots[1]:3.2f}, x_1={roots[0]:3.2f}$"
    return out, roots


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

    def fit(self, x_start: int, x_end: int, in_kwargs: Dict, out_kwargs: Dict) -> Dict:
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

        from sklearn.metrics import mean_squared_error

        # BG
        bg_reg = RANSACRegressor(random_state=0, max_trials=1000, base_estimator=LinearRegression())
        pipe = make_pipeline(PolynomialFeatures(self.degree), bg_reg)
        pipe.fit(x_out, y_out)
        pred_y_out = pipe.predict(nx_out[..., None])
        bg_title = reg_to_title(bg_reg.estimator_, 'BG:')

        m, n, p = bg_reg.estimator_.coef_[2], bg_reg.estimator_.coef_[1], bg_reg.estimator_.intercept_

        # FG
        fg_reg = LinearRegression(n_jobs=-1)
        pipe = make_pipeline(PolynomialFeatures(self.degree), fg_reg)
        pipe.fit(x_in, y_in)

        a, b, c = fg_reg.coef_[2], fg_reg.coef_[1], fg_reg.intercept_
        add, roots = additional_info(a, b, c, m, n, p)

        if len(roots) == 2 and np.alltrue(np.isreal(roots)):
            nx_in = np.linspace(roots[1], roots[0])
        else:
            nx_in = np.arange(x_in[0], x_in[-1], 0.25)

        pred_y_in = pipe.predict(nx_in[..., None])
        fg_title = reg_to_title(fg_reg, 'FIT:')

        from .tex import sci_4
        fg_mse = f'${sci_4(mean_squared_error(y_in, pipe.predict(x_in)))}$'

        bg_mse = (
                f'${sci_4(mean_squared_error(y_out, pipe.predict(x_out)))}$'
                + add
        )

        return {
            'BG': {
                'out': (x_out[np.logical_not(bg_reg.inlier_mask_)], y_out[np.logical_not(bg_reg.inlier_mask_)]),
                'title': bg_title,
                'line': Line2D(nx_out, pred_y_out, **out_kwargs),
                'mse': bg_mse
            },
            'FIT': {
                'title': fg_title,
                'line': Line2D(nx_in, pred_y_in, **in_kwargs),
                'mse': fg_mse
            }
        }
