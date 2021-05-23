from typing import Tuple

import numpy as np
from scipy.optimize import least_squares
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import check_X_y
from sklearn.utils.validation import check_array, check_is_fitted


class OnePerRegression(RegressorMixin, BaseEstimator):
    """
    Regression model for k * x ** a + c
    """

    def __init__(self, initial_guess: Tuple[float, float, float] = (1, -1, 0)):
        """
        initial_guess:
        - Tuple[float, float, float]
        - k * x ^ a + b (k, a, b)

        Constrained as follows:
        - k[0,INF]
        - a[-15,0]
        - b[0,INF]
        """
        super(OnePerRegression, self).__init__()
        self.initial_guess = initial_guess

    def _constraint(self):
        return np.asarray((
            [0, -15, 0],
            [np.inf, -1, np.inf]
        ))

    def _more_tags(self):
        return {
            "poor_score": True
        }

    def fun(self, guess):
        k, a, b = guess[0:3]
        return self.y_ - k * np.float_power(self.x_, a) + b

    def fit(self, X, y):
        if y is None:
            raise ValueError()
        x, y = check_X_y(X, y, y_numeric=True, force_all_finite=True, dtype='float64')

        self.n_features_in_ = x.shape[1]
        self.x_ = np.average(x, axis=1)
        self.y_ = y

        solution = least_squares(
            self.fun,
            np.asarray(self.initial_guess).astype('float64'),
            bounds=self._constraint(),
            loss='huber'
        )

        self.coef_ = [solution.x[0], solution.x[1]]
        self.intercept_ = solution.x[2]

        return self

    def predict(self, X):
        check_is_fitted(self, 'coef_')
        x: np.ndarray = check_array(X, force_all_finite=True, dtype='float64')
        if x.shape[1] != self.n_features_in_:
            raise ValueError("Wrong number of features")
        x = np.average(X, axis=1)
        return self.coef_[0] * np.float_power(x, self.coef_[1]) + self.intercept_
