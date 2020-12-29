from typing import Union, BinaryIO
from dataclasses import dataclass

import numpy as np

from . import labels as lbl


@dataclass
class ImageFormat:
    dtype: lbl.NumFormat
    dorder: Union[lbl.IFMT, lbl.RFMT]


@dataclass
class ImageType:
    iformat: ImageFormat
    itype: lbl.DataOrg
    ns: int
    nl: int
    nb: int


@dataclass
class Image:
    meta: ImageType
    data: np.ndarray



def read_image(io: BinaryIO, frmt: ImageFormat, width: int, height: int, layers: int) -> np.ndarray:
    if frmt is lbl.NumFormat.DOUB or frmt is lbl.NumFormat.REAL:
        pass
    elif frmt is lbl.NumFormat.COMP or frmt is lbl.NumFormat.COMPLEX:
        pass


    array: np.ndarray = np.ndarray(shape=(layers, width, height))

    return array


img: np.ndarray
def read(image: ImageType) -> np.ndarray:
    if image.itype is lbl.DataOrg.BSQ:
        pass

