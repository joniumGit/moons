from functools import cache

from .config import *
from .helpers import *
from ....support import looping_pairs


def _image_size(corners: np.ndarray) -> Tuple[float, float]:
    """
    Figure out the actual width and height of the image in kilometers

    Assume the following for the bounds:
    - Cassini defines the UP direction to be at positive y
    - First FOV vector is at +X, +Y:

        F1  y
            ^
        x < 0

      At least according to IK files.

    With this assumption in mind this will return a Tuple:
    - Width:    AVERAGE(TOP, BOTTOM)
    - Height:   AVERAGE(RIGHT, LEFT)
    """
    top, right, bottom, left = [np.linalg.norm(p[0] - p[1]) for p in looping_pairs(corners)]

    rl = np.average((right, left))
    tb = np.average((top, bottom))

    log.info("Corner diffs: " + ','.join([f"{a:.5e}" for a in (right, bottom, left, top)]))
    return tb, rl


def norm(v: np.ndarray) -> np.ndarray:
    """
    Norm a vector
    """
    n = np.linalg.norm(v)
    if n != 0:
        return v / n
    else:
        return np.zeros(v.shape)


def img_rp_size(helper: ImageHelper) -> Tuple[float, float]:
    """
    Size of image in x, y in kilometers in the Saturn ring plane

    Returns Width, Height in km
    """
    cas = spice.spkezp(CASSINI_ID, helper.time_et, SATURN_FRAME, ABCORR, SATURN_ID)[0]
    frame, bore, bounds = helper.fbb
    t = Transformer(frame, SATURN_FRAME, helper.time_et)
    cas_xy = cas[0:2]
    cas_z = cas[2]
    corners = list()
    for b in bounds:
        tb = t(b)
        corners.append(cas_xy + tb[0:2] * (-cas_z / tb[2]))

    return _image_size(np.asarray(corners))


def img_sp_size(helper: ImageHelper) -> Tuple[float, float]:
    """
    Size in 'Shadow plane'

    Returns Width, Height in km
    """
    frame, bore, bounds = helper.fbb
    t = Transformer(frame, SATURN_FRAME, helper.time_et)
    spi = ShadowPlaneIntersect(helper)
    corners = [spi(t(b)) for b in bounds]

    return _image_size(np.asarray(corners))


def img_raw_size(helper: ImageHelper) -> Tuple[float, float]:
    """
    Raw image size

    Returns Width, Height in km
    """
    frame, bore, bounds = helper.fbb
    t = Transformer(frame, SATURN_FRAME, helper.time_et)
    bore = t(bore)

    target_dist = np.linalg.norm(helper.pos_in_sat(helper.target_id(), CASSINI_ID))
    bore_len = np.linalg.norm(bore)
    corners = [t(b) * target_dist / np.dot(t(b), bore) * bore_len for b in bounds]

    return _image_size(np.asarray(corners))


@cache
def rs() -> float:
    return np.average(spice.bodvar(SATURN_ID, 'RADII', 3)[1])


def scale_to_rs(v: np.ndarray) -> np.ndarray:
    return v / rs()


def get_camera_intersects(helper: ImageHelper):
    """
    Where should our camera be? in RS
    """
    cassini_pos = helper.pos_in_sat(CASSINI_ID, SATURN_ID)
    # Calculating intercepts
    frm, bore, bounds = helper.fbb
    t = Transformer(frm, SATURN_FRAME, helper.time_et)
    bore = t(bore)
    bore_intercept: np.ndarray
    bound_intersects: Union[List[np.ndarray], np.ndarray] = list()
    if helper.size_selection == SIZE_AT_SHADOW:
        # Shadow
        spi = ShadowPlaneIntersect(helper)
        bore_intercept = spi(bore)
        bound_intersects = [np.column_stack((cassini_pos, spi(t(b)))) for b in bounds]
    elif helper.size_selection == SIZE_AT_RING:
        # Ring plane
        bore_intercept = bore * (-cassini_pos[2] / bore[2])
        for b in bounds:
            tb = t(norm(b))
            pv = cassini_pos + tb * (-cassini_pos[2] / tb[2])
            bound_intersects.append(np.column_stack((cassini_pos, pv)))
        bore_intercept = cassini_pos + bore_intercept
    else:
        # Raw
        bore_len = np.linalg.norm(bore)
        target_dist = np.linalg.norm(helper.pos_in_sat(CASSINI_ID, helper.target_id()))
        cnt = target_dist / bore_len
        bore_intercept = cassini_pos + bore * cnt
        for b in bounds:
            tb = t(norm(b))
            nll = np.dot(tb, bore) / bore_len
            bound_intersects.append(np.column_stack((cassini_pos, cassini_pos + tb * target_dist / nll)))
    bound_intersects = np.asarray([scale_to_rs(bi) for bi in bound_intersects])
    up = scale_to_rs(t(np.asarray([0, 1, 0])))
    scale = np.linalg.norm(bound_intersects[0] - bound_intersects[-1]) / (2 * np.linalg.norm(up))
    return scale_to_rs(bore_intercept), bound_intersects, up * scale


__all__ = [
    'norm',
    'rs',
    'scale_to_rs',
    'get_camera_intersects',
    'get_config',
    'img_rp_size',
    'img_raw_size',
    'img_sp_size'
]
