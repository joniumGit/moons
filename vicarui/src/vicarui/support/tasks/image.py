from pathlib import Path
from typing import NoReturn, Dict

from PySide2.QtCore import QThread
from vicarutil.image import read_image

from ..concurrent import typedsignal, signal
from ..misc import ImageWrapper


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


class BRTask(QThread):
    done = signal()

    def __init__(self, image: ImageWrapper, br_config: Dict):
        super(BRTask, self).__init__()
        self._image = image
        self.br_config = br_config

    def run(self) -> NoReturn:
        from ...analysis import br_reduction
        image = self._image
        image.border = self.br_config['border']
        if self.br_config['reduce']:
            image.active = True
            br_reduction(image, degree=self.br_config['degree'])
        else:
            image.active = False
        image.normalized = self.br_config['normalize']
        self.done.emit()
        self.quit()


__all__ = ['ReadTask', 'BRTask']
