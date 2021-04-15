import os

import spiceypy as spice
from vicarutil.image import VicarImage

from .internal import log

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
