from typing import Callable, Any, Union, Tuple, Dict

import numpy as np
from PySide2 import QtWidgets as qt
from PySide2.QtGui import QIntValidator
from astropy.visualization import ImageNormalize, ZScaleInterval, HistEqStretch

from ..helper import NW, CL
from ...support import Busy


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
        return int(w) if w != '' else 1, int(wind) if wind != '' else 1
