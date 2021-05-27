from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import RANSACRegressor
from sklearn.preprocessing import FunctionTransformer

from .classes import *
from ..config import *
from ....pipe import Pipe, OLSWrapper


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
            name="reciprocal",
            color="blue",
            style="-",
            title=r"$\frac{k}{x} + b$""\n",
            reg=make_sac(OLSWrapper()),
            transforms=[
                FunctionTransformer(np.reciprocal, np.reciprocal),
            ],
        ),
        Pipe(
            name="log1p",
            color="magenta",
            style="-",
            title=r"$\log y = k\log x + b$""\n",
            reg=make_sac(TransformedTargetRegressor(
                regressor=OLSWrapper(),
                func=np.log1p,
                inverse_func=np.expm1
            )),
            transforms=[
                FunctionTransformer(np.log1p, np.expm1)
            ],
        )
    ]


__all__ = [
    'get_pipes',
    'Pipe'
]
