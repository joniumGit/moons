"""
Internal convenience functions for reading images
"""

from typing import BinaryIO, cast

import numpy as np

from ..core.entity import VicarImageConstraints
from ..definitions import *
from ..util.transforms import bip_to_bsq, bil_to_bsq


def read_image_internal(f: BinaryIO, offset: int, c: VicarImageConstraints) -> np.ndarray:
    """
    Reads image data from a file into a ndarray.
    """
    f.seek(offset)
    recsize: int = c.recsize
    nbb: int = c.nbb
    dtype: np.dtype = c.dtype
    data = [
        [
            np.frombuffer(f.read(recsize), dtype=dtype, offset=nbb) for _ in range(0, c.n2)
        ] for _ in range(0, c.n3)
    ]
    base_arr: np.ndarray = np.asarray(data)
    if c.org == DataOrg.BIP:
        base_arr = bip_to_bsq(base_arr)
    elif c.org == DataOrg.BIL:
        base_arr = bil_to_bsq(base_arr)
    return base_arr


def read_binary_prefix(f: BinaryIO, offset: int, c: VicarImageConstraints) -> List[List[bytes]]:
    """
    Reads image binary prefix.
    """
    f.seek(offset)
    nbb: int = c.nbb
    skip: int = c.recsize - nbb

    def read_seek() -> bytes:
        b = f.read(nbb)
        f.seek(skip, 1)
        return b

    data = [
        [
            read_seek() for _ in range(0, c.n2)
        ] for _ in range(0, c.n3)
    ]

    return data


def dtype_from_labels(labels: SYSTEM_TYPE) -> np.dtype:
    """
    Generates a Numpy dtype from labels based on Vicar standard.
    """
    fmt: NumberFormat = cast(NumberFormat, labels[SystemLabel.FORMAT])
    order: str
    if isIntFormat(fmt):
        order = labels[SystemLabel.INTFMT].value[1]
    elif isRealFormat(fmt):
        order = labels[SystemLabel.REALFMT].value[1]
    else:
        order = "="
    return fmt.value[3].newbyteorder(order)


def constraint_from_labels(labels: SYSTEM_TYPE) -> VicarImageConstraints:
    """
    Constraints for image reading from labels. Convenience.
    """
    return VicarImageConstraints(
        n1=labels[SystemLabel.N1],
        n2=labels[SystemLabel.N2],
        n3=labels[SystemLabel.N3],
        recsize=labels[SystemLabel.RECSIZE],
        nbb=labels[SystemLabel.NBB],
        nbh=labels[SystemLabel.NLB],
        dtype=dtype_from_labels(labels),
        org=cast(DataOrg, labels[SystemLabel.ORG])
    )
