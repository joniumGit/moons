from sklearn.linear_model import RANSACRegressor, LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer

from .classes import *
from ..config import *
from ....tex import sci_4


def to_eq(x: RANSACRegressor):
    return (
            "$\n"
            fr"$k: \, {sci_4(x.estimator_.coef_[0])}$"
            + (
                "\n"
                fr"$a: \, {sci_4(x.estimator_.coef_[1])}$"
                if len(x.estimator_.coef_) == 2 else ""
            )
            + "\n"
              fr"$b: \, {sci_4(x.estimator_.intercept_)}$$\,"
    )


def get_pipes(fits: List[Fit]):
    def make_sac(base, max_trials=1000):
        return RANSACRegressor(
            random_state=0,
            max_trials=max_trials,
            min_samples=int(np.sqrt(len(fits))),
            base_estimator=base,
        )

    return [
        Pipe(
            color="blue",
            style="-",
            title=r"$\frac{k}{x} + b$""\n",
            pipe_producer=lambda r: make_pipeline(FunctionTransformer(np.reciprocal, np.reciprocal), r),
            reg=make_sac(LinearRegression(n_jobs=-1)),
            eq_producer=to_eq
        ),
        Pipe(
            color="magenta",
            style="-",
            title=r"$\log y = a\log x + b$""\n",
            pipe_producer=lambda r: make_pipeline(FunctionTransformer(np.log1p, np.expm1), r),
            reg=make_sac(LinearRegression(n_jobs=-1)),
            eq_producer=to_eq,
            log=True
        )
    ]


__all__ = [
    'get_pipes'
]
