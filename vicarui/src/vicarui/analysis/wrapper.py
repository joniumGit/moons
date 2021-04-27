from typing import Optional

import numpy as np
from vicarutil.image import VicarImage


class ImageWrapper(object):
    __slots__ = 'image_data', 'bg', 'bg_degree', 'old', 'normalized', 'mse'

    image_data: VicarImage
    bg: Optional[np.ndarray]
    bg_degree: Optional[int]
    old: Optional[bool]
    normalized: Optional[bool]
    mse: Optional[float]

    def __init__(self, image: VicarImage):
        super(ImageWrapper, self).__init__()
        self.image_data = image
        self.bg = None
        self.old = None
        self.normalized = None
        self.bg_degree = None
        self.mse = None

    def add_bg(self, degree: int, bg: np.ndarray, old: bool, normalized: bool, mse: float):
        self.bg_degree = degree
        self.bg = bg
        self.old = old
        self.normalized = normalized
        self.mse = mse

    def get_raw(self):
        return self.image_data

    def get_image(self):
        return self.image_data.data[0]

    def get_bg(self):
        return self.bg

    def get_degree(self):
        return self.bg_degree

    def is_old(self):
        return self.old

    def is_normalized(self):
        return self.normalized

    def get_mse(self):
        return self.mse
