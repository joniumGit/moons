import asyncio
from pathlib import Path
from typing import Callable, Optional

from PySide2 import QtWidgets as qt
from PySide2.QtCore import Qt as qt_core

from .align import NW, C
from .helpers import scan
from .imagewidget import PlotWidget
from .logging import debug, invoke_safe
from .model import FileModel, FileType


class PathItem(qt.QListWidgetItem):
    path: Path

    def __init__(self, path: Path, *args, **kwargs):
        super(PathItem, self).__init__(*args, **kwargs)
        self.setText(path.name)
        self.setForeground(qt_core.black)
        self.setBackground(qt_core.white)
        self.path = path

    def get_path(self) -> Path:
        return self.path


class FileListWidget(qt.QWidget):
    model: FileModel
    max_width = 250
    min_width = 200
    list_height = 400

    im_show: Optional[Callable[[Path], None]] = None
    lbl_show: Optional[Callable[[Path], None]] = None

    def set_image_show_callback(self, c: Callable[[Path], None]):
        self.im_show = c

    def set_lbl_show_callback(self, c: Callable[[Path], None]):
        self.lbl_show = c

    def __init__(self, *args, **kwargs):
        super(FileListWidget, self).__init__(*args, **kwargs)
        self.model = FileModel()
        self.__create_ui()

    @staticmethod
    def __init_list() -> qt.QListWidget:
        lst = qt.QListWidget()
        lst.setMinimumWidth(FileListWidget.min_width)
        lst.setMaximumWidth(FileListWidget.max_width)
        lst.setMinimumHeight(FileListWidget.list_height)
        lst.setMaximumHeight(FileListWidget.list_height)
        return lst

    @staticmethod
    def __set_small_defaults(o: qt.QWidget) -> None:
        o.setMinimumWidth(FileListWidget.min_width)
        o.setMaximumWidth(FileListWidget.max_width)
        o.setMinimumHeight(25)
        o.setMaximumHeight(25)

    @staticmethod
    def __create_spacer() -> qt.QSpacerItem:
        return qt.QSpacerItem(
            FileListWidget.min_width,
            2,
            hData=qt.QSizePolicy.Maximum,
            vData=qt.QSizePolicy.Minimum
        )

    def __create_ui(self):
        layout = qt.QVBoxLayout()
        load_btn = qt.QPushButton(text="Load files")
        select_btn = qt.QPushButton(text="Show")
        img_text = qt.QLabel(text="Image files")
        lbl_text = qt.QLabel(text="Label files")
        lbl_list = FileListWidget.__init_list()
        img_list = FileListWidget.__init_list()

        FileListWidget.__set_small_defaults(select_btn)
        FileListWidget.__set_small_defaults(load_btn)
        FileListWidget.__set_small_defaults(img_text)
        FileListWidget.__set_small_defaults(lbl_text)

        layout.addWidget(img_text, alignment=NW)
        layout.addWidget(img_list, alignment=NW)
        layout.addSpacerItem(FileListWidget.__create_spacer())
        layout.addWidget(lbl_text, alignment=NW)
        layout.addWidget(lbl_list, alignment=NW)
        layout.addSpacerItem(FileListWidget.__create_spacer())
        layout.addWidget(load_btn, alignment=C)
        layout.addWidget(select_btn, alignment=C)
        layout.addStretch()

        select_btn.clicked.connect(self.show_file)
        load_btn.clicked.connect(self.pick_dir)
        img_list.clicked.connect(lbl_list.clearSelection)
        lbl_list.clicked.connect(img_list.clearSelection)

        self.model.set_callback(FileType.IMAGE, lambda x: img_list.addItem(PathItem(x)))
        self.model.set_callback(FileType.LABEL, lambda x: lbl_list.addItem(PathItem(x)))
        self.model.set_clear_callback(self.clear)

        self.select_btn = select_btn
        self.load_btn = load_btn
        self.lbl_list = lbl_list
        self.img_list = img_list
        self.setLayout(layout)

    @invoke_safe
    def show_file(self):
        selected_img = self.img_list.selectedItems()
        selected_lbl = self.lbl_list.selectedItems()
        if self.im_show is not None and selected_img is not None and len(selected_img) > 0:
            self.im_show(selected_img[0].path)
            debug("Image selected: %s", str(selected_img[0].path))
        if self.lbl_show is not None and selected_lbl is not None and len(selected_lbl) > 0:
            self.lbl_show(selected_lbl[0].path)
            debug("Label selected: %s", str(selected_lbl[0].path))

    @invoke_safe
    def clear(self):
        debug("Clearing lists")
        self.lbl_list.clear()
        self.img_list.clear()

    @invoke_safe
    def pick_dir(self) -> None:
        debug("Picking files")
        selected = ImageChooser.getExistingDirectory()
        debug("Picked dir %s", str(selected))
        self.model.accept_files(asyncio.run(scan(selected)))


class ImageChooser(qt.QFileDialog):

    def __init__(self, callback: Callable, *args, **kwargs):
        super(ImageChooser, self).__init__(*args, **kwargs)
        self.callback = callback
        fd = self
        fd.setAcceptMode(fd.AcceptOpen)
        fd.setFileMode(fd.DirectoryOnly)
        fd.setOption(fd.ReadOnly, True)
        fd.setOption(fd.ShowDirsOnly, True)
        fd.setOption(fd.HideNameFilterDetails, True)
        fd.setOption(fd.DontUseCustomDirectoryIcons, True)
        fd.setViewMode(fd.List)


class AppWindow(qt.QWidget):

    def __init__(self, *args, **kwargs):
        super(AppWindow, self).__init__(*args, **kwargs)
        plw = PlotWidget()
        flw = FileListWidget()

        flw.set_image_show_callback(plw.init_vicar_callback())

        layout = qt.QHBoxLayout()
        layout.addWidget(flw)
        layout.addWidget(plw)
        self.setLayout(layout)
        self.plw = plw
        self.flw = flw
