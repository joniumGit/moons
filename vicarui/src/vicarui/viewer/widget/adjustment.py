from typing import Callable, Any, Union, Tuple, Dict

import numpy as np
from PySide2 import QtWidgets as qt
from PySide2.QtGui import QIntValidator
from astropy.visualization import ImageNormalize, ZScaleInterval, HistEqStretch

from ..helper import NW, CL
from ...support import Busy, typedsignal


class AdjustmentWidget(qt.QWidget):
    click = typedsignal(tuple)
    """
    Tuple[float, float, bool] click event
    """

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

        validator = QIntValidator()
        validator.setBottom(0)
        border_value.setValidator(validator)

        self.border_label = border_label
        self.border_value = border_value

        img_proc_toggle = qt.QCheckBox(text="Post-Processing")
        img_proc_toggle.setChecked(False)
        self.img_proc_toggle = img_proc_toggle

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

        simulate_click1 = qt.QPushButton("L")
        simulate_click2 = qt.QPushButton("R")
        for btn in [simulate_click1, simulate_click2]:
            btn.setFixedWidth(15)
        simulate_click_x = qt.QLineEdit()
        simulate_click_y = qt.QLineEdit()
        simulate_click_x.setFixedWidth(60)
        simulate_click_y.setFixedWidth(60)
        simulate_click_x.setValidator(QIntValidator())
        simulate_click_x.setValidator(QIntValidator())
        simulate_click_x.setPlaceholderText("Click X")
        simulate_click_y.setPlaceholderText("Click Y")
        layout.addWidget(simulate_click_x)
        layout.addWidget(simulate_click_y)
        layout.addWidget(simulate_click1)
        layout.addWidget(simulate_click2)

        def __click(right: bool = False):
            try:
                x = float(simulate_click_x.text())
                y = float(simulate_click_y.text())
                self.click.emit((x, y, right))
            except ValueError:
                pass
            except Exception as e:
                from ...support import log
                log.exception("Failed clock event", exc_info=e)

        simulate_click1.clicked.connect(__click)
        from functools import partial
        simulate_click2.clicked.connect(partial(__click, right=True))

        self.click_buttons = (simulate_click1, simulate_click2)
        self.click_x = simulate_click_x
        self.click_y = simulate_click_y

        click_width.setText(str(1))
        click_window.setText(str(100))

        reload_btn = qt.QPushButton(text="Reload")
        self.reload_btn = reload_btn
        Busy.listen(self, lambda busy: self.reload_btn.setEnabled(not busy))

        layout.addWidget(reload_btn, alignment=NW)
        self.setLayout(layout)

    def get_br_package(self) -> Dict[str, Any]:
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

    def get_click_area(self) -> Tuple[int, int]:
        w = self.click_width.text().strip()
        wind = self.click_window.text().strip()
        return int(w) if w != '' else 0, int(wind) if wind != '' else 0
