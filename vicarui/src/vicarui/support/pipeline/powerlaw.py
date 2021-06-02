from typing import Optional, Tuple

import numpy as np

from .adapter_interface import WrapperRegressor
from ..tex import sci_4


def _f(x, A, k) -> np.ndarray:
    return A * np.float_power(x, k)


class Powerlaw(WrapperRegressor):
    coef_: Optional[np.ndarray] = None
    errors_: Optional[np.ndarray] = None
    cov_: Optional[np.ndarray] = None

    def __init__(self, initial_guess: Tuple[float, float] = (1, 1), max_iter: int = 1000):
        super(Powerlaw, self).__init__()
        self.initial_guess = initial_guess
        self.max_iter = max_iter

    def fit(self, X, y, sample_weight: np.ndarray = None):
        from scipy.optimize import curve_fit
        self.coef_, self.cov_ = curve_fit(
            _f,
            X[:, 0],
            y,
            p0=self.initial_guess,
            sigma=sample_weight,
            absolute_sigma=True,
            method='lm',
            maxfev=self.max_iter
        )
        if self.cov_ is not None:
            self.errors_ = np.sqrt(np.diag(self.cov_))
        else:
            self.errors_ = np.zeros(len(self.coef_)) + np.inf
        return self

    def predict(self, X, y=None):
        return self.coef_[0] * np.float_power(X[:, 0], self.coef_[1])

    @property
    def intercept_(self):
        """
        No Intercept
        """
        return None

    @property
    def std_(self):
        """
        We don't estimate std error for this
        """
        return None

    def __str__(self):
        return (
            f"$A:\\,{sci_4(self.coef_[0])}$\n$k:\\,{sci_4(self.coef_[1])}$"
            "\n$\\Delta_{coef}"
            f"({','.join(sci_4(err) for err in self.errors_)})$"
        )


__all__ = ['Powerlaw']
