from typing import Tuple

import numpy as np

from .pipe import Pipe


def roots_2nd_deg(eq1: np.ndarray, eq2: np.ndarray):
    """
    Equation coefficients from largest to smallest

    Returns roots from largest to smallest
    """
    return -np.sort(-np.roots(eq1 - eq2))


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
            return x_val, d
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


def error_estimate_for_x(bg: Pipe, fg: Pipe):
    """
    Estimate by values from covariance matrix
    """
    #       0,C     1,B     2,A
    # 0,C   V
    # 1,B   BC      V
    # 2,A   AC      AB      V
    eq = bg.eq - fg.eq
    bg_cov = bg.base.result_.cov_params()
    bg_ab = bg_cov[2, 1]
    fg_cov = bg.base.result_.cov_params()
    fg_ab = fg_cov[2, 1]
    d_b = np.reciprocal(2 * eq[0])
    d_a = np.divide(eq[1], 2 * eq[0] ** 2)
    err_squared = d_b ** 2 * (fg_cov[1, 1] + bg_cov[1, 1]) + d_a ** 2 * (fg_cov[2, 2] + bg_cov[2, 2])
    err_squared += 2 * d_b * d_a * (-fg_ab - bg_ab)

    return np.sqrt(err_squared)


def error_estimate_for_y(bg: Pipe, fg: Pipe):
    """
    Trying to combine the standard errors of estimates of teh two models
    """
    return np.sqrt(bg.base.result_.scale + fg.base.result_.scale)


def contrast_error_2nd_deg(bg: Pipe, fg: Pipe) -> Tuple[float, float]:
    """
    Evaluates the maximum error for x, and contrast
    """
    return error_estimate_for_x(bg, fg), error_estimate_for_y(bg, fg)


def additional_2nd_deg_info(bg: Pipe, fg: Pipe, suppress: bool) -> Tuple[str, np.ndarray]:
    from .tex import sci_4
    eq1 = bg.eq
    eq2 = fg.eq
    roots = roots_2nd_deg(eq1, eq2)
    out = "  "
    if np.alltrue(np.isreal(roots)):
        x_val, d = contrast_2nd_deg(eq1, eq2)
        x_err, c_err = contrast_error_2nd_deg(bg, fg)
        integral = integrate_2nd_deg(eq1, eq2)

        from .internal import log
        from .tex import sci_2

        newline = '\n'

        if not suppress:
            log.info(
                f"""
                Values:
                - BG EQ: {str(eq1).replace(newline, "")} ERR: {str(bg.errors).replace(newline, "")}
                - FG EQ: {str(eq2).replace(newline, "")} ERR: {str(fg.errors).replace(newline, "")}
                - Contrast: {d:.7e}    ERR: {c_err:.7e} 
                - X Pos:    {x_val:.7e}    ERR: {x_err:.7e}
                - Integral: {integral:.7e}
                """
            )

        out += r"    $\Delta_{max}=" f" {sci_4(d)}" r"\pm "
        out += f"{sci_4(c_err)}" f", x={x_val:3.2f} " r"\pm " f" {sci_2(x_err)}$"
        out += fr"  $\int\Delta={sci_4(integral)}, x_0={roots[1]:3.2f}, x_1={roots[0]:3.2f}$"
    return out, roots
