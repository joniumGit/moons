from functools import cached_property
from typing import Optional, Tuple

import numpy as np
from vicarutil.image import VicarImage


class ImageWrapper(object):
    _raw: VicarImage

    invalid_indices: Optional[np.ndarray]
    border: int
    active: bool

    _bg: Optional[np.ndarray]
    _bg_degree: Optional[int]
    _bg_outliers: Optional[np.ndarray]
    _normalized: Optional[bool]
    _mse: Optional[float]

    def __init__(self, image: VicarImage):
        super(ImageWrapper, self).__init__()
        self._raw = image

        self._bg = None
        self._mse = None
        self._bg_degree = None
        self._bg_outliers = None

        self.invalid_indices = None
        self.active = False
        self.normalized = False
        self.border = 0

    @staticmethod
    def normalize(img: np.ndarray):
        return (img - np.min(img)) * 1 / (np.max(img) - np.min(img))

    @property
    def raw(self) -> VicarImage:
        return self._raw

    @property
    def original(self) -> np.ndarray:
        return self.raw.data[0]

    @cached_property
    def sanitized(self) -> np.ndarray:
        img = self.original.copy()
        indices = list()
        for _i, line in enumerate(img):
            if np.alltrue(np.isclose(np.average(line), line)):
                indices.append(_i)
        if len(indices) != 0:
            self.invalid_indices = np.asarray(indices)
            return np.delete(img, indices, axis=0)
        img[np.logical_not(np.isfinite(img))] = np.average(img[np.isfinite(img)])
        return img

    def is_border_valid(self, border: int) -> bool:
        shape = self.sanitized.shape
        return (
                border > 0
                and border * 2 + 20 < shape[0]
                and border * 2 + 20 < shape[1]
        )

    @property
    def shape(self) -> Tuple[int, int]:
        border = self.border
        shape = self.sanitized.shape
        if border != 0 and self.is_border_valid(border):
            return shape[0] - 2 * border, shape[1] - 2 * border
        else:
            return shape

    @property
    def processed(self) -> np.ndarray:
        border = self.border
        img = self.sanitized
        if border != 0 and self.is_border_valid(border):
            img = img[border + 1:-1 * border, border + 1:-1 * border]
        if self.active:
            img = img - self.background
        if self.normalized:
            img = self.normalize(img)
        return img

    @property
    def has_background(self) -> bool:
        return self._bg is not None

    @property
    def background(self) -> np.ndarray:
        if self.active:
            return self._bg
        else:
            return np.zeros(self.shape)

    @background.setter
    def background(self, bg: np.ndarray):
        self._bg = bg

    @property
    def degree(self) -> int:
        return self._bg_degree or -1

    @degree.setter
    def degree(self, deg: int):
        self._bg_degree = deg

    @property
    def mse(self) -> float:
        if self.active:
            return self._mse
        else:
            return -1.0

    @mse.setter
    def mse(self, mse: float):
        self._mse = mse

    @property
    def outliers(self) -> np.ndarray:
        if self.active:
            return self._bg_outliers
        else:
            return np.zeros(self.shape)

    @outliers.setter
    def outliers(self, outliers: np.ndarray):
        self._bg_outliers = outliers


__all__ = ['ImageWrapper']
