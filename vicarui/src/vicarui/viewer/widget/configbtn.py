from typing import Optional, Dict

from PySide2 import QtWidgets as qt

from ...analysis import get_config


class ConfigBtn(qt.QPushButton):
    anal_config: Optional[Dict]
    anal_config_filled: Optional[Dict]

    def __init__(self):
        super(ConfigBtn, self).__init__(text="Config")
        self.anal_config_filled = None
        self.anal_config = get_config()
        if self.anal_config is not None:
            self.clicked.connect(self.show_anal_dialog)
        else:
            self.setEnabled(False)

    def get_config(self) -> Optional[Dict]:
        values: Dict
        if self.anal_config_filled:
            values = self.anal_config_filled
        else:
            if self.anal_config:
                values = dict()
                for k, v in self.anal_config.items():
                    values[k] = v[1]
                self.anal_config_filled = values
            else:
                values = dict()
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
                widget.setPlaceholderText('Any value')
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
                    from ...support import logging as log
                    log.exception("Failed a config value", exc_info=e)
                    values[k] = None

            self.anal_config_filled = values
