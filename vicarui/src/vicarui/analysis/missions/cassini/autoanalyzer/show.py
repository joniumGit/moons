from collections import Generator
from typing import NoReturn

from matplotlib.pyplot import Axes
from sklearn.metrics import mean_squared_error

from .classes import *
from .definition import *
from .pipelines import get_pipes
from ..config import *
from ..helpers import ImageHelper
from .....support import sci_4


def show(
        helper: ImageHelper,
        results: Generator[Fit],
        plots: Dict[str, Axes],
) -> NoReturn:
    fits = list()
    for fit in results:
        if fit.is_finite():
            fits.append(fit)
    pipes = get_pipes(fits)

    px_dist = np.asarray([fit[2] for fit in fits])
    tgt_size = np.asarray(helper.per_px(helper.size_at_target))
    px_to_km = np.asarray([np.sqrt((d[0] * tgt_size[0]) ** 2 + (d[1] * tgt_size[1]) ** 2) for d in px_dist])

    """
    BORE
    |     SHADOW
    |    /
    | A /            A = bore_angle
    |  /
    | /
    |/______________________ IMAGE
    """
    bore_angle = helper.bore_angle
    dists: List[np.ndarray] = [px_to_km, px_to_km / np.sin(bore_angle)]
    contrast, integral = (np.asarray([fit[i] for fit in fits]) for i in (0, 1))

    names = [CONTRAST_TARGET, INTEGRAL_TARGET, CONTRAST_SHADOW, INTEGRAL_SHADOW]
    from warnings import catch_warnings, filterwarnings
    with catch_warnings():
        filterwarnings('ignore', r'.*R.*')
        for pipe in pipes:
            if not pipe.enabled:
                continue
            for tget in names:

                data_ = contrast if 'c' in tget else integral
                dist_ = dists[0] if 'tg' in tget else dists[1]
                x_ = np.linspace(np.min(dist_), np.max(dist_), num=256)[..., None]

                ax: Axes = plots[tget]
                ax.scatter(dist_, data_, facecolors="gray", s=4, alpha=0.6, edgecolors="none")

                try:
                    dist_ = dist_[..., None]
                    pipe.line.fit(dist_, data_)
                    y: np.ndarray = pipe.line.predict(x_)
                    pred = pipe.line.predict(dist_)
                    mse = mean_squared_error(data_, pred)
                    log.info(
                        "FIT,"
                        + tget
                        + ","
                        + pipe.name
                        + ","
                        + ",".join(
                            (f"{v:.4e}" for v in [*pipe.eq, mse]))
                    )
                    ax.plot(
                        x_[:, 0], y,
                        color=pipe.color,
                        linestyle=pipe.style,
                        label=fr"{pipe.title}$\, mse: {sci_4(mse)} \, {getattr(pipe, pipe.to_string)}$"
                    )
                    ax.legend()

                    try:
                        if hasattr(pipe.reg, 'inlier_mask_'):
                            ax.scatter(
                                dist_[np.logical_not(pipe.reg.inlier_mask_)],
                                data_[np.logical_not(pipe.reg.inlier_mask_)],
                                edgecolors=pipe.color,
                                s=32,
                                alpha=0.3,
                                zorder=3,
                                facecolors='none'
                            )
                            ax.set_ylim(np.min(data_[pipe.reg.inlier_mask_]), np.max(data_[pipe.reg.inlier_mask_]))
                        else:
                            ax.set_ylim(np.percentile(data_, 1), np.percentile(data_, 95))
                        pass
                    except ValueError:
                        pass

                except ValueError:
                    log.exception("Failed a regression analysis")

                ax.figure.canvas.draw()
                ax.figure.canvas.flush_events()

    log.info("done")


__all__ = [
    'show'
]
