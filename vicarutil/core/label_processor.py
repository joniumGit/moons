"""
Reads and transforms any labels found in Vicar files
"""

import re
from typing import BinaryIO, Any, Set, Optional

from ..core.entity import Labels
from ..definitions import *
from ..definitions.definitions import LABEL_ENCODING
from ..util.helper import StrIO

LBL_REGEX = re.compile(r"(?P<KEY>[\S]+)[=](?P<VALUE>(?:(?=\')\'[^\']+\'|(?=\S)\S+|(?=\()(\([^\']+\))))?")
"""
Should maybe and hopefully parse all KEY=VALUE pairs
"""
INT_REGEX = re.compile(r"^\d+$")
"""
Should maybe and hopefully detect all Int values
"""
FLOAT_REGEX = re.compile(r"(^[+-]?(?=.?\d)\d*\.\d*(?:[EeDd][+-]?[\d]+)?)(?!\S)")
"""
Should maybe and hopefully detect all Float values
"""
LBL_REGEX_KEY = "KEY"
LBL_REGEX_VALUE = "VALUE"
LBL_OFFSET = len("LBLSIZE=".encode(LABEL_ENCODING))
NUMBERS: Set[str] = set()
for _i in range(0, 10):
    NUMBERS.add(str(_i))


def add_indexed(key: Any, value: Any, target: Dict):
    """
    Adds stuff into labels dicts and adds index if they are already there. Inefficient.
    """
    if key in target:
        i = 1
        nk = '_'.join((key, str(i)))
        while nk in target:
            i += 1
            nk = '_'.join((key, str(i)))
        target[nk] = value
    else:
        target[key] = value


def read_binary_header(f: BinaryIO, labels: Labels) -> bytes:
    """
    Reads binary header from file
    """
    f.seek(labels.vsl(SystemLabel.LBLSIZE))
    return f.read(labels.vsl(SystemLabel.NLB) * labels.vsl(SystemLabel.RECSIZE))


def process_value(value: Optional[str]) -> VALUE_TYPE:
    """
    Processes an transforms a value if applicable
    """
    if value is None:
        return ''
    value = value.strip()

    if INT_REGEX.search(value):
        return int(value)
    elif FLOAT_REGEX.search(value):
        return float(value)
    elif value[0] == '\'':
        value = value[1:-1]
    elif value[0] == '(':
        split = value[1:-1].split(',')
        return [process_value(x.strip()) for x in split]
    return value


def process_system_value(value: str) -> SYSTEM_VALUE_TYPE:
    """
    Transforms strings into SystemLabel values
    """
    value = value.strip()
    if value[0] == '\'':
        value = value[1:-1]
    if INT_REGEX.search(value):
        return int(value)
    for cls in getSystemTypes():
        if cls.has_value(value):
            return cls.map2member(value)
    return value


def read_labels(f: BinaryIO, offset: int) -> Labels:
    """
    Reads normal labels from a file
    """
    f = StrIO(f)

    f.seek(LBL_OFFSET, 1)
    size: str = f.read()
    join: str = f.read()
    while join in NUMBERS:
        size = ''.join((size, join))
        join = f.read()

    f.seek(offset)
    text: str = f.read(int(size))
    matcher = LBL_REGEX.finditer(text)

    labels: SYSTEM_TYPE = dict()
    properties: DICT_TYPE = dict()
    tasks: DICT_TYPE = dict()

    sub_dict: Optional[OBJECT_TYPE] = None
    sub_target: Optional[SpecialLabel] = None
    sub_key: Optional[str] = None

    # This method might be a bit inefficient
    for match in matcher:
        key: str = match.group(LBL_REGEX_KEY)
        value: str = match.group(LBL_REGEX_VALUE)
        if SpecialLabel.has_value(key):
            if sub_dict is not None:
                if sub_target == SpecialLabel.PROPERTY:
                    add_indexed(sub_key, sub_dict, properties)
                elif sub_target == SpecialLabel.TASK:
                    add_indexed(sub_key, sub_dict, tasks)
                sub_dict, sub_target, sub_key = None, None, None
            if key == SpecialLabel.PROPERTY.value:
                sub_target = SpecialLabel.PROPERTY
            elif key == SpecialLabel.TASK.value:
                sub_target = SpecialLabel.TASK
            sub_dict = dict()
            sub_key = process_value(value)
        else:
            if sub_dict is None:
                labels[process_system_value(key)] = process_system_value(value)
            else:
                add_indexed(key, process_value(value), sub_dict)

    return Labels(system=labels, properties=properties, tasks=tasks)


def read_beg_labels(f: BinaryIO) -> Labels:
    """Reads labels at the start of the file"""
    return read_labels(f, 0)


def has_eol(labels: Labels) -> bool:
    """Returns true if the file has EOL labels"""
    return SystemLabel.EOL in labels.system and labels.system[SystemLabel.EOL] != 0


def eol_offset(labels: Labels) -> int:
    """Offset for EOL labels"""
    return labels.vsl(SystemLabel.NLB) * labels.vsl(SystemLabel.RECSIZE)


def read_eol_labels(f: BinaryIO, beg_labels: Labels) -> Labels:
    """Reads EOL labels"""
    return read_labels(f, eol_offset(beg_labels))
