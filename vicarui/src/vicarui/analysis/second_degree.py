from typing import Tuple

import numpy as np

from .pipe import Pipe


def roots_2nd_deg(eq1: np.ndarray, eq2: np.ndarray):
    """
    Equation coefficients from largest to smallest

    Returns roots from largest to smallest
    """
    return -np.sort(-np.roots(eq1 - eq2))


def error_estimate_for_y(bg: Pipe, fg: Pipe):
    """
    Trying to combine the standard errors of estimates of teh two models

    SQRT(SCALE) ~ STD Error of Prediction
    """
    return np.sqrt(bg.base.result_.scale + fg.base.result_.scale)


def contrast_2nd_deg(eq1: np.ndarray, eq2: np.ndarray) -> Tuple[float, float]:
    """
    Equation coefficients from largest to smallest

    Returns distance if all roots real
    """
    equation = eq1 - eq2
    roots: np.ndarray = np.roots(equation)
    try:
        if np.alltrue(np.isreal(roots)):
            x_val = -0.5 * equation[1] / equation[0]
            d = equation[0] * np.power(x_val, 2) + equation[1] * x_val + equation[2]
            return x_val, d,
    except Exception as e:
        from .internal import log
        log.exception("Exception in contrast", exc_info=e)
    return np.NAN, np.NAN


def integrate_2nd_deg(eq1: np.ndarray, eq2: np.ndarray) -> float:
    """
    Equation coefficients from largest to smallest

    Returns Area between curves
    """
    equation = eq1 - eq2
    roots: np.ndarray = np.roots(equation)
    if np.alltrue(np.isreal(roots)):
        try:
            vals = [
                np.reciprocal(float(i))
                * j
                * (np.power(np.max(roots), i) - np.power(np.min(roots), i))
                for i, j in enumerate(equation[::-1], start=1)
            ]
            return np.sum(vals)
        except Exception as e:
            from .internal import log
            log.exception("Exception in integral", exc_info=e)
    return np.NAN


def contrast_error_2nd_deg(bg: Pipe, fg: Pipe) -> float:
    """
    Evaluates the maximum error for x, and contrast
    """
    return error_estimate_for_y(bg, fg)


def integral_error_2nd_deg(start: float, end: float, contrast_error: float) -> float:
    """
    Evaluates the maximum error for the integral
    """
    return np.abs(end - start) * contrast_error


def additional_2nd_deg_info(bg: Pipe, fg: Pipe, suppress: bool) -> Tuple[str, np.ndarray]:
    from .tex import sci_4
    eq1 = bg.eq
    eq2 = fg.eq
    roots = roots_2nd_deg(eq1, eq2)
    out = "  "
    if np.alltrue(np.isreal(roots)):
        x_max, contrast = contrast_2nd_deg(eq1, eq2)
        integral = integrate_2nd_deg(eq1, eq2)

        contrast_error = contrast_error_2nd_deg(bg, fg)
        integral_error = (roots[0] - roots[1]) * contrast_error

        from .internal import log

        newline = '\n'

        if not suppress:
            log.info(
                f"""
                Values:
                - BG EQ: {str(eq1).replace(newline, "")} ERR: {str(bg.errors).replace(newline, "")}
                - FG EQ: {str(eq2).replace(newline, "")} ERR: {str(fg.errors).replace(newline, "")}
                - Contrast: {contrast:.7e}    ERR: {contrast_error:.7e} 
                - X Pos:    {x_max:.7e}
                - Integral: {integral:.7e}    ERR: {integral_error:.7e}
                """
            )

        out += r"    $\Delta_{max}=" f" {sci_4(contrast)}" r"\pm "
        out += f"{sci_4(contrast_error)}" f", x={x_max:3.2f} $"
        out += fr"  $\int\Delta={sci_4(integral)} "
        out += r"\pm" f"{sci_4(integral_error)}, x_0={roots[1]:3.2f}, x_1={roots[0]:3.2f}$"
    return out, roots
