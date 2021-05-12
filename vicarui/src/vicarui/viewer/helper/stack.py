from pathlib import Path
from typing import List

import numpy as np
from vicarutil.image import read_image

from ..widget.filelist import FileListWidget
from ...analysis import ImageWrapper
from ...support import start_progress, stop_progress


def stack(flw: FileListWidget, paths: List[Path]) -> ImageWrapper:
    flw.busy = True
    start_progress()
    try:
        images = list()
        for p in paths:
            images.append(read_image(p))
        image = images[0]
        try:
            times = [
                img['IDENTIFICATION']['IMAGE_TIME'] for img in images
            ]
            image['IDENTIFICATION']['IMAGE_NUMBER'] = f"Stack ({times[0]} - {times[1]})"
        except (KeyError, AttributeError):
            pass
        for img in images:
            for line in img.data[0]:
                if np.alltrue(np.isclose(line, np.average(line))):
                    line.fill(np.NINF)
        data = np.asarray([img.data / len(images) for img in images])
        image.data = np.sum(data, axis=0, dtype='float64', where=np.isfinite(data))
        return ImageWrapper(image)
    finally:
        flw.busy = False
        stop_progress()