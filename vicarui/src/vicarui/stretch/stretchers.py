import tkinter as tk
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional, Dict, List, Tuple, Union

from astropy.visualization import *
from sklearn.preprocessing import normalize as sk_normalize


class Dir(Enum):
    """Anchor points"""
    NORTH = "n"
    SOUTH = "s"
    EAST = "e"
    WEST = "w"
    NORTHWEST = "nw"
    NORTHEAST = "ne"
    SOUTHWEST = "sw"
    SOUTHEAST = "se"


class Fill(Enum):
    """Fill directions"""
    X = "ew"
    Y = "ns"
    BOTH = "nsew"


class GridConstraints:
    """Layout for grid"""
    fill: Optional[Fill]
    anchor: Optional[Dir]
    spanx: int = 0
    spany: int = 0
    col: int = 0
    row: int = 0
    padx: int = 0

    def __init__(
            self,
            fill: Fill = None,
            anchor: Dir = None,
            spanx: int = 0,
            spany: int = 0,
            col: int = 0,
            row: int = 0,
            padx: int = 0
    ) -> None:
        super().__init__()
        self.fill = fill
        self.anchor = anchor
        self.spanx = spanx
        self.spany = spany
        self.col = col
        self.row = row
        self.padx = padx

    def spanx(self, width: int) -> 'GridConstraints':
        self.spanx = width
        return self

    def spany(self, height: int) -> 'GridConstraints':
        self.spany = height
        return self

    def col(self, column: int) -> 'GridConstraints':
        self.col = column
        return self

    def row(self, row: int) -> 'GridConstraints':
        self.row = row
        return self

    def next_row(self):
        self.row += 1

    def next_column(self):
        self.col += 1

    def fill(self, fill: Fill) -> 'GridConstraints':
        self.fill = fill
        return self

    def padx(self, pad: int) -> 'GridConstraints':
        self.padx = pad
        return self

    def get(self) -> Dict[str, Any]:
        """Get defined values as a dict to spread for grid function"""
        values = dict()
        sticky = ""
        if self.fill == Fill.Y:
            sticky += "ns"
            if self.anchor == Dir.EAST or self.anchor == Dir.WEST:
                sticky += self.anchor
            elif self.anchor == Dir.NORTHEAST or Dir.SOUTHEAST:
                sticky += Dir.EAST.value
            elif self.anchor == Dir.NORTHWEST or Dir.SOUTHWEST:
                sticky += Dir.WEST.value
        elif self.fill == Fill.X:
            if self.anchor == Dir.NORTH or self.anchor == Dir.SOUTH:
                sticky += self.anchor
            elif self.anchor == Dir.NORTHEAST or Dir.NORTHWEST:
                sticky += Dir.NORTH.value
            elif self.anchor == Dir.SOUTHEAST or Dir.SOUTHWEST:
                sticky += Dir.SOUTH.value
            sticky += "ew"
        elif self.fill == Fill.BOTH:
            sticky += "nsew"
        if sticky == "" and self.anchor is not None:
            sticky += self.anchor.value
        values["sticky"] = sticky
        if self.spanx != 0:
            values["columnspan"] = self.spanx
        if self.spany != 0:
            values["rowspan"] = self.spany
        if self.padx != 0:
            values["padx"] = self.padx
        values["column"] = self.col
        values["row"] = self.row
        return values


def _default_label_constraint() -> GridConstraints:
    return GridConstraints(anchor=Dir.WEST, col=0, row=1, padx=20)


def _default_box_constraint() -> GridConstraints:
    return GridConstraints(anchor=Dir.EAST, col=1, row=1, padx=10, fill=Fill.X)


class Stretch(tk.Frame, ABC):
    """Base class for a stretcher"""
    __selected = tk.IntVar

    def __init__(self, name: str, master=None, cnf=None, **kw):
        if cnf is None:
            cnf = {}
        super().__init__(master=master, cnf=cnf, **kw)
        c = GridConstraints(anchor=Dir.WEST)
        self.__selected = tk.IntVar()
        tk.Checkbutton(
            self,
            text=name,
            variable=self.__selected,
            onvalue=1,
            offvalue=0
        ).grid(**c.get())
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, minsize=180)

    @abstractmethod
    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        pass

    def is_selected(self) -> bool:
        return self.__selected.get()


class StretcherBase(Stretch, ABC):
    """Base class for more complex stretchers"""
    val_min: List[Optional[float]]
    val_max: List[Optional[float]]
    s_vars: Dict[int, tk.StringVar]

    def __init__(self, name: str, master=None, cnf=None, **kw):
        super().__init__(name=name, master=master, cnf=cnf, **kw)
        self.val_min = list()
        self.val_max = list()
        self.s_vars = dict()

    def add_make_input(self, _id: int, c: GridConstraints):
        vmax = self.val_max
        vmin = self.val_min

        def __validate(new_value: str):
            if new_value == "":
                return True
            try:
                f = float(new_value)
                if len(vmin) != 0:
                    try:
                        if f < vmin[_id]:
                            return False
                    except IndexError:
                        pass
                if len(vmax) != 0:
                    try:
                        if f > vmax[_id]:
                            return False
                    except IndexError:
                        pass
                return True
            except ValueError:
                return False

        v_command = (self.register(__validate), '%P')
        v = tk.StringVar()
        self.s_vars[_id] = v
        tk.Entry(self, validate="key", validatecommand=v_command, textvariable=v).grid(**c.get())

    def get_value(self, _id: int) -> Optional[float]:
        try:
            return float(self.s_vars[_id].get())
        except Exception:
            return None


