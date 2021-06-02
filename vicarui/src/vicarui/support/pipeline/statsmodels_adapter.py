from typing import Type, Optional

import numpy as np
from statsmodels.api import OLS
from statsmodels.api import add_constant
from statsmodels.base.model import LikelihoodModel, LikelihoodModelResults

from .adapter_interface import WrapperRegressor


class SMAdapter(WrapperRegressor):
    result_: Optional[LikelihoodModelResults]
    model_: Optional[LikelihoodModel]
    X_: Optional[np.ndarray]
    y_: Optional[np.ndarray]

    def __init__(self, fit_intercept: bool = True, model_cls: Type[LikelihoodModel] = OLS):
        self.model_cls = model_cls
        self.fit_intercept = fit_intercept

    def fit(self, X, y, sample_weight=None):
        self.X_ = X
        self.y_ = y
        if self.fit_intercept:
            self.model_ = self.model_cls(self.y_, add_constant(self.X_, has_constant='add'))
        else:
            self.model_ = self.model_cls(self.y_, self.X_)
        self.result_: LikelihoodModelResults = self.model_.fit()
        return self

    def predict(self, X, y=None):
        if self.fit_intercept:
            return self.result_.predict(add_constant(X, has_constant='add'))
        else:
            return self.result_.predict(X)

    @property
    def intercept_(self):
        """
        Intercept
        """
        return self.result_.params[0] if self.fit_intercept else None

    @property
    def coef_(self):
        """
        From largest to smallest C[n] * x^n + C[(n-1)] + x ^(n-1) + ....

        No intercept
        """
        return self.result_.params[1:][::-1] if self.fit_intercept else self.result_.params[::-1]

    @property
    def errors_(self):
        """
        Same order as coef, intercept last

        C[n] * x^n + C[(n-1)] + x ^(n-1) + ....
        """
        return np.asarray(self.result_.bse[::-1])

    @property
    def std_(self):
        return np.sqrt(self.result_.scale)


__all__ = ['SMAdapter']
