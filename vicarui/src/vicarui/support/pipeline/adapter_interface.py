from abc import ABC, abstractmethod
from typing import Optional, Generic, TypeVar

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin

T = TypeVar('T')


class WrapperRegressor(BaseEstimator, RegressorMixin, ABC, Generic[T]):

    @abstractmethod
    def fit(self, X_, y, sample_weight: np.ndarray = None) -> T:
        """
        Sample weight works with RANSAC
        """
        pass

    @abstractmethod
    def predict(self, X_, y=None):
        pass

    @property
    @abstractmethod
    def errors_(self) -> np.ndarray:
        """
        Same order as coef_
        """
        pass

    @property
    @abstractmethod
    def coef_(self) -> np.ndarray:
        """
        Coefficients in the order that they are to be represented in the equation
        """
        pass

    @property
    @abstractmethod
    def intercept_(self) -> Optional[float]:
        """
        Return intercept if fitted else none
        """
        pass

    @property
    @abstractmethod
    def std_(self) -> Optional[float]:
        """
        Standard error prediction
        """
        pass


__all__ = ['WrapperRegressor']
