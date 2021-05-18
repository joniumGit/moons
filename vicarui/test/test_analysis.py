import numpy as np
from vicarui.analysis.fitting import integrate_2nd_deg, contrast_2nd_deg, roots_2nd_deg

eq1 = np.asarray([0, 0, 0])
eq2 = np.asarray([1, -4, 0])
eq3 = np.asarray([-1, 4, 0])


def test_contrast():
    x_val, d = contrast_2nd_deg(eq1, eq2)
    assert 2 == x_val
    assert d == 4

    x_val, d = contrast_2nd_deg(eq3, eq2)
    assert 2 == x_val
    assert d == 8


def test_roots():
    roots = roots_2nd_deg(eq1, eq2)
    assert roots[1] == 0
    assert roots[0] == 4

    roots = roots_2nd_deg(eq2, eq3)
    assert roots[1] == 0
    assert roots[0] == 4


def test_integral():
    integral = integrate_2nd_deg(eq1, eq2)
    assert np.isclose(integral, 32 / 3)
    assert np.isclose(32 / 3, integral)

    integral2 = integrate_2nd_deg(eq3, eq2)
    assert integral2 == 2 * integral
