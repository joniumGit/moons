import importlib
from pathlib import Path
from typing import Callable, Optional, Any, Union

import numpy as np
from PySide2 import QtWidgets as qt
from astropy.visualization import ImageNormalize, ZScaleInterval, HistEqStretch
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavBar
from matplotlib.figure import Figure
from vicarutil.image import VicarImage, read_image

from .. import analysis as anal
from ..analysis import br_reduction
from ..support import logging as log


def e(s: str):
    part = s.split('e')
    if len(part) != 1:
        return part[0] + "e^{" + str(int(part[1])) + "}"
    else:
        return part[0]


class VicarEvent:
    line_has_data: bool = False
    fit_x_start: int = -1
    fit_x_end: int = -1
    fit_degree: int = 2

    def __init__(self, data: np.ndarray, data_axis: Axes, line_axis: Axes, area: tuple[int, int]):
        self.data = data
        self.area = area
        self.data_axis = data_axis
        self.line_axis = line_axis
        self.cid = data_axis.figure.canvas.mpl_connect('button_press_event', self)

        self.fit_x = None
        self.fit_y = None

    def __call__(self, event: MouseEvent):
        if event.canvas.cursor().shape() != 0:
            return
        if event.inaxes == self.line_axis and self.line_has_data:
            title = self.line_axis.get_title().split("\n")[0]
            if event.button == MouseButton.LEFT and self.fit_x_start == -1 and self.fit_x_end == -1:
                self.fit_x_start = event.xdata
                self.line_axis.set_title(title + " \nset end ")
            elif event.button == MouseButton.LEFT and self.fit_x_end == -1:
                self.fit_x_end = event.xdata

                if self.fit_x_start == self.fit_x_end:
                    return
                elif self.fit_x_end < self.fit_x_start:
                    temp = self.fit_x_end
                    self.fit_x_end = self.fit_x_start
                    self.fit_x_start = temp

                data_x = self.fit_x
                data_y = self.fit_y

                fit_data_x = list()
                fit_data_y = list()

                else_x = list()
                else_y = list()

                for i, j in zip(data_x, data_y):
                    if self.fit_x_start <= i <= self.fit_x_end:
                        fit_data_x.append(i)
                        fit_data_y.append(j)
                    else:
                        else_x.append(i)
                        else_y.append(j)

                log.debug(str(fit_data_x))
                log.debug(str(fit_data_y))

                import numpy.polynomial.polynomial as poly

                self.line_axis.set_title(title)

                def _plot(_x_s, _x_e, _x_d, _y_d, _c):
                    fit = poly.polyfit(_x_d, _y_d, self.fit_degree)
                    nx = np.arange(_x_s, _x_e, 0.1)
                    f = poly.polyval(nx, fit)
                    self.line_axis.plot(nx, f, linewidth=3, c=_c)
                    self.line_axis.set_title(self.line_axis.get_title() + f"\n{_c}: $" + e(f"{fit[0]:.3e}") + ''.join([
                        (" +" if __x > 0 else " ") + e(f"{__x:.3e}") + f"x^{__i + 1}"
                        if __i != 0 else e(f"{__x:.3e}") + "x"
                        for __i, __x in enumerate(fit[1:])
                    ]) + "$")

                _plot(data_x[0], data_x[-1], else_x, else_y, 'gray')
                _plot(self.fit_x_start, self.fit_x_end, fit_data_x, fit_data_y, 'black')

                self.line_axis.figure.canvas.draw()
            else:
                if event.button == MouseButton.LEFT:
                    self.fit_x_start = event.xdata
                    self.line_axis.set_title(title + "\nset end ")
                else:
                    self.fit_x_start = -1
                    self.line_axis.set_title(title + "\nset start ")
                self.fit_x_end = -1
                if len(self.line_axis.lines) != 0:
                    self.line_axis.lines.pop(1)
                    self.line_axis.lines.pop(0)
            self.line_axis.figure.canvas.draw()
        elif event.inaxes == self.data_axis:
            width = self.area[0]
            window = self.area[1]
            row = int(event.ydata)
            col = int(event.xdata)

            row_max = len(self.data) - 1
            col_max = len(self.data[0]) - 1

            log.debug(f"Click detected at {row},{col}")
            if width <= row <= row_max - width and width <= col <= col_max - width:
                if event.button in {MouseButton.LEFT, MouseButton.RIGHT}:
                    from matplotlib.patches import Rectangle
                    if hasattr(self, 'rect'):
                        if self.rect:
                            self.rect.remove()
                            self.rect = None

                    self.line_has_data = True
                    if event.button == MouseButton.LEFT:
                        self.line_axis.clear()
                        self.line_axis.set_title(f"HORIZONTAL slice with HEIGHT: {row - width} <= y <= {row + width}")
                        start = max(0, col - window)
                        end = min(col_max, col + window) + 1
                        x = np.arange(start, end, 1)
                        y = np.average(
                            self.data[row - width:row + width + 1, start:end].T,
                            axis=1
                        )
                        self.line_axis.scatter(x, y, s=8, c='b')

                        self.fit_x = x
                        self.fit_y = y

                        rect = Rectangle(
                            (start, row - width),
                            end - start - 1,
                            width * 2,
                            color='b',
                            lw=1,
                            fill=False
                        )
                        self.rect = rect
                        self.data_axis.add_patch(rect)
                    elif event.button == MouseButton.RIGHT:
                        self.line_axis.clear()
                        self.line_axis.set_title(f"VERTICAL slice with WIDTH: {col - width} <= x <= {col + width}")
                        start = max(0, row - window)
                        end = min(row_max, row + window) + 1
                        x = np.arange(start, end, 1)
                        y = np.average(
                            self.data[start:end, col - width:col + width + 1],
                            axis=1
                        )
                        self.line_axis.scatter(x, y, s=8, c='r')

                        self.fit_x = x
                        self.fit_y = y

                        rect = Rectangle(
                            (col - width, start),
                            width * 2,
                            end - start - 1,
                            color='r',
                            lw=1,
                            fill=False
                        )
                        self.rect = rect
                        self.data_axis.add_patch(rect)
                else:
                    self.clear_line()
            else:
                self.clear_line()
            self.line_axis.figure.canvas.draw()
            self.line_axis.figure.canvas.flush_events()

    def clear_line(self):
        self.line_axis.clear()
        self.line_has_data = False
        self.fit_x_start = -1
        self.fit_x_end = -1

    def detach(self):
        try:
            self.data_axis.figure.canvas.mpl_disconnect(self.cid)
        except Exception as e:
            log.exception("Exception in detach", exc_info=e)


