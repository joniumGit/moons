from typing import NoReturn

from PySide2.QtWidgets import QProgressBar


class Progress:
    """
    Global progress bar
    """
    _bar: QProgressBar = None

    @staticmethod
    def start() -> NoReturn:
        Progress._bar.setMinimum(0)
        Progress._bar.setMaximum(0)
        Progress._bar.setValue(0)

    @staticmethod
    def stop() -> NoReturn:
        Progress._bar.setMaximum(100)
        Progress._bar.reset()

    @staticmethod
    def max(value: int) -> NoReturn:
        Progress._bar.setMaximum(value)

    @staticmethod
    def value(value: int) -> NoReturn:
        Progress._bar.setValue(value)

    @staticmethod
    def bar() -> QProgressBar:
        if Progress._bar is None:
            Progress._bar = QProgressBar()
        return Progress._bar


def start_progress():
    Progress.start()


def stop_progress():
    Progress.stop()


__all__ = ['start_progress', 'stop_progress', 'Progress']
