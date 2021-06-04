# noinspection PyUnresolvedReferences
from typing import Tuple, List, Dict, Iterable, Union

# noinspection PyUnresolvedReferences
import numpy as np
import spiceypy as spice
# noinspection PyUnresolvedReferences
from vicarutil.image import VicarImage

from ...internal import log as parent_logger
# noinspection PyUnresolvedReferences
from ....support import ImageWrapper

log = parent_logger.getChild("cas")
log.debug('Initializing SPICE: %s' + spice.tkvrsn('TOOLKIT'))

# https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/naif_ids.html

# Body
CASSINI = 'CASSINI'
SATURN = 'SATURN'
SUN = 'SUN'

# Color Config
# https://davidmathlogic.com/colorblind/#%23FF0000-%230088FF-%23FFBF00-%239A9999-%23000000
SATURN_COLOR = '#FF0000'
SUN_COLOR = '#FFBF00'
TARGET_COLOR = '#0088FF'
TARGET_ALT_COLOR = 'green'
CAMERA_COLOR = '#9A9999'
CASSINI_COLOR = '#000000'
WF_ALPHA = 0.35

# SPICE ID's
CASSINI_ID = -82
SATURN_ID = 699
SUN_ID = 10

# SPICE Const
J2K = 'J2000'
RADII = 'RADII'
POLE_RA = 'POLE_RA'

# Label -> Inst. Conversion
FRAME_WAC = 'CASSINI_ISS_WAC'
FRAME_NAC = 'CASSINI_ISS_NAC'
LABEL_WAC = 'ISSWA'
LABEL_NAC = 'ISSNA'


class Correction:
    LT = "LT"
    """
    One way Light Time, Newtonian, One iteration

    Position of target at the time Photons arrive to Observer at ET
    """
    LTS = "LT+S"
    """
    LT with added stellar aberration, Newtonian, One iteration
    
    Modifies LT to add the effect of observer velocity relative to solar system barycenter
    """

    CN = "CN"
    """
    LT until it converges, Three iterations, Slower
    """

    CNS = "CN+S"
    """
    CN + Aberration correction
    """

    NONE = "NONE"


def l2i(label: str) -> str:
    """
    Known cassini camera from image labels to actual frame name
    """
    if label.strip() == LABEL_WAC:
        return FRAME_WAC
    elif label.strip() == LABEL_NAC:
        return FRAME_NAC
    else:
        return label


# Saturn centric frame
SATURN_FRAME = 'IAU_SATURN'

# Module config
TARGET_ESTIMATE = "Draw Target Estimate"
SUN_SATURN_VECTORS = "Draw Sun Saturn Vectors"
TARGET_OVERRIDE = "Target Override"
INSTRUMENT_OVERRIDE = "Instrument Override"
SIZE_FRAME = "Size at (0: target, 1: shadow, 2: ring)"
SINGLE_PLOT_AUTOFIT = "Autofit plots (0: all, 1: TC, 2: SC, 3: TI, 4: SI)"
DISABLE_FITTING = "Disable Autofit Fitters"

SIZE_AT_TARGET = 0
SIZE_AT_SHADOW = 1
SIZE_AT_RING = 2


def get_config():
    return {
        TARGET_ESTIMATE: (bool, True),
        SUN_SATURN_VECTORS: (bool, True),
        TARGET_OVERRIDE: (str, None),
        INSTRUMENT_OVERRIDE: (str, None),
        SIZE_FRAME: (int, 0),
        SINGLE_PLOT_AUTOFIT: (int, 0),
        DISABLE_FITTING: (bool, False)
    }
