from enum import Enum
from os import walk
from pathlib import Path
from time import time
from typing import Dict, List, Iterable, TypeVar, Tuple, Callable

import numpy as np
from PySide2.QtCore import QThread

from ..concurrent import typedsignal, signal
from ..logging import handle_exception
from ..progress import Progress

_T = TypeVar('_T')


class FileType(Enum):
    IMAGE = "IMG"
    LABEL = "LBL"


def _safe_file_iter(o: Iterable[_T]) -> Iterable[_T]:
    try:
        yield from o
    except PermissionError:
        yield from o


def sequence_from_image(p: Path):
    from vicarutil.image.core import read_beg_labels
    with open(p, 'rb') as f:
        labels = read_beg_labels(f)
        return labels['IDENTIFICATION']['SEQUENCE_ID']


class FileTask(QThread):
    started = signal()
    set_count = typedsignal(int)
    update_count = typedsignal(int)
    finished = typedsignal(dict)

    def __init__(self, base_path: str, done_callback: Callable[[dict], None]):
        super(FileTask, self).__init__()

        self.base = Path(base_path)
        self._start = 0

        _quit = self.quit

        def done(d: Dict):
            done_callback(d)
            _quit()
            Progress.stop()

        self.started.connect(Progress.start())
        self.finished.connect(done)
        self.set_count.connect(lambda i: Progress.max(i))
        self.update_count.connect(lambda i: Progress.value(i))

    def abort(self):
        self.finished.emit(dict())

    def check_time(self):
        from time import time
        current = time()
        if current - self._start > 30:
            raise TimeoutError()

    def scan_dirs(self, path: Path) -> List[Path]:
        out = list()
        self.check_time()
        out.append(path)
        for f in _safe_file_iter(path.iterdir()):
            if f.is_dir():
                out.extend(self.scan_dirs(f))
        return out

    def scan_files(self, path: Path) -> List[Tuple[str, Path]]:
        out = list()
        self.check_time()
        for f in _safe_file_iter(path.iterdir()):
            if f.is_file() and f.suffix.endswith(FileType.IMAGE.value):
                try:
                    seq = sequence_from_image(f)
                    out.append((seq, f))
                except Exception as e:
                    handle_exception(e)
        return out

    def run(self) -> None:
        try:

            self._start = time()
            self.started.emit()
            if self.base.is_dir():
                dirs = self.scan_dirs(self.base)
                self.set_count.emit(len(dirs))
                out = dict()
                total: int = np.sum([len(files) for _, _, files in walk(self.base, followlinks=False)])
                self.set_count.emit(total)
                cnt = 0
                self.update_count.emit(cnt)
                for d, _, files in walk(self.base, followlinks=False):
                    p = Path(d)
                    for f in files:
                        if f.endswith(FileType.IMAGE.value):
                            try:
                                fp = p.joinpath(f)
                                seq = sequence_from_image(fp)
                                if seq not in out:
                                    out[seq] = list()
                                out[seq].append(fp)
                            except Exception as e:
                                handle_exception(e)
                        cnt += 1
                        self.update_count.emit(cnt)
                self.finished.emit(out)
            else:
                self.finished.emit(dict())
            self.quit()
        except TimeoutError:
            self.finished.emit(dict())
            self.quit()


__all__ = ['FileTask', 'FileType']
