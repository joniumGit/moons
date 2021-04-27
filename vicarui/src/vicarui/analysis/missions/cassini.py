from typing import Dict, Optional, List

import numpy as np
import spiceypy as spice
from vicarutil.image import VicarImage

from ..internal import log
from ..kernels import load_kernels_for_image, release_kernels

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

TARGET_ESTIMATE = "Draw Target Estimate"
SUN_SATURN_VECTORS = "Draw Sun Saturn Vectors"
TARGET_OVERRIDE = "Target Override"
TARGET_OVERRIDE_ID = "Target Override id"
INSTRUMENT_OVERRIDE = "Instrument Override"
INSTRUMENT_OVERRIDE_ID = "Instrument Override id"


def get_config() -> Dict:
    return {
        TARGET_ESTIMATE: (bool, False),
        SUN_SATURN_VECTORS: (bool, True),
        TARGET_OVERRIDE: (str, None),
        TARGET_OVERRIDE_ID: (int, None),
        INSTRUMENT_OVERRIDE: (str, None),
        INSTRUMENT_OVERRIDE_ID: (int, None)
    }


def get_additional_functions() -> Dict[str, str]:
    return {
        "View Image Geometry": "view_geometry"
    }


def set_info(image: VicarImage, axes=None, border: int = 0, **config) -> Optional[str]:
    try:
        load_kernels_for_image(image)
        identification: Dict[str, str] = image.labels.property('IDENTIFICATION')

        utc = identification['IMAGE_TIME']
        log.debug(f'IMAGE_TIME = {utc}')
        time = spice.utc2et(utc.strip()[:-1])

        # ids
        target_id: int = None
        target: str = None
        if TARGET_OVERRIDE in config or TARGET_OVERRIDE_ID in config:
            if TARGET_OVERRIDE in config:
                ovr = config[TARGET_OVERRIDE]
                if ovr:
                    target = ovr
                    target_id = spice.bodn2c(ovr)
                    log.debug(f'TARGET_OVERRIDE = {ovr}')
            if TARGET_OVERRIDE_ID in config:
                ovr = config[TARGET_OVERRIDE_ID]
                if ovr:
                    target_id = ovr
                    target = spice.bodc2n(target_id)
                    log.debug(f'TARGET_OVERRIDE_ID = {ovr}')

        if not target_id:
            target = identification['TARGET_NAME']
            target_id = spice.bodn2c(target)
            log.debug(f'TARGET_NAME = {target}')

        cassini_id: int = spice.bodn2c(CASSINI)
        saturn_id: int = spice.bodn2c(SATURN)
        sun_id: int = spice.bodn2c(SUN)

        # Instrument data
        frame: str = None
        if INSTRUMENT_OVERRIDE in config or INSTRUMENT_OVERRIDE_ID in config:
            if INSTRUMENT_OVERRIDE_ID in config:
                ovr = config[INSTRUMENT_OVERRIDE_ID]
                if ovr:
                    frame = spice.frmnam(ovr)
            if INSTRUMENT_OVERRIDE in config:
                ovr = config[INSTRUMENT_OVERRIDE]
                if ovr:
                    frame = ovr

        if not frame:
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

        try:
            filters: List[str] = image.labels.properties['INSTRUMENT']['FILTER_NAME']
            title += "  Filters: " + ','.join(filters)
            exposure: float = image.labels.properties['INSTRUMENT']['EXPOSURE_DURATION']
            title += f" Exp: {exposure / 1000:.2f}s"
            number: str = str(identification['IMAGE_NUMBER'])
            title += f"  Image n: {number}"
        except KeyError:
            log.warning("Failed to find filter data")

        if axes is not None:
            try:
                # noinspection PyUnresolvedReferences
                from matplotlib.axes import Axes
                ax: Axes = axes

                if SUN_SATURN_VECTORS in config and config[SUN_SATURN_VECTORS]:
                    t_form = spice.pxform(J2K, frame, time)

                    t_sun: np.ndarray = spice.mxv(t_form, sun_pos)
                    t_saturn: np.ndarray = spice.mxv(t_form, saturn_pos)
                    t_sun = -t_sun / np.linalg.norm(t_sun)
                    t_saturn = -t_saturn / np.linalg.norm(t_saturn)

                    x = 200
                    y = 200

                    sun_coord = np.vstack([x, y]).ravel() + t_sun[:2] * 100
                    saturn_coord = np.vstack([x, y]).ravel() + t_saturn[:2] * 100

                    ax.plot((x, sun_coord[0]), (y, sun_coord[1]), label="Sun", color="r")
                    ax.plot((x, saturn_coord[0]), (y, saturn_coord[1]), label="Saturn", color="y")

                if TARGET_ESTIMATE in config and config[TARGET_ESTIMATE]:
                    t_form = spice.pxform(J2K, frame, time)
                    t_sun: np.ndarray = -1 * spice.mxv(t_form, sun_pos)
                    t_cassini, _ = spice.spkezp(target_id, time, frame, ABCORR, cassini_id)
                    shape, frame_name, bore, n_vec, boundaries = spice.getfov(spice.bodn2c(frame), 10)

                    x_len = len(image.data[0])
                    y_len = len(image.data[0][0])

                    if border != 0:
                        x_len -= 2 * border
                        y_len -= 2 * border

                    x = -1 * np.arctan(t_cassini[0] / t_cassini[2]) * x_len / boundaries[0][0] + x_len / 2.
                    y = -1 * np.arctan(t_cassini[1] / t_cassini[2]) * y_len / boundaries[0][1] + y_len / 2.

                    ax.scatter(x, y, s=16, c="g")
                    sun_coord = np.vstack([x, y]).ravel() + -1 * t_sun[:2] * 300
                    ax.plot((x, sun_coord[0]), (y, sun_coord[1]), color="g")

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


def view_geometry(image: VicarImage):
    from PySide2.QtWidgets import QDialog
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.pyplot import Figure

    d = QDialog()
    fig = Figure()
    agg = FigureCanvasQTAgg(figure=fig)
