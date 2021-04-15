from typing import Tuple

import numpy as np
from vicarutil.image import VicarImage


def br_reduction(image: VicarImage) -> Tuple[np.ndarray, np.ndarray]:
    """
    Background reduction for image, also normalizes image data

    Parameters
    ----------
    image : VicarImage
            Image instance

    Returns
    -------
    data : tuple
           (Image data with reduced background, Reduction)
    """

    import numpy.polynomial.polynomial as poly

    img: np.ndarray = image.data[0].copy()[3:-2, 3:-2]
    indices = list()
    for _i, line in enumerate(img):
        if np.isclose(np.average(line), line[0]):
            indices.append(_i)
    img = np.delete(img, indices, axis=0)

    def reduction(arr: np.ndarray, mask: np.ndarray):
        r = np.arange(0, len(arr))
        averages = np.average(arr, axis=1)
        f = poly.polyval(r, poly.polyfit(r, averages, 3))
        for i in r:
            np.add(mask[i], f[i], mask[i])

    minus = np.zeros(img.shape)

    reduction(img, minus)
    reduction(img.T, minus.T)

    minus = minus / 2

    img = img - minus
    img = (img - np.min(img)) * 1 / (np.max(img) - np.min(img))

    return img, minus
