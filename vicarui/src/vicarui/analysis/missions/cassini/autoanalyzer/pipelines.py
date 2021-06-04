import statsmodels.api as sm
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import RANSACRegressor
from sklearn.preprocessing import FunctionTransformer, PolynomialFeatures

from .classes import *
from ..config import *
from .....support import Pipe, SMAdapter, Powerlaw, PipeStr, partial_cls


def get_pipes(fits: List[Fit]):
    def make_sac(base, max_trials=500):
        return RANSACRegressor(
            random_state=0,
            max_trials=max_trials,
            min_samples=int(np.sqrt(len(fits))),
            base_estimator=base,
        )

    return [
        Pipe(
            enabled=False,
            name="rec",
            color="blue",
            style="-",
            title=r"$\frac{k}{x} + B$",
            reg=make_sac(SMAdapter()),
            transforms=[
                FunctionTransformer(np.reciprocal, np.reciprocal),
            ],
        ),
        Pipe(
            enabled=False,
            name="kox",
            color="blue",
            style="-",
            title=r"$\frac{k}{x}$""\n",
            reg=make_sac(SMAdapter(fit_intercept=False)),
            transforms=[
                FunctionTransformer(np.reciprocal, np.reciprocal),
            ],
        ),
        Pipe(
            enabled=True,
            name="ln-sac",
            color="magenta",
            style="-",
            title=r"$y = \exp(A) \cdot x^k$ (ln, ransac)",
            reg=make_sac(TransformedTargetRegressor(
                regressor=make_sac(SMAdapter()),
                func=np.log,
                inverse_func=np.exp
            )),
            transforms=[
                FunctionTransformer(np.log, np.exp)
            ],
            display_style=PipeStr.LINEARIZED_POWERLAW
        ),
        Pipe(
            enabled=False,
            name="ln-rls",
            color="magenta",
            style="-",
            title=r"$\log y = k\cdot\log x$ RLM",
            reg=TransformedTargetRegressor(
                regressor=SMAdapter(model_cls=partial_cls(sm.RLM, M=sm.robust.norms.HuberT())),
                func=np.log,
                inverse_func=np.exp
            ),
            transforms=[
                FunctionTransformer(np.log, np.exp)
            ],
        ),
        Pipe(
            enabled=False,
            name="poly-rec",
            color="green",
            style="-",
            title=r"$\frac{k}{x^2} + \frac{a}{x} + B$",
            reg=make_sac(SMAdapter()),
            transforms=[
                FunctionTransformer(np.reciprocal, np.reciprocal),
                PolynomialFeatures(degree=2, include_bias=False)
            ],
        ),
        Pipe(
            enabled=True,
            name="pwr",
            color="cyan",
            style="-",
            title=r"$y = A \cdot x^k$ (Weighted)",
            reg=Powerlaw(max_iter=1000),
            display_style=PipeStr.DELEGATE,
            needs_errors=True
        ),
        Pipe(
            enabled=False,
            name="pwr",
            color="cyan",
            style="-",
            title=r"$y = A \cdot x^k$",
            reg=Powerlaw(max_iter=1000),
            display_style=PipeStr.DELEGATE,
            needs_errors=False
        ),
        # Pipe(
        #     enabled=True,
        #     name="linear",
        #     color="black",
        #     style="-",
        #     title=r"$y = kx + A$",
        #     reg=make_sac(SMAdapter(fit_intercept=True), max_trials=300),
        #     display_style=PipeStr.KAB,
        #     needs_errors=False
        # ),
    ]


__all__ = [
    'get_pipes',
    'Pipe',
]
