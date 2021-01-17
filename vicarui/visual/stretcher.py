import tkinter as tk
from abc import ABC, abstractmethod
from typing import List

from astropy.visualization import *
from sklearn.preprocessing import normalize as sk_normalize


def normalize(image: np.ndarray) -> np.ndarray:
    normalized: List[np.ndarray] = []
    if len(image.shape) == 3:
        for arr in image:
            normalized.append(sk_normalize(arr))
    elif len(image.shape) == 2:
        return np.asarray(sk_normalize(image.copy()))
    else:
        raise ValueError("Unable to normalize image of size: " + str(image.shape))
    return np.asarray(normalized)


__stretchers = {
    "Histogram equalization": HistEqStretch,  # ok
    "Sinh": SinhStretch,  # ok
    "Sqrt(x)": SqrtStretch,  # ok
    "X^2": SquaredStretch,  # ok
    "Log": LogStretch,  # ok
    "Asinh": AsinhStretch,  # ok
    "Contrast-Bias": ContrastBiasStretch,
    "Linear": LinearStretch,
    "Power Law": PowerStretch,
    "Power Distribution": PowerDistStretch,
}


class Stretcher(tk.Frame, ABC):
    on_var = tk.IntVar(0)
    row = 0
    column = 0
    image: np.ndarray

    def __init__(self, root: tk.Frame, name: str, image: np.ndarray):
        super().__init__(master=root)
        tk.Checkbutton(
            self,
            text=name,
            variable=self.on_var,
            onvalue=1,
            offvalue=0
        ).grid(row=0, column=0, sticky="w")
        self.column += 1
        self.image = image

    @abstractmethod
    def get_stretch(self) -> BaseStretch:
        pass


class HEQ(Stretcher):

    def get_stretch(self) -> BaseStretch:
        return HistEqStretch(self.image)


class SQRT(Stretcher):

    def get_stretch(self) -> BaseStretch:
        return SqrtStretch()


class SQUARE(Stretcher):

    def get_stretch(self) -> BaseStretch:
        return SquaredStretch()


class NumberStretch(Stretcher, ABC):
    a: tk.StringVar

    def __init__(self, root: tk.Frame, name: str, image: np.ndarray, min_val: int = None, max_val: int = None):
        super().__init__(root, name, image)
        self.min_val = min_val
        self.max_val = max_val
        vcmd = (self.register(self.__validate), '%P')
        e = tk.Entry(self).grid(
            row=0,
            column=self.column,
            variable=self.a,
            validate="key",
            validatecommand=vcmd,
            sticky="nw"
        )
        self.column += 1
        tk.Label(
            self,
            text="(" + str(min_val) + ", " + str(max_val) + ")"
        ).grid(row=0, column=self.column, sticky="w")
        self.column += 1

    def __validate(self, new_value: str):
        try:
            f = float(new_value)
            if (self.min_val is not None and f < self.min_val) or (self.max_val is not None and f > self.max_val):
                return False
            return True
        except ValueError:
            return False


class SINH(NumberStretch):

    def __init__(self, root: tk.Frame, name: str, image: np.ndarray):
        super().__init__(root, name, image, min_val=0, max_val=1)

    def get_stretch(self) -> BaseStretch:
        if self.a.get() is not None and self.a.get().strip() != '':
            return SinhStretch(float(self.a.get()))
        return SinhStretch()


class LOG(NumberStretch):

    def __init__(self, root: tk.Frame, name: str, image: np.ndarray):
        super().__init__(root, name, image, min_val=0)

    def get_stretch(self) -> BaseStretch:
        if self.a.get() is not None and self.a.get().strip() != '':
            return LogStretch(float(self.a.get()))
        return LogStretch()


class ASINH(NumberStretch):

    def __init__(self, root: tk.Frame, name: str, image: np.ndarray):
        super().__init__(root, name, image, min_val=0, max_val=1)

    def get_stretch(self) -> BaseStretch:
        if self.a.get() is not None and self.a.get().strip() != '':
            return AsinhStretch(float(self.a.get()))
        return AsinhStretch()
