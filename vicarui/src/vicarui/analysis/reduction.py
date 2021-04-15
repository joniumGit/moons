from typing import Tuple

import numpy as np
from vicarutil.image import VicarImage


def br_reduction(
        image: VicarImage,
        reduce: bool = True,
        normalize: bool = True,
        degree: int = 3,
        border: int = 2
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Polynomial background reduction and image normalization

    Fits once for both axes in image and combines the result.

    If normalization is selected reduction result is normalized to [0, 1]

    Parameters
    ----------
    image:      VicarImage
                Image instance

    reduce:     bool
                Whether to do background reduction

    normalize:  bool
                Whether to normalize image data

    degree:     int
                Polynomial fit degree

    border:     int
                Amount of pixels to exclude from all sides

    Returns
    -------
    data:       tuple
                (Normalized image data with reduced background, Reduction data)
    """

    import numpy.polynomial.polynomial as poly

    img: np.ndarray = image.data[0].copy()[border + 1:-1 * border, border + 1:-1 * border]

    if reduce:
        indices = list()
        for _i, line in enumerate(img):
            if np.isclose(np.average(line), line[0]):
                indices.append(_i)
        img = np.delete(img, indices, axis=0)

        def reduction(arr: np.ndarray, mask: np.ndarray):
            r = np.arange(0, len(arr))
            averages = np.average(arr, axis=1)
            f = poly.polyval(r, poly.polyfit(r, averages, degree))
            for i in r:
                np.add(mask[i], f[i], mask[i])

        minus = np.zeros(img.shape)

        reduction(img, minus)
        reduction(img.T, minus.T)

        minus = minus / 2

        img = img - minus

    else:
        minus = np.zeros(img.shape)

    if normalize:
        img = (img - np.min(img)) * 1 / (np.max(img) - np.min(img))
        if reduce:
            minus = (minus - np.min(minus)) * 1 / (np.max(minus) - np.min(minus))

    return img, minus
