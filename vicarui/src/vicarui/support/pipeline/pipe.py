from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union, cast, Generic, TypeVar

import numpy as np
from sklearn.base import TransformerMixin
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import RANSACRegressor
from sklearn.pipeline import make_pipeline, Pipeline

from .statsmodels_adapter import WrapperRegressor, SMAdapter
from ..tex import sci_4


def ine(o, d):
    return o if o is not None else d


def ransac(min_samples: int, max_iter: int = 1000) -> RANSACRegressor:
    return RANSACRegressor(
        random_state=0,
        max_trials=max_iter,
        min_samples=min_samples,
        base_estimator=SMAdapter()
    )


class PipeStr(Enum):
    KAB = "kab_str"
    LINEARIZED_POWERLAW = "kab_str"
    POLY = "poly_str"
    DELEGATE = "delegate"


T = TypeVar('T', bound=WrapperRegressor)


@dataclass(frozen=False)
class Pipe(Generic[T]):
    color: str = ""
    name: str = ""
    style: str = ""
    title: str = ""
    enabled: bool = True
    reg: Union[
        RANSACRegressor,
        TransformedTargetRegressor,
        T
    ] = field(default_factory=lambda: SMAdapter())
    transforms: List[TransformerMixin] = field(default_factory=lambda: list())
    display_style: PipeStr = PipeStr.KAB
    needs_errors: bool = False

    @property
    def base(self) -> T:
        reg: Union[RANSACRegressor, TransformedTargetRegressor, T]
        reg = self.reg
        while True:
            try:
                reg = reg.regressor_
            except AttributeError:
                try:
                    reg = reg.estimator_
                except AttributeError:
                    break
        return cast(T, reg)

    @property
    def errors(self):
        return self.base.errors_

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
        try:
            icep = reg.intercept_
            if icep is not None:
                return np.asarray([*reg.coef_, icep])
            return np.asarray(reg.coef_)
        except AttributeError:
            return np.asarray(reg.coef_)

    @property
    def kab_str(self) -> str:
        """
        K,A,B, Latex String
        """
        eq = self.eq
        param_cnt = len(eq)
        out: str = ""
        if param_cnt >= 1:
            out += f"$k:\\,{sci_4(eq[0])}$"
        if param_cnt == 2:
            out += f"\n$A:\\,{sci_4(eq[1])}$"
        elif param_cnt > 2:
            out += f"\n$B:\\,{sci_4(eq[1])}$\n$b:\\,{sci_4(eq[2])}$"
        out += "\n$\\Delta_{std}^{coef}:\\,("
        out += f"{','.join(sci_4(err) for err in self.errors)})$"
        return out

    @property
    def poly_str(self) -> str:
        eq = self.eq
        out = "$"
        out += ' '.join(reversed([
            sci_4(coef, plus_sign=True)
            + (fr" \cdot x^{idx} " if idx != 1 else r"\cdot x ")
            for idx, coef in enumerate(reversed(eq[:-1]), start=1)
        ]))
        out += f' {sci_4(eq[-1], plus_sign=True)}'
        out += '$\n' r'$ \Delta^{coef}_{std}(' + ','.join(sci_4(x) for x in self.errors) + ")"
        out += r'$ $\Delta^{model}_{std}: '
        out += f"{sci_4(self.base.std_)}$"
        return out

    def __str__(self):
        if self.display_style == PipeStr.DELEGATE:
            return str(self.base)
        else:
            return getattr(self, self.display_style.value)


class SMPipe(Pipe[SMAdapter]):
    """
    Statsmodels pipe
    """
    pass


__all__ = ['Pipe', 'ransac', 'PipeStr', 'SMPipe']
