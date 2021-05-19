from collections import Generator
from dataclasses import dataclass
from typing import Any, NoReturn, Callable, Optional

from .config import *
from .funcs import norm
from .helpers import ImageHelper, Transformer
from ...fitting import DataPacket
from ...wrapper import ImageWrapper

INTEGRAL_PX = "i-px"
INTEGRAL_SHADOW = "i-sh"
INTEGRAL_TARGET = "i-tg"

CONTRAST_PX = "c-px"
CONTRAST_SHADOW = "c-sh"
CONTRAST_TARGET = "c-tg"


@dataclass(frozen=False)
class Selection:
    initial_position: Tuple[float, float]
    is_vertical: bool
    shadow_radius: float
    width: int
    window: int
    length: int


@dataclass(frozen=True)
class Fit:
    arg_max: float
    contrast: float
    integral: float
    distance_px: Tuple[float, float]

    def is_finite(self):
        return np.alltrue(np.isfinite([self.contrast, self.integral]))

    def __getitem__(self, i: int):
        if i == 0:
            return self.contrast
        elif i == 1:
            return self.integral
        elif i == 2:
            return self.distance_px
        else:
            return self.arg_max


class AutoFit:
    packet: DataPacket
    start_x: int
    start_y: int

    def __init__(self, packet: DataPacket):
        self.packet = packet
        self.start_x = 0
        self.start_y = 0

    def select(self, x: int, y: int, vertical: bool = False) -> Any:
        return self.packet.select(x, y, vertical)

    def fit(self, x: float, y: float) -> Fit:
        data = self.packet.fit(x, y)
        bg = data['BG']['equation']
        fg = data['FIT']['equation']
        from ...fitting import contrast_2nd_deg, integrate_2nd_deg
        x_val, contrast = contrast_2nd_deg(bg, fg)
        integral = integrate_2nd_deg(bg, fg)
        dist_px = (self.start_x - x, self.start_y - y)
        return Fit(
            arg_max=x_val,
            contrast=contrast,
            integral=integral,
            distance_px=dist_px
        )


class FitHelper:

    def __init__(self, image: ImageWrapper, helper: ImageHelper):
        self.data = image.get_processed()
        self.packet = DataPacket(self.data)
        self.autofit = AutoFit(self.packet)
        self.shadow = norm(Transformer(SATURN_FRAME, helper.frame, helper.time_et)(
            helper.pos_in_sat(SUN_ID, helper.target_id()))
        )[0:2]
        self.im_helper = helper

    def __call__(self, s: Selection) -> Generator[Tuple[Any, Fit]]:
        self.packet.configure(s.width, s.window)

        iterations = s.length
        radius = s.shadow_radius
        vertical = s.is_vertical

        shadow = self.shadow
        initial = s.initial_position
        start_x = int(initial[0])
        start_y = int(initial[1])

        autofit = self.autofit
        autofit.start_x = start_x
        autofit.start_y = start_y

        if vertical:
            for i in range(
                    int(initial[0]),
                    int(initial[0] + iterations * np.sign(shadow[0])),
                    int(1 * np.sign(shadow[0]))
            ):
                rect = autofit.select(int(initial[0]), int(initial[1]), vertical)
                fit = autofit.fit(initial[1] - radius, initial[1] + radius)
                yield rect, fit
                initial = (i, initial[1] + shadow[1] * np.abs(1 / shadow[0]))
        else:
            for i in range(
                    int(initial[1]),
                    int(initial[1] + iterations * np.sign(shadow[1])),
                    int(1 * np.sign(shadow[1]))
            ):
                rect = autofit.select(int(initial[0]), int(initial[1]))
                fit = autofit.fit(initial[0] - radius, initial[0] + radius)
                yield rect, fit
                initial = (initial[0] + shadow[0] * np.abs(1 / shadow[1]), i)


