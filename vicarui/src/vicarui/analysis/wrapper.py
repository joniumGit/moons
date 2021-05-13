from typing import Optional

import numpy as np
from vicarutil.image import VicarImage


class ImageWrapper(object):
    image_data: VicarImage
    bg: Optional[np.ndarray]
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
        if border != 0:
            img = self.get_image()[border + 1:-1 * border, border + 1:-1 * border]
        else:
            img = self.get_image()
        if self.active:
            img = img - self.get_bg()
        if self.normalized:
            img = (img - np.min(img)) * 1 / (np.max(img) - np.min(img))
        return img

    def get_image(self):
        return self.image_data.data[0]

    def get_bg(self):
        return self.bg

    def get_degree(self):
        return self.bg_degree

    def is_normalized(self):
        return self.normalized

    def get_mse(self):
        return self.mse
