from .config import *
from .funcs import norm
from .helpers import ImageHelper, Transformer
from ...fitting import DataPacket
from ...wrapper import ImageWrapper


class AutoFit:
    packet: DataPacket
    start_x: int
    start_y: int

    def __init__(self, packet: DataPacket):
        self.packet = packet
        self.start_x = 0
        self.start_y = 0

    def select(self, x: int, y: int, vertical: bool):
        return self.packet.select(x, y, vertical)

    def fit(self, x: float, y: float):
        data = self.packet.fit(x, y)
        bg = data['BG']['equation']
        fg = data['FIT']['equation']

        x_val = -0.5 * (bg[1] - fg[1]) / (bg[0] - fg[0])
        contrast = (bg[0] - fg[0]) * np.power(x_val, 2) + (bg[1] - fg[1]) * x_val + bg[2] - fg[2]

        eq = [bg[0] - fg[0], bg[1] - fg[1], bg[2] - fg[2]]
        roots = np.roots(eq)
        if len(roots) == 2 and np.alltrue(np.isreal(roots)):
            integral = (
                    1 / 3 * (bg[0] - fg[0]) * (np.power(roots[0], 3) - np.power(roots[1], 3))
                    + 1 / 2 * (bg[1] - fg[1]) * (np.power(roots[0], 2) - np.power(roots[1], 2))
                    + (bg[2] - fg[2]) * (roots[0] - roots[1]))
        else:
            integral = np.NAN

        return np.sqrt((self.start_x - x) ** 2 + (self.start_y - y) ** 2), contrast, integral


class FitHelper:

    def __init__(self, image: ImageWrapper, helper: ImageHelper):
        self.data = image.get_processed()
        self.packet = DataPacket(self.data)
        self.autofit = AutoFit(self.packet)
        self.shadow = norm(Transformer(SATURN_FRAME, helper.frame, helper.time_et)(
            helper.pos_in_sat(SUN_ID, helper.target_id()))
        )[0:2]

    def plot(self, initial: Tuple[float, float], vertical: bool, radius: float, max_iter: int, width: int, window: int):
        autofit = self.autofit
        shadow = self.shadow
        rad = radius

        self.autofit.start_x = int(initial[0])
        self.autofit.start_y = int(initial[1])

        self.packet.configure(width, window)

        fits = list()
        rects = list()
        if vertical:
            for i in range(
                    int(initial[0]),
                    int(initial[0] + max_iter * np.sign(shadow[0])),
                    int(1 * np.sign(shadow[0]))
            ):
                rects.append(autofit.select(int(initial[0]), int(initial[1]), vertical))
                fits.append(autofit.fit(
                    initial[1] - rad,
                    initial[1] + rad
                ))
                initial = (i, initial[1] + shadow[1] * np.abs(1 / shadow[0]))
        else:
            for i in range(
                    int(initial[1]),
                    int(initial[1] + max_iter * np.sign(shadow[1])),
                    int(1 * np.sign(shadow[1]))
            ):
                rects.append(autofit.select(int(initial[0]), int(initial[1]), vertical))
                fits.append(autofit.fit(
                    initial[0] - rad,
                    initial[0] + rad
                ))
                initial = (initial[0] + shadow[0] * np.abs(1 / shadow[1]), i)

        return zip(fits, rects)


def auto(*_, image: ImageWrapper = None, **config):
    from ...kernels import load_kernels_for_image, release_kernels
    try:
        load_kernels_for_image(image.get_raw())
        helper = FitHelper(image, ImageHelper(image.get_raw(), **config))
    finally:
        release_kernels()

    from PySide2.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton
    from PySide2.QtGui import QDoubleValidator, QIntValidator
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
    from matplotlib.pyplot import Figure, Axes

    d = QDialog()
    d.setWindowTitle("Autofit")
    layout = QVBoxLayout()
    buttons = QHBoxLayout()
    layout.addLayout(buttons)

    fig = Figure()
    agg = FigureCanvasQTAgg(figure=fig)
    ax: Axes = fig.add_subplot(121)
    other_ax: Axes = fig.add_subplot(122)
    fig.set_tight_layout('true')
    ax.imshow(helper.data)

    layout.addWidget(agg, stretch=1)
    tb = NavigationToolbar2QT(agg, d)
    layout.addWidget(tb)
    d.setLayout(layout)

    width = QLineEdit()
    window = QLineEdit()
    max_iter = QLineEdit()
    radius = QLineEdit()
    initial_x = QLineEdit()
    initial_y = QLineEdit()

    for le in [width, window, initial_x, initial_y, radius]:
        le.setValidator(QDoubleValidator())

    max_iter.setValidator(QIntValidator())

    width.setText("1")
    window.setText("100")
    max_iter.setText("10")
    radius.setText("5")

    def make_visible(vertical: bool):
        ax.clear()
        other_ax.clear()
        ax.imshow(helper.data)
        for fit, rect in helper.plot(
                (float(initial_x.text()), float(initial_y.text())),
                vertical,
                float(radius.text()),
                int(max_iter.text()),
                int(width.text()),
                int(window.text())
        ):
            ax.add_patch(rect)
            other_ax.scatter(*fit[0:2])

        agg.draw()
        agg.flush_events()

    fit_vertical = QPushButton("Fit Vertical")
    fit_horizontal = QPushButton("Fit Horizontal")

    for c in [width, window, max_iter, radius, initial_x, initial_y, fit_horizontal, fit_vertical]:
        buttons.addWidget(c)

    from matplotlib.backend_bases import MouseEvent

    def press_event(e: MouseEvent):
        if e.inaxes == ax:
            initial_x.setText(str(e.xdata))
            initial_y.setText(str(e.ydata))

    fig.canvas.mpl_connect('button_press_event', press_event)
    fit_vertical.clicked.connect(lambda _: make_visible(True))
    fit_horizontal.clicked.connect(lambda _: make_visible(False))

    d.exec_()


__all__ = ['auto']