class FigureWrapper(FigureCanvasQTAgg):
    event_handler: Optional[VicarEvent] = None

    def __init__(self, width=7.5, height=7.5, dpi=125):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(FigureWrapper, self).__init__(self.fig)

    def clear(self):
        if self.event_handler is not None:
            self.event_handler.detach()
            self.event_handler = None
        self.fig.clf(keep_observers=True)

    def show_image(
            self,
            image: VicarImage,
            norm: Callable[[np.ndarray], Union[ImageNormalize, None]],
            br_pack: dict[str, Any],
            click_area: tuple[int, int],
            **kwargs
    ):
        data_axis: Axes = self.fig.add_subplot(3, 3, (2, 6))
        og_axis = self.fig.add_subplot(331)
        bg_axis = self.fig.add_subplot(334)
        line_axis = self.fig.add_subplot(3, 3, (7, 9))

        data_axis.set_title("Post-Processed")
        og_axis.set_title("original")
        bg_axis.set_title("background")
        line_axis.set_title("line")

        try:
            delegate = 'show_image_delegate'
            if not hasattr(self, delegate):
                __i = importlib.import_module(f"..analysis.missions.{anal.SELECTED}", package=__package__)
                # noinspection PyUnresolvedReferences
                setattr(self, delegate, __i.set_info)
            title = getattr(self, delegate)(image, axes=data_axis, **kwargs)
            self.fig.suptitle(title)
        except Exception as e:
            log.exception("Failed to set info", exc_info=e)

        data, mask = br_reduction(image, **br_pack)
        og_axis.imshow(image.data[0], cmap="gray")
        bg_axis.imshow(mask, cmap="coolwarm")

        normalizer = norm(data)
        data_axis.imshow(
            data,
            norm=normalizer,
            cmap="gray",
            aspect="equal"
        )
        data_axis.minorticks_on()

        for x in self.fig.axes:
            if x != line_axis:
                x.invert_yaxis()

        if normalizer:
            data = normalizer(data)
        else:
            data_axis.set_title("No Post-Processing")

        self.event_handler = VicarEvent(data, data_axis, line_axis, click_area)
        self.figure.set_tight_layout('true')
        self.draw()


