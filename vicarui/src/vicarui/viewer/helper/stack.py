from pathlib import Path
from typing import List

import numpy as np
from vicarutil.image import read_image

from ..widget.filelist import FileListWidget
from ...support import start_progress, stop_progress, ImageWrapper


def stack(flw: FileListWidget, paths: List[Path]) -> ImageWrapper:
    try:
        flw.busy = True
        start_progress()
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
        data = np.asarray([img.data[0] for img in images])
        data = data - np.ma.mean(np.ma.masked_where(data, np.logical_not(np.isfinite(data))), keepdims=True, axis=0).data
        image.data = np.asarray([np.average(
            data,
            axis=0,
            weights=[float(img.labels['INSTRUMENT']['EXPOSURE_DURATION']) for img in images]
        )])
        flw.busy = False
        stop_progress()
        return ImageWrapper(image)
    except Exception:
        flw.busy = False
        stop_progress()
