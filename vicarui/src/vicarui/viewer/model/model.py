from pathlib import Path
from typing import Dict, List, Optional, Callable

from ...support import info, invoke_safe, FileType


# Not used anymore
class FileModel:
    file_store: Dict[FileType, List[Path]]
    callback_store: Dict[FileType, Callable[[Path], None]]
    clear_callback: Optional[Callable[[], None]] = None

    def __init__(self, *args, **kwargs):
        super(FileModel, self).__init__(*args, **kwargs)
        self.file_store = dict()
        self.callback_store = dict()

    def __len__(self):
        return len(self.file_store)

    @invoke_safe
    def __getitem__(self, item: FileType) -> Optional[List[Path]]:
        return self.file_store[item]

    @invoke_safe
    def set_clear_callback(self, c: Callable[[None], None]):
        self.clear_callback = c

    @invoke_safe
    def set_callback(self, for_type: FileType, c: Callable[[Path], None]):
        self.callback_store[for_type] = c

    @invoke_safe
    def accept_files(self, files: Dict[FileType, List[Path]]):
        amount = sum([len(files[k]) for k in files])
        info("Accepting files, count %d", amount)
        if amount != 0 and self.clear_callback is not None:
            self.clear_callback()
        for k in files:
            self.file_store[k] = files[k]
            if k in self.callback_store:
                for f in files[k]:
                    self.callback_store[k](f)
