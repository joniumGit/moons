from typing import BinaryIO

from .definitions.definitions import LABEL_ENCODING


class StrIO:

    def __init__(self, file: BinaryIO):
        self.file = file

    def reset(self) -> None:
        self.seek(0)

    def seek(self, n: int = 0, whence: int = 0) -> None:
        self.file.seek(n, whence)

    def read(self, n: int = 1) -> str:
        return str(self.file.read(n), encoding=LABEL_ENCODING)

    def unwrap(self) -> BinaryIO:
        return self.file