class SimpleStretch(Stretch, ABC):
    """Simple stretch that doesn't require arguments"""

    def __init__(self, name: str, master=None, cnf=None, **kw):
        if cnf is None:
            cnf = {}
        super().__init__(master=master, name=name, cnf=cnf, **kw)


class HEQ(SimpleStretch):
    """Histogram Equalization"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Histogram EQ", master, cnf, **kw)

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        return HistEqStretch(image)


class SQRT(SimpleStretch):
    """Square-root stretch"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Square-root Stretch", master, cnf, **kw)

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        return SqrtStretch()


class SQUARE(SimpleStretch):
    """Squared stretch"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Squared stretch", master, cnf, **kw)

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        return SquaredStretch()


class LINEAR(SimpleStretch):
    """Linear stretch"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Linear stretch", master, cnf, **kw)

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        return LinearStretch()


class SINH(StretcherBase):
    """Sinh Stretcher"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Sinh", master, cnf, **kw)
        self.val_min.append(0)
        self.val_max.append(1)
        tk.Label(self, text="a value (default 1/3): ").grid(**_default_label_constraint().get())
        self.add_make_input(0, _default_box_constraint())

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        v = self.get_value(0)
        if v is not None:
            return SinhStretch(v)
        return SinhStretch()


class ASINH(StretcherBase):
    """ASinh Stretcher"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("ASinh", master, cnf, **kw)
        self.val_min.append(0)
        self.val_max.append(1)
        tk.Label(self, text="a value (default 0.1): ").grid(**_default_label_constraint().get())
        self.add_make_input(0, _default_box_constraint())

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        v = self.get_value(0)
        if v is not None:
            return AsinhStretch(v)
        return AsinhStretch()


class LOG(StretcherBase):
    """Logarithmic Stretcher"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Log", master, cnf, **kw)
        self.val_min.append(0)
        tk.Label(self, text="a value (default 1000): ").grid(**_default_label_constraint().get())
        self.add_make_input(0, _default_box_constraint())

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        v = self.get_value(0)
        if v is not None:
            return LogStretch(v)
        return LogStretch()


class PLAW(StretcherBase):
    """Power law Stretcher"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Power Law", master, cnf, **kw)
        self.val_min.append(0)
        tk.Label(self, text="a value: ").grid(**_default_label_constraint().get())
        self.add_make_input(0, _default_box_constraint())

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        v = self.get_value(0)
        if v is not None:
            return PowerStretch(v)
        return PowerStretch(1)


class PDIST(StretcherBase):
    """Power distribution Stretcher"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Power Distribution", master, cnf, **kw)
        self.val_min.append(0)
        tk.Label(self, text="a value (default: 1000): ").grid(**_default_label_constraint().get())
        self.add_make_input(0, _default_box_constraint())

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        v = self.get_value(0)
        if v is not None:
            return PowerDistStretch(v)
        return PowerDistStretch()


class CBIAS(StretcherBase):
    """Contrast Bias Stretcher"""

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__("Contrast-Bias", master, cnf, **kw)
        c0 = _default_label_constraint()
        c1 = _default_box_constraint()
        tk.Label(self, text="Contrast: ").grid(**c0.get())
        self.add_make_input(0, c1)
        c0.next_row()
        c1.next_row()
        tk.Label(self, text="Bias: ").grid(**c0.get())
        self.add_make_input(1, c1)

    def get_stretch(self, image: np.ndarray = None) -> BaseStretch:
        v0 = self.get_value(0)
        v1 = self.get_value(1)
        if v0 is not None and v1 is not None:
            return ContrastBiasStretch(v0, v1)
        return ContrastBiasStretch(0, 0)


STRETCHERS = [HEQ, SQRT, SQUARE, LINEAR, SINH, ASINH, LOG, PLAW, PDIST, CBIAS]


def make_panel(master: Union[tk.Frame, tk.Tk]) -> Tuple[tk.Frame, List[Stretch]]:
    rf = tk.Frame(master=master)
    c = GridConstraints(fill=Fill.X)
    rl = list()
    rf.grid_columnconfigure(0, weight=1)
    for cls in STRETCHERS:
        i = cls(master=rf)
        i.grid(**c.get())
        rl.append(i)
        c.next_row()
    return rf, rl


def __make_compound(stretches: List[BaseStretch]) -> BaseStretch:
    _len = len(stretches)
    cmb_s = list()
    if _len > 1:
        if _len % 2 != 0:
            for s1, s2 in zip(*[iter(stretches[1:])] * 2):
                cmb_s.append(CompositeStretch(s1, s2))
            cmb_s.append(stretches[0])
        else:
            for s1, s2 in zip(*[iter(stretches)] * 2):
                cmb_s.append(CompositeStretch(s1, s2))
    else:
        cmb_s.append(stretches[0])
    if len(cmb_s) > 1:
        return __make_compound(cmb_s)
    return cmb_s[0]


def get_stretch(selection: List[Stretch], image: np.ndarray) -> BaseStretch:
    rs = list()
    for s in selection:
        if s.is_selected():
            rs.append(s.get_stretch(image))
    if len(rs) > 0:
        return __make_compound(rs)
    else:
        return LinearStretch()


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
