import asyncio as aio
from os import PathLike
from pathlib import Path
from typing import Dict, List, Union

from .filetype import FileType
from .logging import aio_invoke_safe_or_default, aio_invoke_safe, warn, aio_timed

@aio_timed
@aio_invoke_safe_or_default(default=dict())
async def scan(d: Union[str, PathLike]) -> Dict[FileType, List[Path]]:
    if d is not None:
        d = Path(d)
        files: Dict[FileType, List[Path]] = dict()
        for t in FileType:
            files[t] = list()
        dirs: List[Path] = [d]
        try:
            await aio.wait_for(scan_dir(d, dirs), 3)
            for p in dirs:
                await aio.wait_for(scan_files(p, files), 3)
            return files
        except aio.TimeoutError:
            warn("Files search timed out for path %s", str(d))
    return dict()


@aio_invoke_safe
async def scan_files(d: Path, files: Dict[FileType, List[Path]]):
    for f in d.iterdir():
        if f.is_file():
            for key in FileType:
                if f.suffix.endswith(key.value):
                    files[key].append(f)


@aio_invoke_safe
async def scan_dir(d: Path, dirs: List[Path]):
    children = list()

    def safe_iter(o):
        try:
            yield from o
        except PermissionError:
            yield from o

    try:
        for x in safe_iter(d.iterdir()):
            try:
                if x.is_dir():
                    children.append(aio.create_task(scan_dir(x, dirs)))
                    dirs.append(x)
            except PermissionError:
                pass
    except Exception as e:
        for c in children:
            c.cancel()
        raise e
    await aio.gather(*children)
