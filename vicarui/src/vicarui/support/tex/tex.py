import numpy as np


def e(s: str):
    part = s.split('e')
    try:
        p1 = int(part[1])
        if len(part) != 1:
            return part[0] + r"\cdot 10^{" + f"{'+' if p1 >= 0 else ''}{str(p1)}" + "}"
        else:
            return part[0]
    except IndexError:
        return "nan"


def sci_n(val: float, precision: int, plus_sign: bool = False) -> str:
    return (
            (
                '+'
                if plus_sign and val > 0
                else ''
            ) + e(("{0:." + str(precision) + "e}").format(val))
    ) if np.isfinite(val) else "nan"


def sci_2(val: float, plus_sign: bool = False) -> str:
    return sci_n(val, 2, plus_sign)


def sci_4(val: float, plus_sign: bool = False) -> str:
    return sci_n(val, 4, plus_sign)


def sci_5(val: float, plus_sign: bool = False) -> str:
    return sci_n(val, 5, plus_sign)