class AdjustmentWidget(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(AdjustmentWidget, self).__init__(*args, **kwargs)
        self.setFixedHeight(35)

        br_toggle = qt.QCheckBox(text="Background Reduction")
        br_toggle.setChecked(True)
        self.br_toggle = br_toggle

        normal_toggle = qt.QCheckBox(text="Normalization")
        normal_toggle.setChecked(True)
        self.normal_toggle = normal_toggle

        degree_label = qt.QLabel(text="Degree")
        degree = qt.QComboBox()

        for i in range(1, 6):
            degree.addItem(str(i))

        degree.setCurrentIndex(2)

        self.degree_label = degree_label
        self.degree = degree

        border_label = qt.QLabel(text="Border")
        border_value = qt.QLineEdit()
        border_value.setText(str(2))
        border_value.setFixedWidth(40)

        from PySide2.QtGui import QIntValidator
        validator = QIntValidator()
        validator.setBottom(0)
        border_value.setValidator(validator)

        self.border_label = border_label
        self.border_value = border_value

        img_proc_toggle = qt.QCheckBox(text="Post-Processing")
        img_proc_toggle.setChecked(True)
        self.img_proc_toggle = img_proc_toggle

        from .align import NW, CL

        layout = qt.QHBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(br_toggle, alignment=NW)
        layout.addWidget(degree, alignment=NW)
        layout.addWidget(degree_label, alignment=CL)
        layout.addSpacerItem(qt.QSpacerItem(10, 5, hData=qt.QSizePolicy.Minimum, vData=qt.QSizePolicy.Minimum))
        layout.addWidget(normal_toggle, alignment=NW)
        layout.addSpacerItem(qt.QSpacerItem(10, 5, hData=qt.QSizePolicy.Minimum, vData=qt.QSizePolicy.Minimum))
        layout.addWidget(border_value, alignment=NW)
        layout.addWidget(border_label, alignment=CL)
        layout.addSpacerItem(qt.QSpacerItem(10, 5, hData=qt.QSizePolicy.Minimum, vData=qt.QSizePolicy.Minimum))
        layout.addWidget(img_proc_toggle, alignment=NW)
        layout.addStretch()

        click_width = qt.QLineEdit()
        validator = QIntValidator()
        validator.setBottom(1)
        click_width.setValidator(validator)
        click_width.setFixedWidth(30)

        click_window = qt.QLineEdit()
        validator = QIntValidator()
        validator.setBottom(1)
        click_window.setValidator(validator)
        click_window.setFixedWidth(30)

        self.click_width = click_width
        self.click_window = click_window
        self.click_label = qt.QLabel(text="Click area (width, window)")

        layout.addWidget(self.click_label)
        layout.addWidget(click_width, alignment=NW)
        layout.addWidget(click_window, alignment=NW)

        click_width.setText(str(1))
        click_window.setText(str(100))

        reload_btn = qt.QPushButton(text="Reload")
        self.reload_btn = reload_btn
        layout.addWidget(reload_btn, alignment=NW)

        self.setLayout(layout)

    def get_br_package(self) -> dict[str, Any]:
        return {
            'normalize': self.normal_toggle.isChecked(),
            'reduce': self.br_toggle.isChecked(),
            'degree': self.degree.currentIndex() + 1,
            'border': int(self.border_value.text()) if self.border_value.text().strip() != '' else 0
        }

    def get_image_normalize(self) -> Callable[[np.ndarray], Union[ImageNormalize, None]]:
        if self.img_proc_toggle.isChecked():
            return lambda image: ImageNormalize(interval=ZScaleInterval(), stretch=HistEqStretch(image))
        else:
            return lambda image: None

    def get_click_area(self) -> tuple[int, int]:
        w = self.click_width.text().strip()
        wind = self.click_window.text().strip()
        return (
            int(w) if w != '' else 1,
            int(wind) if wind != '' else 1
        )


class PlotWidget(qt.QWidget):
    image: Optional[VicarImage]

    def __init__(self, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)
        self.fig = FigureWrapper()
        self.tools = NavBar(self.fig, self)

        self.frame = qt.QFrame()
        sub_layout = qt.QVBoxLayout()
        sub_layout.addWidget(self.fig)
        self.frame.setMinimumWidth(700)
        self.frame.setMinimumHeight(700)
        self.frame.setLayout(sub_layout)

        layout = qt.QVBoxLayout()
        layout.setSpacing(2)
        self.adjustments = AdjustmentWidget()
        self.adjustments.reload_btn.clicked.connect(self.reload_image)

        layout.addWidget(self.adjustments)
        layout.addWidget(self.frame)
        layout.addWidget(self.tools)

        self.setLayout(layout)
        self.image = None

    def reload_image(self):
        if self.image:
            self.show_image(self.image)

    def show_image(self, image: VicarImage):
        self.image = image
        self.fig.clear()
        self.fig.show_image(
            image,
            self.adjustments.get_image_normalize(),
            self.adjustments.get_br_package(),
            self.adjustments.get_click_area()
        )

    def init_vicar_callback(self) -> Callable[[Path], None]:
        return lambda p: self.show_image(read_image(p))


class StretchWidget(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(StretchWidget, self).__init__(*args, **kwargs)


class IntervalWidget(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(IntervalWidget, self).__init__(*args, **kwargs)
