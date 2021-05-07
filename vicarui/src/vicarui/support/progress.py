from PySide2.QtWidgets import QProgressBar


class Progress:
    bar: QProgressBar = None


def start_progress():
    Progress.bar.setMinimum(0)
    Progress.bar.setMaximum(0)
    Progress.bar.setValue(0)


def stop_progress():
    Progress.bar.setMaximum(100)
    Progress.bar.reset()


def p_bar() -> QProgressBar:
    if Progress.bar is None:
        Progress.bar = QProgressBar()
    return Progress.bar
