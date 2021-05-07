from PySide2 import QtWidgets as qt

from .widget import PlotWidget, FileListWidget


class AppWindow(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(AppWindow, self).__init__(*args, **kwargs)
        plw = PlotWidget()
        flw = FileListWidget()

        plw.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        flw.setSizePolicy(qt.QSizePolicy.MinimumExpanding, qt.QSizePolicy.Expanding)

        flw.show_image.connect(plw.open_image)

        from functools import partial
        plw.image_show_start.connect(partial(setattr, flw, 'busy', True))
        plw.image_show_end.connect(partial(setattr, flw, 'busy', False))

        layout = qt.QHBoxLayout()
        layout.addWidget(flw)
        layout.addWidget(plw, stretch=90)
        self.setLayout(layout)
        self.plw = plw
        self.flw = flw
