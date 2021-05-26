from dataclasses import dataclass, field
from typing import List, Union

import numpy as np
from sklearn.base import TransformerMixin
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import RANSACRegressor
from sklearn.linear_model._base import LinearModel
from sklearn.pipeline import make_pipeline, Pipeline

from .tex import sci_4


def ine(o, d):
    return o if o is not None else d


@dataclass(frozen=False)
class Pipe:
    reg: Union[RANSACRegressor, LinearModel, TransformedTargetRegressor]
    color: str = ""
    name: str = ""
    style: str = ""
    title: str = ""
    transforms: List[TransformerMixin] = field(default_factory=lambda x: list())

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
        reg: Union[RANSACRegressor, LinearModel, TransformedTargetRegressor]
        reg = self.reg
        while isinstance(reg, RANSACRegressor) or isinstance(reg, TransformedTargetRegressor):
            # noinspection PyUnresolvedReferences
            try:
                reg = reg.regressor_
            except AttributeError:
                reg = reg.estimator_
        return np.asarray([*reg.coef_[::-1], reg.intercept_])

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
                  fr"$b: \, {sci_4(eq[2 if use_a else 1])}$$\,"
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
        return out


__all__ = ['Pipe']
