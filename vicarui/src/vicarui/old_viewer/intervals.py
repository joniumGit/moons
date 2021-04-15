import tkinter as tk
from abc import ABC, abstractmethod
from typing import Callable, Tuple, cast

from astropy.visualization import PercentileInterval, AsymmetricPercentileInterval, MinMaxInterval
from astropy.visualization import ZScaleInterval, BaseInterval, ManualInterval


def register_validator(self: tk.Frame, validator: Callable) -> Tuple[str, str]:
    return self.register(validator), "%P"


def class_validate_int(f: Callable) -> Callable:
    def wrapped_validate_int(self, new_value: str):
        try:
            return cast(f(self, int(new_value)), bool)
        except ValueError:
            return False

    return wrapped_validate_int


def class_validate_float(f: Callable) -> Callable:
    def wrapped_validate_float(self, new_value: str):
        try:
            return cast(f(self, float(new_value)), bool)
        except KeyError:
            return False

    return wrapped_validate_float


class SelectorBase(tk.Frame, ABC):
    on_var = tk.IntVar(0)
    row = 0
    column = 0

    def __init__(self, name: str, master=None, cnf=None, **kw):
        if cnf is None:
            cnf = {}
        super().__init__(master, cnf, **kw)
        tk.Checkbutton(
            self,
            text=name,
            variable=self.on_var,
            onvalue=1,
            offvalue=0
        ).grid(row=0, column=0, sticky="w")
        self.column += 1

    @abstractmethod
    def get_interval(self) -> BaseInterval:
        pass


class MinMax(SelectorBase):

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("MinMax", master, cnf, **kw)

    def get_interval(self) -> BaseInterval:
        return MinMaxInterval()


class AsymmetricPercentile(SelectorBase):
    lower: tk.StringVar
    upper: tk.StringVar

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Percentile 2", master, cnf, **kw)

    @class_validate_float
    def validate_min(self, new_value: float) -> bool:
        return isinstance(new_value, float)

    @class_validate_float
    def validate_max(self, new_value: float) -> bool:
        return isinstance(new_value, float)

    def get_interval(self) -> BaseInterval:
        return AsymmetricPercentileInterval(
            lower_percentile=float(self.lower.get()),
            upper_percentile=float(self.upper.get())
        )


class PercentileSelector(SelectorBase):
    percent: tk.StringVar

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Percentile 1", master, cnf, **kw)

    @class_validate_float
    def validate_percent(self, new_value: float):
        return isinstance(new_value, float) and new_value > 0

    def get_interval(self) -> BaseInterval:
        return PercentileInterval(float(self.percent.get()))


class ManualSelector(SelectorBase):
    v_min: tk.StringVar
    v_max: tk.StringVar

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Manual", master, cnf, **kw)

    @class_validate_float
    def validate_min(self, new_value: float) -> bool:
        return isinstance(new_value, float)

    @class_validate_float
    def validate_max(self, new_value: float) -> bool:
        return isinstance(new_value, float)

    def get_interval(self) -> BaseInterval:
        v_min: str = self.v_min.get()
        no_min = v_min is None or v_min == ""
        v_max: str = self.v_max.get()
        no_max = v_max is None or v_max == ""
        if no_min and no_max:
            return ManualInterval()
        elif no_max:
            return ManualInterval(vmin=float(v_min))
        elif no_min:
            return ManualInterval(vmax=float(v_max))
        else:
            return ManualInterval(vmin=float(v_min), vmax=float(v_max))


class ZScaleSelector(SelectorBase):
    n_samples: tk.StringVar
    contrast: tk.StringVar

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("ZScale", master, cnf, **kw)
        tk.Entry(self).grid(
            validate="key",
            validatecommand=register_validator(self, self.validate_n_samples)
        )
        tk.Entry(self).grid(
            validatecommand=register_validator(self, self.validate_contrast)
        )

    @class_validate_int
    def validate_n_samples(self, new_value: int) -> bool:
        return isinstance(new_value, int)

    @class_validate_float
    def validate_contrast(self, new_value: float) -> bool:
        return 0 <= new_value <= 1

    def get_interval(self) -> BaseInterval:
        n: str = self.n_samples.get()
        no_n = n is None or n == ""
        c: str = self.contrast.get()
        no_c = c is None or c == ""
        if no_n and no_c:
            return ZScaleInterval()
        elif no_n:
            return ZScaleInterval(contrast=float(c))
        elif no_c:
            return ZScaleInterval(nsamples=int(n))
        else:
            return ZScaleInterval(nsamples=int(n), contrast=float(c))
