from vicarutil.image import VicarImage

from .config import ImageWrapper
from .helpers import ImageHelper


def view_labels(*_, image: ImageWrapper = None, **__):
    if image:
        image: VicarImage = image.get_raw()
        from PySide2.QtWidgets import QTextEdit, QHBoxLayout, QVBoxLayout, QLabel
        from PySide2.QtCore import QSize
        from ....viewer.helper import CT
        from ....support import non_modal

        dia = non_modal()
        dia.setModal(False)

        helper = ImageHelper(image)

        dia.setWindowTitle(f"IMAGE: {helper.id}")
        layout = QHBoxLayout()

        def boxed(title: str, text: str):
            sub = QVBoxLayout()
            t = QTextEdit()
            t.setMinimumWidth(250)
            t.setText(text)
            t.setReadOnly(True)
            sub.addWidget(QLabel(text=title), alignment=CT)
            sub.addWidget(t, stretch=1)
            layout.addLayout(sub, stretch=1)

        boxed("Labels", str(image.labels))

        if image.eol_labels is not None:
            boxed("EOL Labels", str(image.eol_labels))

        dia.setLayout(layout)
        dia.resize(QSize(480, 640))
        dia.setVisible(True)


__all__ = ['view_labels']
