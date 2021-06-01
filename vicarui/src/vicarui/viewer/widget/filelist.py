from pathlib import Path
from typing import List, Dict, TypeVar

from PySide2 import QtWidgets as qt
from PySide2.QtGui import QStandardItem, QStandardItemModel, QMouseEvent

from ..helper import C
from ...logging import handle_exception, debug
from ...support import invoke_safe, typedsignal, SimpleSignal, FileTask, Tasker, Busy

_T = TypeVar('_T')


class _CommonConfig:
    max_width = 250
    min_width = 200


class CategoryItem(QStandardItem):

    def __init__(self, category: str):
        super(CategoryItem, self).__init__()
        self.setText(category)
        self.setEditable(False)
        self.setSelectable(False)


class PathItem(QStandardItem):

    def __init__(self, path: Path):
        super(PathItem, self).__init__()
        self.path = path
        self.setText(path.name)
        self.setEditable(False)
        self.setSelectable(True)

    def get_path(self) -> Path:
        return self.path


class FileModel(QStandardItemModel):

    def __init__(self, **files: List[Path]):
        super(FileModel, self).__init__()
        items = list()
        for k, v in files.items():
            if len(v) != 0:
                i = CategoryItem(f"{k}")
                for j in v:
                    si = PathItem(j)
                    i.appendRow(si)
                items.append(i)
        items.sort(key=lambda item: item.text())
        root = self.invisibleRootItem()
        root.appendRows(items)


class ImageChooser(qt.QFileDialog):

    def __init__(self, *args, **kwargs):
        super(ImageChooser, self).__init__(*args, **kwargs)
        self.setAcceptMode(self.AcceptOpen)
        self.setFileMode(self.DirectoryOnly)
        self.setOption(self.ReadOnly, True)
        self.setOption(self.ShowDirsOnly, True)
        self.setOption(self.HideNameFilterDetails, True)
        self.setOption(self.DontUseCustomDirectoryIcons, True)
        self.setViewMode(self.List)


class Spacer(qt.QSpacerItem):
    def __init__(self):
        super(Spacer, self).__init__(
            _CommonConfig.min_width,
            2,
            hData=qt.QSizePolicy.Minimum,
            vData=qt.QSizePolicy.Maximum
        )


class Button(qt.QPushButton):
    clicked: SimpleSignal

    def __init__(self, text: str):
        super(Button, self).__init__(text=text)
        self.setFixedWidth(_CommonConfig.max_width)
        self.setFixedHeight(25)
        self.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)


class Label(qt.QLabel):

    def __init__(self, text: str):
        super(Label, self).__init__(text=text)
        self.setFixedWidth(_CommonConfig.max_width)
        self.setFixedHeight(25)
        self.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)


class FileListWidget(qt.QWidget):
    show_image = typedsignal(Path)
    show_multiple = typedsignal(list)

    model: FileModel
    _busy = False

    def __init__(self, *args, **kwargs):
        super(FileListWidget, self).__init__(*args, **kwargs)

        layout = qt.QVBoxLayout()
        layout.setSpacing(2)

        self.setLayout(layout)

        load_btn = Button("Load files")
        show_btn = Button("Show")
        clear_btn = Button("Clear")
        item_label = Label("Image files")
        item_view = qt.QTreeView()
        sort_selection = qt.QComboBox()
        sort_selection.addItems(FileTask.Sort.SELECTIONS[::-1])
        sort_selection.setEditable(False)
        self.sort_selection = sort_selection

        item_view.setHeaderHidden(True)
        item_view.mouseDoubleClickEvent = self.show_on_dbl
        item_view.setSelectionMode(item_view.SelectionMode.ExtendedSelection)

        layout.addWidget(item_label)
        layout.addWidget(sort_selection)
        layout.addWidget(item_view)
        layout.addSpacerItem(Spacer())
        layout.addWidget(load_btn, alignment=C)
        layout.addWidget(clear_btn, alignment=C)
        layout.addWidget(show_btn, alignment=C)

        show_btn.clicked.connect(self.show_file)
        load_btn.clicked.connect(self.pick_dir)
        clear_btn.clicked.connect(self.clear)

        self.show_btn = show_btn
        self.load_btn = load_btn
        self.item_view = item_view

        self.model = QStandardItemModel()
        self.model.invisibleRootItem()

        Busy.listen(self, self.set_busy)

    def set_busy(self, busy: bool):
        if busy:
            self._busy = True
            self.show_btn.setEnabled(False)
            self.load_btn.setEnabled(False)
        else:
            self._busy = False
            self.show_btn.setEnabled(True)
            self.load_btn.setEnabled(True)

    @invoke_safe
    def show_file(self):
        try:
            if not self._busy:
                if len(self.item_view.selectedIndexes()) > 1:
                    selected: List[Path] = [
                        self.model.itemFromIndex(i).get_path() for i in self.item_view.selectedIndexes()
                    ]
                    debug("Selected %d files", len(selected))
                    self.show_multiple.emit(selected)
                elif len(self.item_view.selectedIndexes()) == 1:
                    selected_img: PathItem = self.model.itemFromIndex(self.item_view.selectedIndexes()[0])
                    if selected_img is not None:
                        debug("Image selected: %s", str(selected_img.get_path()))
                        self.show_image.emit(selected_img.get_path())
        except IndexError:
            pass

    @invoke_safe
    def clear(self):
        debug("Clearing lists")
        self.model.clear()

    @invoke_safe
    def files_callback(self, files: Dict[str, List[Path]]):
        self.model = FileModel(**files)
        self.item_view.setModel(self.model)
        Busy.clear()

    @invoke_safe
    def pick_dir(self) -> None:
        debug("Picking files")
        selected = ImageChooser.getExistingDirectory(caption="Select image directory")
        if selected is not None and selected != "":
            Busy.set_busy()
            debug("Picked dir %s", str(selected))
            Tasker.run(FileTask(
                selected,
                self.files_callback,
                sort_by=self.sort_selection.itemText(self.sort_selection.currentIndex())
            ))

    @invoke_safe
    def show_on_dbl(self, event: QMouseEvent) -> None:
        try:
            i = self.item_view.indexAt(event.pos())
            if i is not None:
                item: QStandardItem = self.model.itemFromIndex(i)
                if item is not None and item.hasChildren():
                    if self.item_view.isExpanded(i):
                        self.item_view.collapse(i)
                    else:
                        self.item_view.expand(i)
                else:
                    self.show_file()
        except Exception as e:
            handle_exception(e)
