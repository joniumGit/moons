import re
from typing import BinaryIO, Any, Dict, Optional, Set

from .definitions.definitions import LABEL_ENCODING, VSL, SYSTEM_CLASS_LIST, Special
from .definitions.types import VALUE_TYPE, SYSTEM_VALUE_TYPE, SYSTEM_TYPE, DICT_TYPE, OBJECT_TYPE
from .entity import Labels
from .helper import StrIO

LBL_REGEX = re.compile(r"(?P<KEY>[\S]+)[=](?P<VALUE>(?:(?=\')\'[^\']+\'|(?=\S)\S+|(?=\()(\([^\']+\))))?")
INT_REGEX = re.compile(r"^\d+$")
FLOAT_REGEX = re.compile(r"(^[+-]?(?=.?\d)\d*\.\d*(?:[EeDd][+-]?[\d]+)?)")
LBL_REGEX_KEY = "KEY"
LBL_REGEX_VALUE = "VALUE"
LBL_OFFSET = len("LBLSIZE=".encode(LABEL_ENCODING))
NUMBERS: Set[str] = set()
for _i in range(0, 10):
    NUMBERS.add(str(_i))


def dict_add_indexed(key: Any, value: Any, target: Dict):
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
    f.seek(labels.vsl(VSL.LBLSIZE))
    return f.read(labels.vsl(VSL.NLB) * labels.vsl(VSL.RECSIZE))


def process_value(value: Optional[str]) -> VALUE_TYPE:
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
    value = value.strip()
    if value[0] == '\'':
        value = value[1:-1]
    if INT_REGEX.search(value):
        return int(value)
    for cls in SYSTEM_CLASS_LIST:
        if cls.has_value(value):
            return cls.map2member(value)
    return value


def read_labels(f: BinaryIO, offset: int) -> Labels:
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
    sub_target: Optional[Special] = None
    sub_key: Optional[str] = None

    for match in matcher:
        key: str = match.group(LBL_REGEX_KEY)
        value: str = match.group(LBL_REGEX_VALUE)
        if Special.has_value(key):
            if sub_dict is not None:
                if sub_target == Special.PROPERTY:
                    dict_add_indexed(sub_key, sub_dict, properties)
                elif sub_target == Special.TASK:
                    dict_add_indexed(sub_key, sub_dict, tasks)
                sub_dict, sub_target, sub_key = None, None, None
            if key == Special.PROPERTY.value:
                sub_target = Special.PROPERTY
            elif key == Special.TASK.value:
                sub_target = Special.TASK
            sub_dict = dict()
            sub_key = process_value(value)
        else:
            if sub_dict is None:
                labels[process_system_value(key)] = process_system_value(value)
            else:
                dict_add_indexed(key, process_value(value), sub_dict)

    return Labels(system=labels, properties=properties, tasks=tasks)


def read_beg_labels(f: BinaryIO) -> Labels:
    return read_labels(f, 0)


def has_eol(labels: Labels) -> bool:
    return VSL.EOL in labels.system and labels.system[VSL.EOL] != 0


def eol_offset(labels: Labels) -> int:
    return labels.vsl(VSL.NLB) * labels.vsl(VSL.RECSIZE)


def read_eol_labels(f: BinaryIO, beg_labels: Labels) -> Labels:
    return read_labels(f, eol_offset(beg_labels))
