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


def test_re_to_eq():
    from sklearn.preprocessing import Normalizer, PolynomialFeatures
    from sklearn.pipeline import make_pipeline
    from sklearn.linear_model import HuberRegressor
    from sklearn.metrics import mean_squared_error
    x = np.asarray([0, 1, 2, 2.2, 3, 3.4, 4, 5])
    y = np.asarray([0, 1, 2, 2.0, 3, 2.0, 4, 5])
    model = HuberRegressor()
    pipe = make_pipeline(Normalizer(), PolynomialFeatures(degree=2, include_bias=False), model)
    pipe.fit(x[..., None], y)
    n_y = pipe.predict(np.arange(0, 6)[..., None])
    true_y = np.asarray([0, 1, 2, 3, 4, 5])
    print(true_y)
    print(n_y)
    print(mean_squared_error(true_y, n_y))
    from vicarui.analysis.fitting import reg_to_eq
    poly = np.poly1d(reg_to_eq(model))
    assert np.equal(poly(Normalizer().fit_transform(np.arange(0, 6)[..., None])[:, 0]), n_y).all()
