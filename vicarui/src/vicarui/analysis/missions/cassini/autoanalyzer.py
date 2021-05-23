from collections import Generator
from dataclasses import dataclass
from functools import cached_property, partial
from typing import Any, NoReturn, Callable, TypeVar

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


def to_zero_one(v: np.ndarray) -> np.ndarray:
    return (v - np.min(v)) * 1 / (np.max(v) - np.min(v))


@dataclass(frozen=False)
class Selection:
    initial_position: Tuple[float, float]
    target_position: Tuple[float, float]
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
        return np.alltrue(np.isfinite([self.contrast, self.integral])) and self.contrast > 0 and self.integral > 0

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

        autofit = self.autofit
        autofit.start_x, autofit.start_y = s.target_position

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
) -> NoReturn:
    from matplotlib.pyplot import Axes
    from sklearn.preprocessing import FunctionTransformer
    from sklearn.pipeline import make_pipeline, Pipeline
    from sklearn.linear_model import RANSACRegressor, LinearRegression
    from sklearn.metrics import mean_squared_error
    from typing import cast
    from ...tex import sci_4
    from ...custom_fitter import OnePerRegression

    type_var = TypeVar('type_var')

    @dataclass(frozen=False)
    class Pipe:
        reg: type_var
        eq_producer: Callable[[type_var], str]
        pipe_producer: Callable[[type_var], Pipeline]
        color: str
        style: str
        title: str = ""
        log: bool = False

        @cached_property
        def line(self):
            return self.pipe_producer(self.reg)

        @cached_property
        def eq(self):
            return self.eq_producer(self.reg)

    fits = list()
    for fit in results:
        if fit.is_finite():
            fits.append(fit)

    def make_sac(base, max_trials=1000):
        return RANSACRegressor(
            random_state=0,
            max_trials=max_trials,
            min_samples=int(np.sqrt(len(fits))),
            base_estimator=base,
        )

    def to_eq(x):
        return (
                "$\n"
                fr"$k: \, {sci_4(x.estimator_.coef_[0])}$"
                + (
                    "\n"
                    fr"$a: \, {sci_4(x.estimator_.coef_[1])}$"
                    if len(x.estimator_.coef_) == 2 else ""
                )
                + "\n"
                  fr"$b: \, {sci_4(x.estimator_.intercept_)}$$\,"
        )

    plots = cast(Dict[str, Axes], plots)
    pipes = [
        Pipe(
            color="blue",
            style="-",
            title=r"$\frac{k}{x} + b$""\n",
            # pipe_producer=make_pipeline,
            pipe_producer=lambda r: make_pipeline(FunctionTransformer(np.reciprocal, np.reciprocal), r),
            reg=make_sac(LinearRegression(n_jobs=-1)),
            eq_producer=to_eq
        ),
        Pipe(
            color="red",
            style="-",
            title=r"$kx^a + b$",
            pipe_producer=make_pipeline,
            reg=make_sac(OnePerRegression()),
            eq_producer=to_eq
        ),
        Pipe(
            color="magenta",
            style="-",
            title=r"$\log y = a\log x + b$""\n",
            pipe_producer=lambda r: make_pipeline(FunctionTransformer(np.log1p, np.expm1), r),
            reg=make_sac(LinearRegression(n_jobs=-1)),
            eq_producer=to_eq,
            log=True
        )
    ]

    px_dist = np.asarray([fit[2] for fit in fits])
    tgt_size = np.asarray(helper.per_px(helper.size_at_target))
    sh_size = np.asarray(helper.per_px(helper.size_at_shadow))
    dists = [
        np.asarray([np.sqrt((d[0] * tgt_size[0]) ** 2 + (d[1] * tgt_size[1]) ** 2) for d in px_dist]),
        np.asarray([np.sqrt((d[0] * sh_size[0]) ** 2 + (d[1] * sh_size[1]) ** 2) for d in px_dist]),
    ]

    contrast, integral = (np.asarray([fit[i] for fit in fits]) for i in (0, 1))
    # contrast, integral = (to_zero_one(v) for v in (contrast, integral))

    names = [CONTRAST_TARGET, INTEGRAL_TARGET, CONTRAST_SHADOW, INTEGRAL_SHADOW]
    from warnings import catch_warnings, filterwarnings
    with catch_warnings():
        filterwarnings('ignore', r'.*R.*')
        for pipe in pipes:
            for tget in names:

                data_ = contrast if 'c' in tget else integral
                dist_ = dists[0] if 'tg' in tget else dists[1]
                x_ = np.linspace(np.min(dist_), np.max(dist_), num=256)

                ax: Axes = plots[tget]
                ax.scatter(dist_, data_, c="gray", s=4, alpha=0.65)

                try:
                    if not pipe.log:
                        pipe.line.fit(dist_[..., None], data_)
                        y = pipe.line.predict(x_[..., None])
                        mse = mean_squared_error(data_, pipe.line.predict(dist_[..., None]))
                    else:
                        pipe.line.fit(dist_[..., None], np.log1p(data_))
                        y = pipe.line.predict(x_[..., None])
                        y = np.expm1(y)
                        mse = mean_squared_error(np.log1p(data_), pipe.line.predict(dist_[..., None]))
                    log.info(
                        "FIT,"
                        + tget
                        + ","
                        + type(pipe.reg.estimator_).__name__
                        + ","
                        + ",".join(
                            (f"{v:.4e}" for v in [*pipe.reg.estimator_.coef_, pipe.reg.estimator_.intercept_, mse]))
                    )
                    ax.plot(
                        x_, y,
                        color=pipe.color,
                        linestyle=pipe.style,
                        label=fr"{pipe.title}$\, mse: {sci_4(mse)} \, {pipe.eq}$"
                    )
                    ax.legend()
                except ValueError:
                    log.exception("Failed a regression analysis")

                try:
                    ax.set_ylim(0, np.percentile(data_, 95))
                    pass
                except ValueError:
                    pass

                ax.figure.canvas.draw()
                ax.figure.canvas.flush_events()

    log.info("done")


