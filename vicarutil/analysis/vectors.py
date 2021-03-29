import os
import sys
from typing import Dict

import spiceypy as spice
from matplotlib.axes import Axes

from vicarutil.image import VicarImage
from vicarutil.image.util.logging import log

bp = sys.argv[1]
META_KERNEL = bp + '/kernels/mk/commons.tm'
KERNEL_BASE = bp + '/kernels/mk/'

log().debug('Initializing SPICE: %s' + spice.tkvrsn('TOOLKIT'))

_loaded_kernels = list()


def load_kernels_for_image(image: VicarImage):
    try:
        year = image.labels.property('IDENTIFICATION')['IMAGE_TIME'][0:4]
        for f in os.listdir(bp + "/kernels/mk"):
            if year in f:
                kernel = KERNEL_BASE + f
                log().info("Loading kernel: " + f)
                spice.furnsh(kernel)
                _loaded_kernels.append(f)
    except KeyError:
        log().warning("Failed to find identification tag from image: %s", image.name)


def release_kernels():
    for k in _loaded_kernels:
        try:
            spice.kclear()
        except Exception as e:
            log().critical("Failed to unload kernel!", exc_info=e)


def set_info(plot: Axes, image: VicarImage):
    j2k = 'J2000'
    try:
        identification: Dict[str, str] = image.labels.property('IDENTIFICATION')
        target = identification['TARGET_NAME']
        utc = identification['IMAGE_MID_TIME']
        probe = identification['']
        pa = 1.12
        plot.set_title("FROM: %s - %s @ %s %s \nPA=%.5f DEG" % (probe, target, j2k, utc, pa))
    except KeyError:
        log().warning("Failed to find target name from: %s", image.name)
        plot.set_title("Failed to load identification data")
