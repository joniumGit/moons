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
from vicarutil.image import read_image

from .. import analysis as anal
from ..analysis import br_reduction, DataPacket, ImageWrapper
from ..support import logging as log


class VicarEvent:
    line_has_data: bool = False
    fit_x_start: int = -1
    fit_x_end: int = -1
    fit_degree: int = 2
    dpkt: DataPacket

    def __init__(self, data: np.ndarray, data_axis: Axes, line_axis: Axes, area: tuple[int, int]):
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

                self.line_axis.set_title(title)

                d = self.dpkt.fit(
                    self.fit_x_start,
                    self.fit_x_end,
                    in_kwargs={'color': 'black', 'linewidth': 3},
                    out_kwargs={'color': 'gray', 'linewidth': 3}
                )

                self.line_axis.set_title(
                    self.line_axis.get_title() + '\n' + d['FIT']['title'] + '\n' + d['BG']['title']
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
                    self.line_axis.set_title(f"HORIZONTAL slice with HEIGHT: {row - width} <= y <= {row + width}")
                    self.dpkt.scatter(self.line_axis, s=8, c='b')
                else:
                    r.set_color('r')
                    self.line_axis.set_title(f"VERTICAL slice with WIDTH: {col - width} <= x <= {col + width}")
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
            image: ImageWrapper,
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
            title = getattr(self, delegate)(image.get_raw(), axes=data_axis, **kwargs)
            self.fig.suptitle(title)
        except Exception as e:
            log.exception("Failed to set info", exc_info=e)

        data, mask = br_reduction(image, **br_pack)

        og_axis.imshow(image.get_image(), cmap="gray")
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

        old_toggle = qt.QCheckBox(text="Outlier detection")
        old_toggle.setChecked(True)
        self.old_toggle = old_toggle

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
        layout.addWidget(old_toggle, alignment=NW)
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
            'border': int(self.border_value.text()) if self.border_value.text().strip() != '' else 0,
            'old': self.old_toggle.isChecked()
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
    image: Optional[ImageWrapper]

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

    def show_image(self, image: ImageWrapper):
        self.image = image
        self.fig.clear()
        self.fig.show_image(
            image,
            self.adjustments.get_image_normalize(),
            self.adjustments.get_br_package(),
            self.adjustments.get_click_area()
        )

    def init_vicar_callback(self) -> Callable[[Path], None]:
        return lambda p: self.show_image(ImageWrapper(read_image(p)))


class StretchWidget(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(StretchWidget, self).__init__(*args, **kwargs)


class IntervalWidget(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(IntervalWidget, self).__init__(*args, **kwargs)
