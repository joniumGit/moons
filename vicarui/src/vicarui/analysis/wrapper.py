from typing import Optional

import numpy as np
from vicarutil.image import VicarImage

from .fitting import to_zero_one


class ImageWrapper(object):
    image_data: VicarImage
    bg: Optional[np.ndarray]
    bg_outliers: Optional[np.ndarray]

    bg_degree: Optional[int]
    normalized: Optional[bool]
    mse: Optional[float]

    invalid_indices: Optional[np.ndarray]

    border: int
    active: bool

    def __init__(self, image: VicarImage):
        super(ImageWrapper, self).__init__()
        self.image_data = image

        self.bg = None
        self.bg_degree = None
        self.bg_outliers = None
        self.mse = None
        self.invalid_indices = None

        self.active = False
        self.normalized = False
        self.border = 0

    def add_bg(
            self,
            degree: int,
            bg: np.ndarray,
            mse: float
    ):
        self.bg_degree = degree
        self.bg = bg
        self.mse = mse

    def get_raw(self):
        return self.image_data

    def get_processed(self):
        border = self.border
        img = self.remove_invalid()
        if border != 0 and self.is_border_valid(border):
            img = img[border + 1:-1 * border, border + 1:-1 * border]
        if self.active:
            img = img - self.bg
        if self.normalized:
            img = to_zero_one(img)
        return img

    def get_image(self):
        return self.image_data.data[0]

    def is_border_valid(self, border: int):
        return border > 0 \
               and border * 2 + 20 < len(self.get_image()) \
               and border * 2 + 20 < len(self.get_image()[0])

    def remove_invalid(self) -> np.ndarray:
        img = self.get_image().copy()
        indices = list()
        for _i, line in enumerate(img):
            if np.alltrue(np.isclose(np.average(line), line)):
                indices.append(_i)
        if len(indices) != 0:
            self.invalid_indices = np.asarray(indices)
            return np.delete(img, indices, axis=0)
        img[np.logical_not(np.isfinite(img))] = np.average(img[np.isfinite(img)])
        return img
