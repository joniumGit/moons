from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog

_dialogs = list()


def non_modal() -> QDialog:
    dia = QDialog(
        f=Qt.WindowMaximizeButtonHint
          & ~Qt.WindowContextHelpButtonHint
          | Qt.WindowCloseButtonHint
    )

    __onclose = dia.closeEvent

    def on_close(e):
        __onclose(e)
        _dialogs.remove(dia)

    dia.closeEvent = on_close

    return dia


def modal() -> QDialog:
    dia = QDialog(
        f=Qt.WindowMaximizeButtonHint
          & ~Qt.WindowContextHelpButtonHint
          | Qt.WindowCloseButtonHint
    )
    dia.setModal(True)

    __onclose = dia.closeEvent

    def on_close(e):
        __onclose(e)
        _dialogs.remove(dia)

    dia.closeEvent = on_close

    return dia
