from typing import NoReturn

import numpy as np
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

from .pipe import ransac, OLSWrapper
from .wrapper import ImageWrapper
from ..support import info


def br_reduction(
        image: ImageWrapper,
        degree: int = 3,
) -> NoReturn:
    """
    Polynomial background reduction and image normalization

    Fits once for both axes in image and combines the result.

    Stores everything in the image wrapper

    Parameters
    ----------
    image:      ImageWrapper
                Image instance

    degree:     int
                Polynomial fit degree

    Returns
    -------
    NoReturn
    """

    img: np.ndarray
    border = image.border
    if image.is_border_valid(border):
        img = image.sanitized[border + 1:-1 * border, border + 1:-1 * border]
    else:
        img = image.sanitized
    gen_bg: bool = True

    if image.has_background:
        minus = image.background
        gen_bg = not (
                img.shape == minus.shape
                and image.degree == degree
        )

    image.border = border

    try:
        if gen_bg:
            reg = ransac(min_samples=int(np.sqrt(img.shape[0] * img.shape[1])), max_iter=100)
            pipe = make_pipeline(
                PolynomialFeatures(degree=degree, include_bias=False),
                reg
            )

            indexes = list()
            for i in range(0, len(img)):
                for j in range(0, len(img[0])):
                    indexes.append([i, j])
            indexes = np.asarray(indexes)
            pipe.fit(indexes, img.ravel())
            pred = pipe.predict(indexes)
            mse = mean_squared_error(img.ravel(), pred)
            minus = pred.reshape(img.shape)
            inlier_mask = reg.inlier_mask_.reshape(img.shape)

            image.background = minus
            image.degree = degree
            image.mse = mse
            image.outliers = np.ma.masked_where(inlier_mask, inlier_mask)

            n = '\n'
            info(f"Background mse: {mse:.5e}")
            est: OLSWrapper = reg.estimator_
            info(
                f"Bacground (model direct):"
                f"\n- Coef:       {str(est.coef_).replace(n, '')}"
                f"\n- Intercept:  {str(est.intercept_).replace(n, '')}"
                f"\n- Errors:     {str(est.errors).replace(n, '')}"
            )
    except Exception as e:
        from ..support import handle_exception
        handle_exception(e)
        image.active = False
        image.normalized = False
