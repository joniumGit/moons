from typing import Callable, Dict

from PySide2 import QtWidgets as qt

from ...analysis import get_additional_functions
from ...support import Busy
from ...logging import log


def call_additional(name: str, provider: Callable[[], Dict]):
    try:
        from ...analysis import anal_module
        getattr(anal_module(), name)(**provider())
    except (ImportError, AttributeError) as e:
        log.exception("Failed action", e)


class AdditionalBtn(qt.QPushButton):

    def __init__(self, arguments_provider: Callable[[], Dict]):
        super(AdditionalBtn, self).__init__(text="...")
        Busy.listen(self, lambda busy: self.setEnabled(not busy))
        additional = get_additional_functions()
        if additional:
            d = qt.QDialog()

            def __f(func_name: str):
                d.close()
                call_additional(func_name, arguments_provider)

            layout = qt.QVBoxLayout()
            from functools import partial
            for a, name in additional.items():
                b = qt.QPushButton(text=a)
                b.clicked.connect(partial(__f, name))
                layout.addWidget(b)
            d.setLayout(layout)
            d.setMinimumWidth(300)
            d.setWindowTitle("Additional")
            d.setModal(True)

            self.clicked.connect(lambda _: d.exec_())
        else:
            self.setEnabled(False)
