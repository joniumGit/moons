from dataclasses import dataclass, field
from typing import List, Union, Type, cast

import numpy as np
from sklearn.base import TransformerMixin, BaseEstimator, RegressorMixin
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import RANSACRegressor
from sklearn.pipeline import make_pipeline, Pipeline
from statsmodels.api import add_constant
from statsmodels.regression.linear_model import RegressionResults, RegressionModel, OLS

from ..tex import sci_4


def ine(o, d):
    return o if o is not None else d


def ransac(min_samples: int, max_iter: int = 1000) -> RANSACRegressor:
    return RANSACRegressor(
        random_state=0,
        max_trials=max_iter,
        min_samples=min_samples,
        base_estimator=OLSWrapper()
    )


class OLSWrapper(BaseEstimator, RegressorMixin):

    def __init__(self):
        self.model_cls: Type[RegressionModel] = OLS

    def fit(self, X, y):
        self.X_ = X
        self.y_ = y
        self.model_ = self.model_cls(self.y_, add_constant(self.X_, has_constant='add'))
        self.result_: RegressionResults = self.model_.fit()
        return self

    def predict(self, X, y=None):
        return self.result_.predict(add_constant(X, has_constant='add'))

    @property
    def metrics_model(self):
        return self.result_

    @property
    def intercept_(self):
        """
        Intercept
        """
        return self.metrics_model.params[0]

    @property
    def coef_(self):
        """
        From largest to smallest C[n] * x^n + C[(n-1)] + x ^(n-1) + ....

        No intercept
        """
        return self.metrics_model.params[1:][::-1]

    @property
    def errors(self):
        """
        Same order as coef, intercept last

        C[n] * x^n + C[(n-1)] + x ^(n-1) + ....
        """
        return np.asarray([*self.metrics_model.bse[::-1]])


@dataclass(frozen=False)
class Pipe:
    color: str = ""
    name: str = ""
    style: str = ""
    title: str = ""
    enabled: bool = True
    reg: Union[RANSACRegressor, TransformedTargetRegressor, OLSWrapper] = field(default_factory=lambda: OLSWrapper())
    transforms: List[TransformerMixin] = field(default_factory=lambda: list())
    to_string: str = "kab_str"

    @property
    def base(self) -> OLSWrapper:
        reg: Union[RANSACRegressor, TransformedTargetRegressor, OLSWrapper]
        reg = self.reg
        while not isinstance(reg, OLSWrapper):
            try:
                reg = reg.regressor_
            except AttributeError:
                reg = reg.estimator_
        return cast(OLSWrapper, reg)

    @property
    def errors(self):
        return self.base.errors

    @property
    def line(self) -> Pipeline:
        if hasattr(self, 'pipe_'):
            return self.pipe_
        else:
            self.pipe_ = make_pipeline(
                *self.transforms,
                self.reg
            )
            return self.pipe_

    @property
    def eq(self) -> np.ndarray:
        reg = self.base
        return np.asarray([*reg.coef_, reg.intercept_])

    @property
    def kab_str(self) -> str:
        eq = self.eq
        use_a = len(eq) == 3
        return (
                "$\n"
                fr"$k: \, {sci_4(eq[0])}$"
                + (
                    "\n"
                    fr"$a: \, {sci_4(eq[1])}$"
                    if use_a else ""
                )
                + "\n"
                  fr"$b: \, {sci_4(eq[2 if use_a else 1])}$"
                + "\n"
                  fr"err: $(" + ','.join([sci_4(x) for x in self.errors]) + r")$$\,"
        )

    @property
    def poly_str(self) -> str:
        eq = self.eq
        out = ' '.join(reversed([
            sci_4(coef, plus_sign=True)
            + (fr" \cdot x^{idx} " if idx != 1 else r"\cdot x ")
            for idx, coef in enumerate(reversed(eq[:-1]), start=1)
        ]))
        out += f' {sci_4(eq[-1], plus_sign=True)}'
        out += '$\n' r'$ \Delta_{std}(' + ','.join([sci_4(x) for x in self.errors]) + ")"
        return out


__all__ = ['Pipe', 'OLSWrapper', 'ransac']