def show(
        helper: ImageHelper,
        results: Generator[Fit],
        plots: Dict,
        func_fwd: Callable[[float], float] = np.reciprocal,
        func_bwd: Optional[Callable[[float], float]] = None
) -> NoReturn:
    from matplotlib.pyplot import Axes
    from sklearn.preprocessing import FunctionTransformer
    from sklearn.pipeline import make_pipeline, Pipeline
    from sklearn.linear_model import HuberRegressor
    from sklearn.metrics import mean_squared_error
    from typing import cast

    @dataclass(frozen=False)
    class Pipe:
        line: Pipeline
        color: str
        style: str
        title: str = ""

    plots = cast(Dict[str, Axes], plots)
    pipes = [
        Pipe(
            color="yellow",
            style="-",
            line=make_pipeline(FunctionTransformer(np.reciprocal), HuberRegressor())
        ),
        Pipe(
            color="magenta",
            style="-",
            line=make_pipeline(FunctionTransformer(np.log1p, np.expm1), HuberRegressor())
        ),
        Pipe(
            color="cyan",
            style="-",
            line=make_pipeline(FunctionTransformer(func_fwd, func_bwd), HuberRegressor())
        ),
    ]

    fits = list()
    for fit in results:
        if fit.is_finite():
            fits.append(fit)

    px_dist = np.asarray([fit[2] for fit in fits])
    tgt_size = helper.per_px(helper.size_at_target)
    sh_size = helper.per_px(helper.size_at_shadow)
    dists = [
        np.asarray([np.sqrt(np.sum(np.power(np.multiply(d, tgt_size), 2))) for d in px_dist]),
        np.asarray([np.sqrt(np.sum(np.power(np.multiply(d, sh_size), 2))) for d in px_dist])
    ]

    contrast = np.asarray([fit[0] for fit in fits])
    integral = np.asarray([fit[1] for fit in fits])

    p = iter([plots[CONTRAST_TARGET], plots[INTEGRAL_TARGET], plots[CONTRAST_SHADOW], plots[INTEGRAL_SHADOW]])

    def plot_(x_, dist_, data_):
        ax: Axes = p.__next__()
        ax.scatter(dist_, data_, c="gray", s=8)
        from ...tex import sci_4
        for pipe in pipes:
            try:
                pipe.line.fit(dist_[..., None], data_)
                y = pipe.line.predict(x_[..., None])
                mse = mean_squared_error(data_, pipe.line.predict(dist_[..., None]))
                ax.plot(x_, y, color=pipe.color, linestyle=pipe.style, label=pipe.title + f" mse: ${sci_4(mse)}$")
            except Exception as e:
                log.exception("Failed a regression analysis", exc_info=e)
        try:
            ax.set_ylim(np.percentile(data_, 2), np.percentile(data_, 98))
        except ValueError:
            pass

    for dist in dists:
        x = np.linspace(np.min(dist), np.max(dist), num=256)
        plot_(x, dist, contrast)
        plot_(x, dist, integral)

    for plot in p:
        plot.legend()


