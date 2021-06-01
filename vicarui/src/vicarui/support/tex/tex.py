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


def sci_2(val: float, plus_sign: bool = False) -> str:
    return ('+' if plus_sign and val > 0 else '') + e(f"{val:.2e}")


def sci_4(val: float, plus_sign: bool = False) -> str:
    return ('+' if plus_sign and val > 0 else '') + e(f"{val:.4e}")


def sci_5(val: float, plus_sign: bool = False) -> str:
    return ('+' if plus_sign and val > 0 else '') + e(f"{val:.5e}")
