import os
from typing import Dict, Optional

import numpy as np
import spiceypy as spice

from .internal import log
from ..image import VicarImage

META_KERNEL: str
KERNEL_BASE: str


def provide_kernels(path: str):
    log.info(f"Received kernel base path: {path}")
    if path.endswith('/'):
        path = path[:-1]
    global META_KERNEL
    global KERNEL_BASE
    META_KERNEL = f'{path}/mk/commons.tm'
    KERNEL_BASE = f'{path}/mk/'


log.debug('Initializing SPICE: %s' + spice.tkvrsn('TOOLKIT'))

CASSINI = 'CASSINI'
SATURN = 'SATURN'
SUN = 'SUN'
ABCORR = 'LT+S'
J2K = 'J2000'

FRAME_WAC = 'CASSINI_ISS_WAC'
FRAME_NAC = 'CASSINI_ISS_NAC'
LABEL_WAC = 'ISSWA'
LABEL_NAC = 'ISSNA'


def load_kernels_for_image(image: VicarImage):
    try:
        spice.furnsh(META_KERNEL)
        year = image.labels.property('IDENTIFICATION')['IMAGE_TIME'][0:4]
        for f in os.listdir(KERNEL_BASE):
            if year in f:
                kernel = KERNEL_BASE + f
                log.info("Loading kernel: " + f)
                spice.furnsh(kernel)
    except KeyError:
        log.warning("Failed to find identification tag from image: %s", image.name)


def release_kernels():
    try:
        spice.kclear()
    except Exception as e:
        log.critical("Failed to unload kernel!", exc_info=e)


def br_reduction(image: VicarImage) -> np.ndarray:
    from sklearn.preprocessing import PolynomialFeatures
    import statsmodels.api as sm
    image_data: np.ndarray = image.data[0]
    tmp: np.ndarray = image_data.copy()
    x = np.arange(0, tmp.shape[0], 1)
    y = np.arange(0, tmp.shape[1], 1)
    rows = PolynomialFeatures(2).fit_transform(x.reshape(-1, 1))
    cols = PolynomialFeatures(2).fit_transform(y.reshape(-1, 1))
    minus = np.zeros(tmp.shape)
    res = sm.OLS(np.average(tmp, axis=1), rows).fit()
    for i in x:
        np.add(minus[i], np.polyval(res.params[::-1], x), minus[i])
    res = sm.OLS(np.average(tmp.T, axis=1), cols).fit()
    for i in y:
        np.add(minus.T[i], np.polyval(res.params[::-1], y), minus.T[i])
    minus = minus / 2
    return image_data - minus


def set_info(image: VicarImage, axes=None) -> Optional[str]:
    try:
        load_kernels_for_image(image)
        identification: Dict[str, str] = image.labels.property('IDENTIFICATION')
        target = identification['TARGET_NAME']
        log.debug(f'TARGET_NAME = {target}')
        utc = identification['IMAGE_TIME']
        log.debug(f'IMAGE_TIME = {utc}')
        time = spice.utc2et(utc.strip()[:-1])

        # ids
        target_id: int = spice.bodn2c(target)
        cassini_id: int = spice.bodn2c(CASSINI)
        saturn_id: int = spice.bodn2c(SATURN)
        sun_id: int = spice.bodn2c(SUN)

        # Instrument data
        frame: str
        raw_instrument = identification['INSTRUMENT_ID']
        if raw_instrument == LABEL_WAC:
            frame = FRAME_WAC
        elif raw_instrument == LABEL_NAC:
            frame = FRAME_NAC
        else:
            frame = FRAME_NAC
            log.error(f"Unidentified instrument {raw_instrument}")

        # positions
        cassini_pos: np.ndarray
        sun_pos: np.ndarray
        saturn_pos: np.ndarray

        cassini_pos, _ = spice.spkezp(cassini_id, time, J2K, ABCORR, target_id)
        sun_pos, _ = spice.spkezp(sun_id, time, J2K, ABCORR, target_id)
        saturn_pos, _ = spice.spkezp(saturn_id, time, J2K, ABCORR, target_id)

        pa = np.arccos(
            np.linalg.multi_dot((cassini_pos, sun_pos))
            / np.linalg.norm(cassini_pos)
            / np.linalg.norm(sun_pos)
        ) * 180 / np.pi

        title = "FROM: %s - %s @ %s %s \nPA=%.5f DEG" % (CASSINI, target, J2K, utc, pa)

        if axes is not None:
            try:
                # noinspection PyUnresolvedReferences
                from matplotlib.axes import Axes
                ax: Axes = axes

                t_form = spice.pxform(J2K, frame, time)

                t_sun: np.ndarray = spice.mxv(t_form, sun_pos)
                t_saturn: np.ndarray = spice.mxv(t_form, saturn_pos)
                t_sun = -t_sun / np.linalg.norm(t_sun)
                t_saturn = -t_saturn / np.linalg.norm(t_saturn)

                x = 200
                y = 200

                sun_coord = np.vstack([x, y]).ravel() + t_sun[:2] * 100
                saturn_coord = np.vstack([x, y]).ravel() + t_saturn[:2] * 100

                ax.set_title(title)
                ax.plot((x, sun_coord[0]), (y, sun_coord[1]), label="Sun", color="r")
                ax.plot((x, saturn_coord[0]), (y, saturn_coord[1]), label="Saturn", color="y")

                t_cassini, _ = spice.spkezp(target_id, time, frame, ABCORR, cassini_id)
                shape, frame_name, bore, n_vec, boundaries = spice.getfov(spice.bodn2c(frame), 10)
                x_len = len(image.data[0])
                y_len = len(image.data[0][0])

                x = -1 * np.arctan(t_cassini[0] / t_cassini[2]) * x_len / boundaries[0][0] + x_len / 2.
                y = -1 * np.arctan(t_cassini[1] / t_cassini[2]) * y_len / boundaries[0][1] + y_len / 2.

                ax.scatter(x, y, s=16, c="g")

                sun_coord = np.vstack([x, y]).ravel() + -1 * t_sun[:2] * 300
                ax.plot((x, sun_coord[0]), (y, sun_coord[1]), color="g")

                log.debug(f"Target pos: {x},{y}")
                return None
            except ImportError as e:
                log.exception("No matplotlib", exc_info=e)
            except Exception as e:
                log.exception("Something bad happened", exc_info=e)

        return title
    except KeyError:
        log.warning("Failed to find target name from: %s", image.name)
        return "Failed to load identification data"
    finally:
        release_kernels()


__all__ = ['load_kernels_for_image', 'release_kernels', 'set_info', 'provide_kernels', 'br_reduction']
