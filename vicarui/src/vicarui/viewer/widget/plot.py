from pathlib import Path
from typing import Callable, Optional

from PySide2 import QtWidgets as qt
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavBar
from vicarutil.image import read_image

from .additionalbtn import AdditionalBtn
from .adjustment import AdjustmentWidget
from .configbtn import ConfigBtn
from ..helper import FigureWrapper, E
from ...analysis import ImageWrapper


class PlotWidget(qt.QWidget):
    image: Optional[ImageWrapper]

    def __init__(self, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)
        self.fig = FigureWrapper()
        self.tools = NavBar(self.fig, self)

        self.frame = qt.QFrame()
        sub_layout = qt.QVBoxLayout()
        sub_layout.addWidget(self.fig)
        self.frame.setMinimumWidth(700)
        self.frame.setMinimumHeight(700)
        self.frame.setLayout(sub_layout)

        layout = qt.QVBoxLayout()
        layout.setSpacing(2)
        self.adjustments = AdjustmentWidget()
        self.adjustments.reload_btn.clicked.connect(self.reload_image)

        layout.addWidget(self.adjustments)
        layout.addWidget(self.frame)

        sub = qt.QHBoxLayout()
        sub.addWidget(self.tools)
        sub.addStretch()
        self.progress = qt.QProgressBar()
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

    def get_config(self):
        return self.config.get_config()

    def additional_callable(self):
        if self.image is not None:
            return {
                'image': self.image.get_raw(),
                **self.get_config()
            }
        else:
            return dict()

    def reload_image(self):
        if self.image:
            self.show_image(self.image)

    def show_image(self, image: ImageWrapper):
        self.image = image
        self.fig.clear()
        self.fig.show_image(
            image,
            self.adjustments.get_image_normalize(),
            self.adjustments.get_br_package(),
            self.adjustments.get_click_area(),
            **(self.get_config() or dict())
        )

    def init_vicar_callback(self) -> Callable[[Path], None]:
        return lambda p: self.show_image(ImageWrapper(read_image(p)))
