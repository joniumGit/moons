from collections import Generator
from functools import partial
from typing import Any

from PySide2.QtCore import Qt
from PySide2.QtGui import QDoubleValidator, QIntValidator
from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel
from matplotlib.backend_bases import MouseEvent, MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.pyplot import Figure, Axes, Rectangle

from .classes import FitHelper, Selection, Fit
from .definition import *
from .show import show
from ..config import *
from ..helpers import ImageHelper
from ....common import load_kernels_for_image, release_kernels
from .....support import modal, sci_2


def auto(*_, image: ImageWrapper = None, **config):
    if image is None:
        return

    try:
        load_kernels_for_image(image.raw)
        helper = FitHelper(image, ImageHelper(image.raw, **config))
        t_size = helper.im_helper.per_px(helper.im_helper.size_at_target)
        sp_size = helper.im_helper.per_px(helper.im_helper.size_at_shadow)

        d = modal()
        d.setWindowTitle("Autofit")
        d.setWindowState(Qt.WindowMaximized)

        layout = QVBoxLayout()
        buttons = QHBoxLayout()
        layout.addLayout(buttons)

        fig = Figure()
        agg = FigureCanvasQTAgg(figure=fig)
        ax: Axes = fig.add_subplot(2, 4, (1, 6), label="Image Display")

        plots: Dict[str, Axes] = {
            INTEGRAL_TARGET: fig.add_subplot(247, label="Integral at Target"),
            INTEGRAL_SHADOW: fig.add_subplot(248, label="Integral at Shadow"),
            CONTRAST_TARGET: fig.add_subplot(243, label="Contrast at Target"),
            CONTRAST_SHADOW: fig.add_subplot(244, label="Contrast at Shadow")
        }

        titles: Dict[str, str] = {
            INTEGRAL_TARGET: fr"Integral in Target plane $({sci_2(t_size[0])}\,km/px,\,{sci_2(t_size[1])}\,km/px)$",
            INTEGRAL_SHADOW: fr"Integral in Shadow plane $({sci_2(sp_size[0])}\,km/px,\,{sci_2(sp_size[1])}\,km/px)$",
            CONTRAST_TARGET: fr"Contrast in Target plane $({sci_2(t_size[0])}\,km/px,\,{sci_2(t_size[1])}\,km/px)$",
            CONTRAST_SHADOW: fr"Contrast in Shadow plane $({sci_2(sp_size[0])}\,km/px,\,{sci_2(sp_size[1])}\,km/px)$"
        }

        plots[INTEGRAL_TARGET].sharey(plots[INTEGRAL_SHADOW])
        plots[INTEGRAL_TARGET].sharex(plots[CONTRAST_TARGET])

        plots[CONTRAST_SHADOW].sharey(plots[CONTRAST_TARGET])
        plots[CONTRAST_SHADOW].sharex(plots[INTEGRAL_SHADOW])

        def clear_subs():
            for k in plots:
                p = plots[k]
                p.clear()
                p.set_title(titles[k])
                p.set_xlabel("Distance from start (km)")

        fig.set_tight_layout('true')
        imdata = helper.data.copy().astype('float64')
        imdata[np.logical_not(np.isfinite(imdata))] = np.average(imdata[np.isfinite(imdata)])
        imdata = image.normalize(imdata)
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
                        alpha=0.3
                    )
                else:
                    rect.set_color("blue")
                    rect.set_alpha(0.3)
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
            clim = ax.get_images()[0].get_clim()
            ax.clear()
            clear_subs()
            ax.imshow()
            ax.get_images()[0].set_clim(clim)
            s = to_selection(vertical)
            log.info(f'ID: {helper.im_helper.id}')
            log.info(f'Selection: {s}')
            show(
                helper.im_helper,
                rect_intercept(helper(s)),
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
