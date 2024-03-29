from PySide2 import QtWidgets as qt

from .widget import PlotWidget, FileListWidget


class AppWindow(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(AppWindow, self).__init__(*args, **kwargs)
        plw = PlotWidget()
        flw = FileListWidget()

        plw.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        flw.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Expanding)

        from .helper import stack
        flw.show_image.connect(plw.open_image)
        flw.show_multiple.connect(lambda f: plw.show_image(stack(flw, f)))

        layout = qt.QHBoxLayout()
        layout.addWidget(flw)
        layout.addWidget(plw, stretch=90)
        self.setLayout(layout)
        self.plw = plw
        self.flw = flw
