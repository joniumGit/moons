from typing import Union, BinaryIO
from dataclasses import dataclass

import numpy as np

from . import labels as lbl


@dataclass
class ImageFormat:
    dtype: lbl.Format
    dorder: Union[lbl.Intfmt, lbl.Realfmt]


@dataclass
class ImageType:
    iformat: ImageFormat
    itype: lbl.Org
    ns: int
    nl: int
    nb: int


@dataclass
class Image:
    meta: ImageType
    data: np.ndarray



def read_image(io: BinaryIO, frmt: ImageFormat, width: int, height: int, layers: int) -> np.ndarray:
    if frmt is lbl.Format.DOUB or frmt is lbl.Format.REAL:
        pass
    elif frmt is lbl.Format.COMP or frmt is lbl.Format.COMPLEX:
        pass


    array: np.ndarray = np.ndarray(shape=(layers, width, height))

    return array


img: np.ndarray
def read(image: ImageType) -> np.ndarray:
    if image.itype is lbl.Org.BSQ:
        pass

