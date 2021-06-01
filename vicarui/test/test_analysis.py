import numpy as np
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import PolynomialFeatures
from vicarui.analysis.fitting.second_degree import integrate_2nd_deg, contrast_2nd_deg, roots_2nd_deg
from vicarui.support.pipeline import OLSWrapper, Pipe

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


def test_re_to_eq():
    x = np.asarray([0, 1, 2, 2.2, 3, 3.4, 4, 5])
    y = np.asarray([0, 1, 2, 2.0, 3, 2.0, 4, 5])
    original_y = np.asarray([0, 1, 2, 3, 4, 5])

    p = Pipe(
        reg=TransformedTargetRegressor(
            regressor=OLSWrapper(),
        ),
        transforms=[
            PolynomialFeatures(degree=1, include_bias=False)
        ]
    )

    pipe = p.line
    pipe.fit(x[..., None], y)
    predicted = pipe.predict(np.arange(0, 6)[..., None])

    print(f"true:           {original_y}")
    print(f"predicted:      {predicted}")
    print(f"mse:            {mean_squared_error(original_y, predicted)}")

    print(f"eq:             {p.eq}")
    print(f"str:            {p.poly_str}")

    poly = np.poly1d(p.eq)
    assert np.isclose(
        predicted,
        poly(np.arange(0, 6))
    ).all()
    assert np.isclose(
        predicted,
        np.polyval(np.polyfit(x, y, 1), np.arange(0, 6))
    ).all()
