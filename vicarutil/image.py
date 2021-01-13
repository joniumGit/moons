from typing import BinaryIO, List, cast
import numpy as np

from .definitions.definitions import DataOrg, NumFormat, VSL, INT_FORMATS, FLOAT_FORMATS
from .definitions.types import SYSTEM_TYPE
from .entity import VicarImageConstraints
from .transforms import bip_to_bsq, bil_to_bsq


def read_img(f: BinaryIO, offset: int, c: VicarImageConstraints) -> np.ndarray:
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
    fmt: NumFormat = cast(NumFormat, labels[VSL.FORMAT])
    order: str
    if fmt in INT_FORMATS:
        order = labels[VSL.INTFMT].value[1]
    elif fmt in FLOAT_FORMATS:
        order = labels[VSL.REALFMT].value[1]
    else:
        order = "="
    return fmt.value[3].newbyteorder(order)


def constraint_from_labels(labels: SYSTEM_TYPE) -> VicarImageConstraints:
    return VicarImageConstraints(
        n1=labels[VSL.N1],
        n2=labels[VSL.N2],
        n3=labels[VSL.N3],
        recsize=labels[VSL.RECSIZE],
        nbb=labels[VSL.NBB],
        nbh=labels[VSL.NLB],
        dtype=dtype_from_labels(labels),
        org=cast(DataOrg, labels[VSL.ORG])
    )
