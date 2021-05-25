from pathlib import Path
from typing import Optional

from PySide2.QtCore import Slot, QThread
from PySide2.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavBar
from vicarutil.image import read_image

from .additionalbtn import AdditionalBtn
from .adjustment import AdjustmentWidget
from .configbtn import ConfigBtn
from ..helper import FigureWrapper, E
from ...analysis import ImageWrapper
from ...support import Progress


class ReadTask(QThread):
    from ...support import typedsignal
    done = typedsignal(ImageWrapper)

    def __init__(self, p: Path):
        super(ReadTask, self).__init__()
        self.filepath = p

    def run(self) -> None:
        image = read_image(self.filepath)
        wrapper = ImageWrapper(image)
        self.done.emit(wrapper)
        self.quit()


class PlotWidget(QWidget):
    image: Optional[ImageWrapper]
    from ...support import signal
    image_show_end = signal()
    image_show_start = signal()

    def __init__(self, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)
        self.fig = FigureWrapper()
        self.fig.image_shown.connect(self.image_show_end.emit)

        self.tools = NavBar(self.fig, self)

        self.frame = QFrame()
        sub_layout = QVBoxLayout()
        sub_layout.addWidget(self.fig)
        self.frame.setMinimumWidth(700)
        self.frame.setMinimumHeight(700)
        self.frame.setLayout(sub_layout)

        layout = QVBoxLayout()
        layout.setSpacing(2)
        self.adjustments = AdjustmentWidget()
        self.adjustments.reload_btn.clicked.connect(self.reload_image)

        layout.addWidget(self.adjustments)
        layout.addWidget(self.frame)

        sub = QHBoxLayout()
        sub.addWidget(self.tools)
        sub.addStretch()
        self.progress = Progress.bar()
        self.progress.setFixedWidth(250)
        sub.addWidget(self.progress, alignment=E)

        config = ConfigBtn()
        self.config = config
        additional = AdditionalBtn(self.additional_callable)
        sub.addWidget(config)
        sub.addWidget(additional)

        layout.addLayout(sub)

        self.setLayout(layout)
        self.image = None

        from ...analysis import register_mission_listener
        register_mission_listener(lambda _: self.reload_image())

    def get_config(self):
        return self.config.get_config()

    def additional_callable(self):
        if self.image is not None:
            return {
                'image': self.image,
                **self.get_config()
            }
        else:
            return dict()

    def reload_image(self):
        if self.image:
            self.image_show_start.emit()
            self.show_image(self.image, reload=True)

    def show_image(self, image: ImageWrapper, reload: bool = False):
        self.image = image
        self.fig.show_image(
            image,
            self.adjustments.get_image_normalize(),
            self.adjustments.get_br_package(),
            self.adjustments.get_click_area(),
            restore=reload,
            **(self.get_config() or dict())
        )

    @Slot(Path)
    def open_image(self, p: Path):
        self.image_show_start.emit()
        from ...support import start_progress
        start_progress()
        task = ReadTask(p)
        task.done.connect(self.show_image)
        task.run()


__all__ = ['PlotWidget']
