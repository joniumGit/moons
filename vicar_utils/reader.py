import re
import struct
from typing import Union, BinaryIO, Set, Dict, List

import numpy as np

KEY = "KEY"
VALUE = "VALUE"
ENCODING = "ASCII"
TASK = "TASK"
PROPERTY = "PROPERTY"

lbl_regex = re.compile(r"(?P<KEY>[\S]+)[=](?P<VALUE>(?:(?=\')\'[^\']+\'|(?=\S)\S+|(?=\()(\([^\']+\))))?")
int_regex = re.compile(r"^\d+$")
float_regex = re.compile(r"(^(?:[+-]?\d*\.?\d*)+(?:[Ee][+-]?[\d]+))")

lbl_idx = len("LBLSIZE=".encode(ENCODING))
numbers: Set[bytes] = set()
for _i in range(0, 10):
    numbers.add(("%d" % _i).encode(ENCODING))

ARRAY_TYPE = List[Union[str, int, float]]
OBJECT_TYPE = Dict[str, Union[str, int, float, ARRAY_TYPE]]
BASE_TYPE = Dict[str, Union[str, int, float, ARRAY_TYPE, OBJECT_TYPE]]


def extract_image(f: BinaryIO) -> np.ndarray:
    lblsize = find_label_size(f)
    lbl = process_label(export_label(f, lblsize))
    return export_image_data(
        f,
        lblsize,
        lbl['RECSIZE'],
        lbl['NLB'],
        lbl['NBB'],
        lbl['N1'],
        lbl['N2'],
        lbl['N3']
    )[0]


def find_label_size(f: BinaryIO) -> int:
    f.seek(lbl_idx)
    out: str = ""
    b = f.read(1)
    while b in numbers:
        out += str(b, encoding=ENCODING)
        b = f.read(1)
    return int(out)


def export_label(f: BinaryIO, lblsize: int) -> str:
    f.seek(0)
    return str(f.read(lblsize), encoding=ENCODING)


def eol_offset(recsize: int, lblsize: int, nlb: int, n2: int, n3: int) -> int:
    return lblsize + recsize * nlb + n2 * n3 * recsize


def export_eol(f: BinaryIO, offset: int, lblsize: int) -> BASE_TYPE:
    f.seek(offset)
    return process_label(f.read(lblsize))


def export_binary_header(f: BinaryIO, lblsize: int, recsize: int, nlb: int) -> BASE_TYPE:
    f.seek(lblsize)
    return process_label(f.read(nlb * recsize))


def export_image_data(f: BinaryIO,
                      lblsize: int,
                      recsize: int,
                      nlb: int,
                      nbb: int,
                      n1: int,
                      n2: int,
                      n3: int) -> (np.ndarray, np.ndarray):
    f.seek(lblsize + nlb * recsize)
    nbb_store: np.ndarray
    nbb_non_zero = nbb != 0
    if nbb_non_zero:
        nbb_store = np.ndarray(shape=(n2 * n3,), dtype=bytes)
    img_store = np.ndarray(shape=(n1, n2 * n3), dtype=float)
    for i in range(0, n2 * n3):
        if nbb_non_zero:
            nbb_store[i] = f.read(nbb)
        reads = int((recsize - nbb) / 4)
        for j in range(0, reads):
            img_store[i][j] = struct.unpack('<f', f.read(4))[0]
    if nbb_non_zero:
        return img_store, nbb_store
    else:
        return img_store, None


def process_label(data: Union[bytes, str]) -> BASE_TYPE:
    encoded: str
    if isinstance(data, str):
        encoded = data
    else:
        encoded = str(data, encoding=ENCODING)
    found = lbl_regex.finditer(encoded)
    out = dict()
    sub = None
    for m in found:
        key = m.group(KEY)
        val = m.group(VALUE)

        if val is None:
            val = ""
        elif int_regex.search(val):
            val = int(val)
        elif float_regex.search(val):
            val = float(val)
        elif val[0] == "(":
            string = val[1:-1]
            val = string.split(",")
        elif val[0] == "'":
            val = val[1:-1]

        if key == PROPERTY or key == TASK:
            sub = dict()
            if val in out:
                i = 1
                while val + str(i) in out:
                    i += 1
                out[val + str(i)] = sub
            else:
                out[val] = sub

        if sub is None:
            out[key] = val
        else:
            if not (key == PROPERTY or key == TASK):
                sub[key] = val

    return out
