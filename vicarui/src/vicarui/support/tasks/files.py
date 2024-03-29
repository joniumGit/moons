from enum import Enum
from os import walk
from pathlib import Path
from time import time
from typing import Dict, List, Iterable, TypeVar, Callable, Union, Any

import numpy as np
from PySide2.QtCore import QThread
from vicarutil.image.core import read_beg_labels, Labels

from ..concurrent import typedsignal, signal
from ..ui import Progress
from ...logging import handle_exception

_T = TypeVar('_T')


class FileType(Enum):
    IMAGE = "IMG"
    LABEL = "LBL"


class SortType(Enum):
    FILT = 'filter'
    SEQ = 'sequence'
    EXP = 'exposure'
    OTHER = "--"

    @staticmethod
    def reverse(value: Any):
        if isinstance(value, str):
            if not hasattr(SortType, 'reversed_map'):
                SortType.reversed_map = {e.value: e for e in SortType}
            try:
                return SortType.reversed_map[value]
            except KeyError:
                return SortType.OTHER
        return value


def _safe_file_iter(o: Iterable[_T]) -> Iterable[_T]:
    try:
        yield from o
    except PermissionError:
        yield from o


def labels_from_image(p: Path) -> Labels:
    with open(p, 'rb') as f:
        return read_beg_labels(f)


def sequence_from_image(p: Path) -> str:
    try:
        labels = labels_from_image(p)
        return f"Sequence {labels['IDENTIFICATION']['SEQUENCE_ID']}"
    except KeyError:
        return "Not Found"


def default(*_, **__) -> str:
    return "Files"


def filter_from_image(p: Path) -> str:
    try:
        clear = {"CL1", "CL"}
        labels = labels_from_image(p)
        filters = [str(o).strip() for o in labels['INSTRUMENT']['FILTER_NAME']]
        if len(filters) == 0:
            return "Other"
        elif np.alltrue([filt in clear for filt in filters]):
            return "Clear"
        else:
            return ','.join(filters)
    except KeyError:
        return "Not Found"


def exposure_from_image(p: Path) -> str:
    try:
        labels = labels_from_image(p)
        exposure = int(labels['INSTRUMENT']['EXPOSURE_DURATION']) // 1000
        return f"{exposure - exposure % 10:d}"
    except KeyError:
        return "Not Found"


class FileTask(QThread):
    started = signal()
    set_count = typedsignal(int)
    update_count = typedsignal(int)
    finished = typedsignal(dict)

    def __init__(
            self,
            base_path: str,
            done_callback: Callable[[dict], None],
            sort_by: Union[str, SortType] = None
    ):
        super(FileTask, self).__init__()

        self.base = Path(base_path)
        self._start = 0
        self.sort_by = SortType.reverse(sort_by)

        _quit = self.quit

        def done(d: Dict):
            done_callback(d)
            Progress.stop()
            _quit()

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

                if self.sort_by == SortType.SEQ:
                    func = sequence_from_image
                elif self.sort_by == SortType.FILT:
                    func = filter_from_image
                elif self.sort_by == SortType.EXP:
                    func = exposure_from_image
                else:
                    func = default

                for d, _, files in walk(self.base, followlinks=False):
                    p = Path(d)
                    for f in files:
                        if f.endswith(FileType.IMAGE.value):
                            try:
                                fp = p.joinpath(f)
                                seq = func(fp)
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


__all__ = ['FileTask', 'FileType', 'SortType']
