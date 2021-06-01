from typing import NoReturn

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QDialog

from ..concurrent import Lock

_dialogs = list()
_lock = Lock()

_flags = (
        Qt.WindowMaximizeButtonHint
        & ~Qt.WindowContextHelpButtonHint
        | Qt.WindowCloseButtonHint
)


def _process_dialog(d: QDialog):
    _lock.run_blocking(lambda: _dialogs.append(d))
    __onclose = d.closeEvent

    def on_close(e):
        __onclose(e)
        _lock.run_blocking(lambda: _dialogs.remove(d))

    d.closeEvent = on_close


def _make() -> QDialog:
    dia = QDialog(f=_flags)
    _process_dialog(dia)
    return dia


def non_modal() -> QDialog:
    """
    Application default non-modal dialog
    """
    dia = _make()
    dia.setModal(False)
    return dia


def modal() -> QDialog:
    """
    Application default modal dialog
    """
    dia = _make()
    dia.setModal(True)
    return dia


def hold(d: QDialog) -> NoReturn:
    """
    Holds a reference to the dialog until it is closed
    """
    _process_dialog(d)


__all__ = ['non_modal', 'modal', 'hold']