def auto(*_, image: ImageWrapper = None, **config):
    if image is None:
        return

    from ...kernels import load_kernels_for_image, release_kernels
    from PySide2.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton
    from PySide2.QtGui import QDoubleValidator, QIntValidator
    from PySide2.QtCore import Qt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
    from matplotlib.pyplot import Figure, Axes, Rectangle
    from matplotlib.backend_bases import MouseEvent

    try:
        load_kernels_for_image(image.get_raw())
        helper = FitHelper(image, ImageHelper(image.get_raw(), **config))

        d = QDialog()
        d.setWindowTitle("Autofit")
        d.setWindowState(Qt.WindowMaximized)

        layout = QVBoxLayout()
        buttons = QHBoxLayout()
        layout.addLayout(buttons)

        fig = Figure()
        agg = FigureCanvasQTAgg(figure=fig)
        ax: Axes = fig.add_subplot(2, 4, (1, 6))

        plots: Dict[str, Axes] = {
            INTEGRAL_TARGET: fig.add_subplot(247),
            INTEGRAL_SHADOW: fig.add_subplot(248),
            CONTRAST_TARGET: fig.add_subplot(243),
            CONTRAST_SHADOW: fig.add_subplot(244)
        }

        plots[INTEGRAL_TARGET].sharey(plots[INTEGRAL_SHADOW])
        plots[INTEGRAL_TARGET].sharex(plots[CONTRAST_TARGET])
        plots[CONTRAST_TARGET].sharey(plots[CONTRAST_SHADOW])
        plots[INTEGRAL_SHADOW].sharex(plots[CONTRAST_SHADOW])

        t_size = helper.im_helper.per_px(helper.im_helper.size_at_target)
        sp_size = helper.im_helper.per_px(helper.im_helper.size_at_shadow)

        def clear_subs():
            from ...tex import sci_2
            titles = [
                fr"Integral in Target plane $({sci_2(t_size[0])}\,km/px,\,{sci_2(t_size[1])}\,km/px)$",
                fr"Integral in Shadow plane $({sci_2(sp_size[0])}\,km/px,\,{sci_2(sp_size[1])}\,km/px)$",
                fr"Contrast in Target plane $({sci_2(t_size[0])}\,km/px,\,{sci_2(t_size[1])}\,km/px)$",
                fr"Contrast in Shadow plane $({sci_2(sp_size[0])}\,km/px,\,{sci_2(sp_size[1])}\,km/px)$"
            ]
            for p, title in zip(plots.values(), titles):
                p.clear()
                p.set_title(title)
                p.set_xlabel("Distance from start (km)")

        fig.set_tight_layout('true')
        ax.imshow(helper.data)

        def rect_intercept(gen: Generator[Tuple[Any, Fit]]) -> Generator[Fit]:
            for t in gen:
                rect: Rectangle = t[0]
                if rect.get_width() == 0:
                    ax.plot(
                        [rect.get_x(), rect.get_x() + rect.get_width()],
                        [rect.get_y(), rect.get_y() + rect.get_height()],
                        color="gray",
                        alpha=0.65
                    )
                else:
                    rect.set_color("gray")
                    rect.set_alpha(0.65)
                    ax.add_patch(rect)
                yield t[1]

        layout.addWidget(agg, stretch=1)
        tb = NavigationToolbar2QT(agg, d)
        layout.addWidget(tb)
        d.setLayout(layout)

        width = QLineEdit()
        window = QLineEdit()
        length = QLineEdit()
        radius = QLineEdit()
        initial_x = QLineEdit()
        initial_y = QLineEdit()

        np_func = QLineEdit()
        np_reverse_func = QLineEdit()

        def to_selection(vertical: bool) -> Selection:
            return Selection(
                initial_position=(float(initial_x.text()), float(initial_y.text())),
                is_vertical=vertical,
                shadow_radius=float(radius.text()),
                length=int(length.text()),
                width=int(width.text()),
                window=int(window.text())
            )

        np_func.setPlaceholderText("Numpy Function")
        np_reverse_func.setPlaceholderText("Numpy Reverse Function")

        for le in [width, window, initial_x, initial_y, radius]:
            le.setValidator(QDoubleValidator())

        length.setValidator(QIntValidator())

        width.setPlaceholderText("width")
        window.setPlaceholderText("window")
        length.setPlaceholderText("length")
        radius.setPlaceholderText("Shadow Radius")

        def make_visible(vertical: bool):
            ax.clear()
            clear_subs()
            ax.imshow(helper.data)
            show(helper.im_helper, rect_intercept(helper(to_selection(vertical))), plots)
            agg.draw()
            agg.flush_events()

        fit_vertical = QPushButton("Fit Vertical")
        fit_horizontal = QPushButton("Fit Horizontal")

        for c in [
            width,
            window,
            length,
            radius,
            initial_x,
            initial_y,
            np_func,
            np_reverse_func,
            fit_horizontal,
            fit_vertical
        ]:
            buttons.addWidget(c)

        def press_event(e: MouseEvent):
            if e.inaxes == ax:
                initial_x.setText(str(e.xdata))
                initial_y.setText(str(e.ydata))

        fig.canvas.mpl_connect('button_press_event', press_event)
        fit_vertical.clicked.connect(lambda _: make_visible(True))
        fit_horizontal.clicked.connect(lambda _: make_visible(False))

        d.exec_()

    finally:
        release_kernels()


__all__ = ['auto']
