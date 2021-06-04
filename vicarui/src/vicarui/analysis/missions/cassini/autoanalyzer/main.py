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
        shadow_angle = fr"${(spice.pi() - helper.im_helper.phase_angle) * spice.dpr():.2f}$ deg"

        d = modal()
        d.setWindowTitle("Autofit")
        d.setWindowState(Qt.WindowMaximized)

        layout = QVBoxLayout()
        buttons = QHBoxLayout()
        layout.addLayout(buttons)

        fig = Figure()
        agg = FigureCanvasQTAgg(figure=fig)
        data_ax: Axes = fig.add_subplot(2, 4, (1, 6), label="Image Display")
        data_ax.set_title(
            f"Image: {helper.im_helper.id}  "
            fr"$({sci_2(t_size[0])}\,km/px,\,{sci_2(t_size[1])}\,km/px)$  "
            fr"Shadow: {shadow_angle} to image"
        )

        cfg = helper.im_helper.config
        if cfg[SINGLE_PLOT_AUTOFIT] == 1:
            plots: Dict[str, Axes] = {
                CONTRAST_TARGET: fig.add_subplot(2, 4, (3, 8), label="Contrast at Target"),
            }
        elif cfg[SINGLE_PLOT_AUTOFIT] == 2:
            plots: Dict[str, Axes] = {
                CONTRAST_SHADOW: fig.add_subplot(2, 4, (3, 8), label="Contrast at Shadow")
            }
        elif cfg[SINGLE_PLOT_AUTOFIT] == 3:
            plots: Dict[str, Axes] = {
                INTEGRAL_TARGET: fig.add_subplot(2, 4, (3, 8), label="Integral at Target"),
            }
        elif cfg[SINGLE_PLOT_AUTOFIT] == 4:
            plots: Dict[str, Axes] = {
                INTEGRAL_SHADOW: fig.add_subplot(2, 4, (3, 8), label="Integral at Shadow"),
            }
        else:
            plots: Dict[str, Axes] = {
                INTEGRAL_TARGET: fig.add_subplot(247, label="Integral at Target"),
                INTEGRAL_SHADOW: fig.add_subplot(248, label="Integral at Shadow"),
                CONTRAST_TARGET: fig.add_subplot(243, label="Contrast at Target"),
                CONTRAST_SHADOW: fig.add_subplot(244, label="Contrast at Shadow")
            }

        titles: Dict[str, str] = {
            INTEGRAL_TARGET: fr"Integral in image plane",
            INTEGRAL_SHADOW: fr"Integral along shadow",
            CONTRAST_TARGET: fr"Contrast in image plane",
            CONTRAST_SHADOW: fr"Contrast along shadow"
        }

        def clear_subs():
            for k in plots:
                p = plots[k]
                from warnings import catch_warnings, simplefilter
                with catch_warnings():
                    simplefilter('ignore')
                    p.clear()
                p.minorticks_on()
                p.set_title(titles[k])
                p.set_xlabel("Distance from start (km)")
                if 'i' in k:
                    p.set_ylabel(r"$\dfrac{I\,km}{F}$", rotation=0)
                else:
                    p.set_ylabel(r"$\dfrac{I}{F}$", rotation=0)

        fig.set_tight_layout('true')
        imdata = helper.data.copy().astype('float64')
        imdata[np.logical_not(np.isfinite(imdata))] = np.average(imdata[np.isfinite(imdata)])
        imdata = image.normalize(imdata)
        data_ax.imshow = partial(
            data_ax.imshow,
            imdata,
            cmap="gray",
            norm=None,
            aspect="equal",
            interpolation='none',
            origin='upper'
        )
        data_ax.imshow()

        def rect_intercept(gen: Generator[Tuple[Any, Fit]]) -> Generator[Fit]:
            for t in gen:
                rect: Rectangle = t[0]
                if rect.get_width() == 0:
                    data_ax.plot(
                        [rect.get_x(), rect.get_x() + rect.get_width()],
                        [rect.get_y(), rect.get_y() + rect.get_height()],
                        color="blue",
                        alpha=0.1
                    )
                else:
                    rect.set_color("blue")
                    rect.set_alpha(0.1)
                    data_ax.add_patch(rect)
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
            clim = data_ax.get_images()[0].get_clim()
            data_ax.clear()
            clear_subs()
            data_ax.imshow()
            data_ax.get_images()[0].set_clim(clim)
            s = to_selection(vertical)
            log.info(f'ID: {helper.im_helper.id} BG: {image.degree if image.has_background else 0}')
            log.info(f'Selection: {s}')
            show(
                helper.im_helper,
                rect_intercept(helper(s)),
                plots,
                disable_fitting=cfg[DISABLE_FITTING]
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

        holder = [
            data_ax.scatter([], [], c=TARGET_COLOR, s=8, animated=True),
            data_ax.scatter([], [], c=TARGET_ALT_COLOR, s=8, animated=True)
        ]

        def points_draw():
            data_ax.draw_artist(holder[0])
            data_ax.draw_artist(holder[1])
            fig.canvas.blit(fig.bbox)

        def press_event(e: MouseEvent):
            if e.canvas.cursor().shape() != 0:
                return
            if e.inaxes == data_ax:
                if e.button == MouseButton.LEFT:
                    holder[0].set_offsets([(e.xdata, e.ydata)])
                    initial_x.setText(str(e.xdata))
                    initial_y.setText(str(e.ydata))
                    data_ax.redraw_in_frame()
                elif e.button == MouseButton.RIGHT:
                    holder[1].set_offsets([(e.xdata, e.ydata)])
                    target_x.setText(str(e.xdata))
                    target_y.setText(str(e.ydata))
                    data_ax.redraw_in_frame()
            points_draw()

        fig.canvas.mpl_connect('button_press_event', press_event)
        fit_vertical.clicked.connect(lambda _: make_visible(True))
        fit_horizontal.clicked.connect(lambda _: make_visible(False))

        fig.set_tight_layout('true')

        d.exec_()
    finally:
        release_kernels()


__all__ = ['auto']