def auto(*_, image: ImageWrapper = None, **config):
    if image is None:
        return

    from ...kernels import load_kernels_for_image, release_kernels
    from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel
    from PySide2.QtGui import QDoubleValidator, QIntValidator
    from PySide2.QtCore import Qt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
    from matplotlib.pyplot import Figure, Axes, Rectangle
    from matplotlib.backend_bases import MouseEvent, MouseButton
    from ....support import modal

    try:
        load_kernels_for_image(image.get_raw())
        helper = FitHelper(image, ImageHelper(image.get_raw(), **config))

        d = modal()
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
        plots[CONTRAST_SHADOW].sharey(plots[CONTRAST_TARGET])
        plots[CONTRAST_SHADOW].sharex(plots[INTEGRAL_SHADOW])

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
        imdata = helper.data.copy().astype('float64')
        imdata[np.logical_not(np.isfinite(imdata))] = np.average(imdata[np.isfinite(imdata)])
        imdata = to_zero_one(imdata)
        ax.imshow = partial(
            ax.imshow,
            imdata,
            cmap="gray",
            norm=None,
            aspect="equal",
            interpolation='none',
            origin='upper'
        )
        ax.imshow()

        def rect_intercept(gen: Generator[Tuple[Any, Fit]]) -> Generator[Fit]:
            for t in gen:
                rect: Rectangle = t[0]
                if rect.get_width() == 0:
                    ax.plot(
                        [rect.get_x(), rect.get_x() + rect.get_width()],
                        [rect.get_y(), rect.get_y() + rect.get_height()],
                        color="blue",
                        alpha=0.65
                    )
                else:
                    rect.set_color("blue")
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

        initial_label = QLabel("Selection start (L click)")
        initial_x = QLineEdit()
        initial_y = QLineEdit()

        target_label = QLabel("Target Center (R click)")
        target_x = QLineEdit()
        target_y = QLineEdit()

        # ♥

        def to_selection(vertical: bool) -> Selection:
            return Selection(
                initial_position=(float(initial_x.text()), float(initial_y.text())),
                target_position=(float(target_x.text()), float(target_y.text())),
                is_vertical=vertical,
                shadow_radius=float(radius.text()),
                length=int(length.text()),
                width=int(width.text()),
                window=int(window.text())
            )

        for le in [width, window, initial_x, initial_y, radius, target_x, target_y]:
            le.setValidator(QDoubleValidator())

        length.setValidator(QIntValidator())

        width.setPlaceholderText("width")
        window.setPlaceholderText("window")
        length.setPlaceholderText("length")
        radius.setPlaceholderText("Shadow Radius")

        def make_visible(vertical: bool):
            ax.clear()
            clear_subs()
            ax.imshow()
            show(
                helper.im_helper,
                rect_intercept(helper(to_selection(vertical))),
                plots
            )
            agg.draw()
            agg.flush_events()

        fit_vertical = QPushButton("Fit Vertical")
        fit_horizontal = QPushButton("Fit Horizontal")

        for c in [
            width,
            window,
            length,
            radius,
            initial_label,
            initial_x,
            initial_y,
            target_label,
            target_x,
            target_y,
            fit_horizontal,
            fit_vertical
        ]:
            buttons.addWidget(c)

        def press_event(e: MouseEvent):
            if e.canvas.cursor().shape() != 0:
                return
            if e.inaxes == ax:
                if e.button == MouseButton.LEFT:
                    initial_x.setText(str(e.xdata))
                    initial_y.setText(str(e.ydata))
                elif e.button == MouseButton.RIGHT:
                    target_x.setText(str(e.xdata))
                    target_y.setText(str(e.ydata))

        fig.canvas.mpl_connect('button_press_event', press_event)
        fit_vertical.clicked.connect(lambda _: make_visible(True))
        fit_horizontal.clicked.connect(lambda _: make_visible(False))

        d.exec_()

    finally:
        release_kernels()


__all__ = ['auto']
