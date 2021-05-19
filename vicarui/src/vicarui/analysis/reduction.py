from typing import Tuple, Optional

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from .wrapper import ImageWrapper
from ..support import info


def remove_invalid(image: ImageWrapper) -> np.ndarray:
    img = image.get_image().copy()
    indices = list()
    for _i, line in enumerate(img):
        if np.alltrue(np.isclose(np.average(line), line)):
            indices.append(_i)
    if len(indices) != 0:
        image.invalid_indices = np.asarray(indices)
        return np.delete(img, indices, axis=0)
    img[np.logical_not(np.isfinite(img))] = np.average(img[np.isfinite(img)])
    return img


def br_reduction(
        image: ImageWrapper,
        reduce: bool = True,
        normalize: bool = True,
        degree: int = 3,
        border: int = 2
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Polynomial background reduction and image normalization

    Fits once for both axes in image and combines the result.

    If normalization is selected reduction result is normalized to [0, 1]

    Parameters
    ----------
    image:      ImageWrapper
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
                (Normalized image data with reduced background, Reduction data, MSE for reduction)
    """

    img: np.ndarray
    if border > 0 and border * 2 + 20 < len(image.get_image()):
        img = remove_invalid(image)[border + 1:-1 * border, border + 1:-1 * border]
    else:
        img = remove_invalid(image)
    minus: Optional[np.ndarray] = None
    gen_bg: bool = True

    mse = 0.0
    if image.get_bg() is not None:
        minus = image.get_bg()
        gen_bg = not (
                img.shape == minus.shape
                and image.get_degree() == degree
                and normalize == image.is_normalized()
        )
        mse = image.get_mse() or 0.0

    image.border = border

    try:
        if reduce and gen_bg:
            pipe = make_pipeline(PolynomialFeatures(degree=degree, include_bias=False), LinearRegression(n_jobs=-1))
            indexes = list()
            for i in range(0, len(img)):
                for j in range(0, len(img[0])):
                    indexes.append([i, j])
            indexes = np.asarray(indexes)
            pipe.fit(indexes, img.ravel())
            pred = pipe.predict(indexes)
            mse = mean_squared_error(img.ravel(), pred)
            minus = pred.reshape(img.shape)
            image.add_bg(degree, minus, mse)
            info(f"Background mse: {mse:.5e}")
        if reduce and minus is not None:
            img = img - minus
        else:
            minus = np.zeros(img.shape)
            mse = 0.0
    except Exception as e:
        from ..support import handle_exception
        handle_exception(e)
        mse = 0.0
        minus = np.zeros(img.shape)

    if normalize:
        img = (img - np.min(img)) * 1 / (np.max(img) - np.min(img))
        image.normalized = True
    else:
        image.normalized = False

    if reduce:
        image.active = True
    else:
        image.active = False

    return img, minus, mse
