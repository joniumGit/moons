from os import PathLike
from pathlib import Path
from typing import Dict, List, Union

from .logging import invoke_safe_or_default, invoke_safe
from .filetype import FileType


@invoke_safe_or_default(default=dict())
async def scan(d: Union[str, PathLike]) -> Dict[FileType, List[Path]]:
    if d is not None:
        d = Path(d)
        files: Dict[FileType, List[Path]] = dict()
        for t in FileType:
            files[t] = list()
        dirs: List[Path] = [d]
        await scan_dir(d, dirs)
        for p in dirs:
            await scan_files(p, files)
        return files
    return dict()


@invoke_safe
async def scan_files(d: Path, files: Dict[FileType, List[Path]]):
    for f in d.iterdir():
        if f.is_file():
            for key in FileType:
                if f.suffix.endswith(key.value):
                    files[key].append(f)


@invoke_safe
async def scan_dir(d: Path, dirs: List[Path]):
    for x in d.iterdir():
        if x.is_dir():
            await scan_dir(x, dirs)
            dirs.append(x)
