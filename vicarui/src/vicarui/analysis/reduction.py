from typing import Tuple, Optional

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from .wrapper import ImageWrapper
from ..support import info


def ransac(
        x: np.ndarray,
        y: np.ndarray,
        out: np.ndarray,
        degree: int
):
    pipe = make_pipeline(
        PolynomialFeatures(degree=degree),
        LinearRegression()
    )
    pipe.fit(x[..., None], y)
    ny = pipe.predict(x[..., None])
    mse = mean_squared_error(y, ny)
    np.add(ny, out, out=out)
    return mse


def remove_invalid(img: np.ndarray):
    indices = list()
    for _i, line in enumerate(img):
        if np.isclose(np.average(line), line[0]):
            indices.append(_i)
    if len(indices) != 0:
        return np.delete(img, indices, axis=0)
    return img


def br_reduction(
        image: ImageWrapper,
        reduce: bool = True,
        normalize: bool = True,
        degree: int = 3,
        border: int = 2,
        old: bool = True
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

    old:        bool
                Using outlier detection

    Returns
    -------
    data:       tuple
                (Normalized image data with reduced background, Reduction data, MSE for reduction)
    """

    img: np.ndarray
    if border > 0:
        img = remove_invalid(image.get_image().copy()[border + 1:-1 * border, border + 1:-1 * border])
    else:
        img = remove_invalid(image.get_image().copy())
    minus: Optional[np.ndarray] = None
    gen_bg: bool = True

    if normalize:
        img = (img - np.min(img)) * 1 / (np.max(img) - np.min(img))

    mse = 0.0
    if image.get_bg() is not None:
        minus = image.get_bg()
        gen_bg = not (
                img.shape == minus.shape
                and image.get_degree() == degree
                and old == image.is_old()
                and normalize == image.is_normalized()
        )
        mse = image.get_mse() or 0.0

    if reduce and gen_bg:
        from collections import deque

        minus = np.zeros(img.shape)
        mse = deque()

        x = np.arange(0, len(img[0]))
        for i, line in enumerate(img):
            mse.append(ransac(x, line, minus[i], degree))

        x = np.arange(0, len(img))
        for i, line in enumerate(img.T):
            mse.append(ransac(x, line, minus.T[i], degree))

        mse = np.median(mse)
        minus = minus / 2

        if old:
            from sklearn.linear_model import RANSACRegressor
            sac = RANSACRegressor(
                base_estimator=LinearRegression(n_jobs=-1),
                max_trials=1000,
                random_state=0,
                loss='squared_loss'
            )
            pipe = make_pipeline(
                PolynomialFeatures(degree=degree),
                sac
            )
            indexes = list()
            for i in range(0, len(img)):
                for j in range(0, len(img[0])):
                    indexes.append([i, j])
            indexes = np.asarray(indexes)
            pipe.fit(indexes, minus.ravel())
            pred = pipe.predict(indexes)
            mse = np.median([mse, mean_squared_error(minus.ravel(), pred)])
            minus = pred.reshape(img.shape)

        image.add_bg(degree, minus, old, normalize, mse)
        info(f"Background mse (Using old: {old}): {mse:.5e}")

    if reduce and minus is not None:
        img = img - minus
    else:
        minus = np.zeros(img.shape)
        mse = 0.0

    return img, minus, mse
