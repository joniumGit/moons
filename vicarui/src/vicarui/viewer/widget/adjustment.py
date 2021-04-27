from typing import Callable, Optional, Any, Union, Tuple, Dict

import numpy as np
from PySide2 import QtWidgets as qt
from astropy.visualization import ImageNormalize, ZScaleInterval, HistEqStretch

from ..helper import NW, CL
from ... import analysis as anal
from ...support import logging as log


class AdjustmentWidget(qt.QWidget):
    anal_config: Optional[Dict]
    anal_config_filled: Optional[Dict]

    def __init__(self, *args, **kwargs):
        super(AdjustmentWidget, self).__init__(*args, **kwargs)
        self.anal_config = anal.get_config()
        self.anal_config_filled = None

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

        if self.anal_config:
            config_btn = qt.QPushButton(text="Config")
            config_btn.clicked.connect(self.show_anal_dialog)
            self.config_btn = config_btn
            layout.addWidget(config_btn, alignment=NW)

        self.setLayout(layout)

    def get_br_package(self) -> Dict[str, Any]:
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

    def get_click_area(self) -> Tuple[int, int]:
        w = self.click_width.text().strip()
        wind = self.click_window.text().strip()
        return (
            int(w) if w != '' else 1,
            int(wind) if wind != '' else 1
        )

    def get_config(self) -> Optional[Dict]:
        values: Dict
        if self.anal_config_filled:
            values = self.anal_config_filled
        else:
            values = dict()
            for k, v in self.anal_config.items():
                values[k] = v[1]
            self.anal_config_filled = values
        return values

    def show_anal_dialog(self, *_, **__):
        values = self.get_config()

        from PySide2.QtWidgets import QDialog
        from PySide2.QtGui import QIntValidator, QDoubleValidator

        widgets = dict()

        layout = qt.QVBoxLayout()
        for k, v in self.anal_config.items():
            widget: Optional[qt.QLineEdit]
            if v[0] == str:
                widget = qt.QLineEdit()
                widget.setPlaceholderText('Any string value')
                widgets[k] = (str, widget)
            elif v[0] == int:
                widget = qt.QLineEdit()
                widget.setValidator(QIntValidator())
                widget.setPlaceholderText('Int value e.g. 1')
                widgets[k] = (int, widget)
            elif v[0] == float:
                widget = qt.QLineEdit()
                widget.setValidator(QDoubleValidator())
                widget.setPlaceholderText('Float value e.g. 0.001')
                widgets[k] = (float, widget)
            elif v[0] == bool:
                widget = qt.QLineEdit()
                widget.setPlaceholderText('True/False')
                widgets[k] = (bool, widget)
            else:
                widget = None
            if widget:
                if values[k] is not None:
                    widget.setText(str(values[k]))
                sub = qt.QVBoxLayout()
                sub.addWidget(qt.QLabel(k))
                sub.addWidget(widget)
                layout.addLayout(sub)

        if len(layout.children()) != 0:
            diag = QDialog()
            diag.setWindowTitle("Config")
            diag.setModal(True)
            diag.setLayout(layout)
            diag.exec_()

            for k, v in widgets.items():
                t = v[1].text()
                try:
                    if t and t != '':
                        if v[0] == bool:
                            if t in {'true', 'True'}:
                                values[k] = True
                            elif t in {'false', 'False'}:
                                values[k] = False
                            else:
                                values[k] = None
                        else:
                            values[k] = v[0](t)
                    else:
                        values[k] = None
                except ValueError as e:
                    log.exception("Failed a config value", exc_info=e)
                    values[k] = None

            self.anal_config_filled = values
