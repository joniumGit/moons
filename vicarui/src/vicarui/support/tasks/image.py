from pathlib import Path
from typing import NoReturn

from PySide2.QtCore import QThread
from vicarutil.image import read_image

from ..concurrent import typedsignal
from ...analysis.wrapper import ImageWrapper


class ReadTask(QThread):
    done = typedsignal(ImageWrapper)

    def __init__(self, p: Path):
        super(ReadTask, self).__init__()
        self.filepath = p

    def run(self) -> NoReturn:
        image = read_image(self.filepath)
        wrapper = ImageWrapper(image)
        self.done.emit(wrapper)
        self.quit()


__all__ = ['ReadTask']
