import re
import typing as t
from typing import BinaryIO, Callable, Any

from .entity import *
from .definitions.definitions import *
from .definitions.types import *

lbl_offset = len("LBLSIZE=".encode(LABEL_ENCODING))
numbers: Set[str] = set()
for _i in range(0, 10):
    numbers.add(str(_i))

lbl_regex = re.compile(r"(?P<KEY>[\S]+)[=](?P<VALUE>(?:(?=\')\'[^\']+\'|(?=\S)\S+|(?=\()(\([^\']+\))))?")
int_regex = re.compile(r"^\d+$")
float_regex = re.compile(r"(^[+-]?(?=.?\d)\d*\.\d*(?:[EeDd][+-]?[\d]+)?)")
lbl_regex_key = "KEY"
lbl_regex_value = "VALUE"


class StrIO:

    def __init__(self, file: BinaryIO):
        self.file = file

    def reset(self) -> None:
        self.seek(0)

    def seek(self, n: int = 0, whence: int = 0) -> None:
        self.file.seek(n, whence)

    def read(self, n: int = 1) -> str:
        return str(self.file.read(n), encoding=LABEL_ENCODING)

    def unwrap(self) -> BinaryIO:
        return self.file


def _ensure_io(func: Callable) -> Callable:
    def _ensuring_io(f: Union[str, BinaryIO], *args, **kwargs):
        if isinstance(f, str):
            with open(f, "rb") as file:
                return func(file, *args, **kwargs)
        else:
            return func(f, *args, **kwargs)

    return _ensuring_io


def _find_lbl_size(file: StrIO) -> int:
    size: str = file.read()
    join: str = file.read()
    while join in numbers:
        size = ''.join((size, join))
        join = file.read()
    return int(size)


def _read_labels(file: StrIO) -> str:
    return _read_eol_labels(file, lbl_offset)


def _read_eol_labels(file: StrIO, offset: int) -> str:
    file.reset()
    file.seek(offset)
    size = _find_lbl_size(file)
    file.reset()
    return file.read(size)


def _process_value(value: str, map_to_enum: bool = True) -> Union[int, float, str, ARRAY_TYPE]:
    if value is None:
        return ''
    value = value.strip()
    if int_regex.search(value):
        return int(value)
    elif float_regex.search(value):
        return float(value)
    elif value[0] == '(':
        split = value[1:-1].split(',')
        return [_process_value(x.strip()) for x in split]
    elif value[0] == '\'':
        value = value[1:-1]
    if map_to_enum:
        for cls in SYSTEM_CLASS_LIST:
            if cls.has_value(value):
                return cls.map2member(value)
    return value


def _process_key(key: str) -> VSL:
    if key[0] == '\'':
        key = key[1:-1]
    return VSL.map2member(key)


def _add(key: Any, value: Any, target: Dict):
    if key in target:
        i = 1
        nk = '_'.join((key, str(i)))
        while nk in target:
            i += 1
            nk = '_'.join((key, str(i)))
        target[nk] = value
    else:
        target[key] = value


def _is_special(key: str) -> bool:
    return Special.has_value(key)


def _process_labels(
        raw_labels: Union[str, bytes],
        defaults: Tuple[SYSTEM_TYPE, DICT_TYPE, DICT_TYPE] = None
) -> Tuple[SYSTEM_TYPE, DICT_TYPE, DICT_TYPE]:
    text: str
    if isinstance(raw_labels, bytes):
        text = str(raw_labels, encoding=LABEL_ENCODING)
    else:
        text = raw_labels
    matcher = lbl_regex.finditer(text)

    labels: SYSTEM_TYPE
    properties: DICT_TYPE
    tasks: DICT_TYPE
    if defaults:
        labels = defaults[0]
        properties = defaults[1]
        tasks = defaults[2]
    else:
        labels = dict()
        properties = dict()
        tasks = dict()

    sub_dict: Optional[OBJECT_TYPE] = None
    sub_target: Optional[Special] = None
    sub_key: Optional[str] = None

    for match in matcher:
        key: str = match.group(lbl_regex_key)
        value: str = match.group(lbl_regex_value)
        if _is_special(key):
            if sub_dict is not None:
                if sub_target == Special.PROPERTY:
                    _add(sub_key, sub_dict, properties)
                elif sub_target == Special.TASK:
                    _add(sub_key, sub_dict, tasks)
                sub_dict, sub_target, sub_key = None, None, None
            if key == Special.PROPERTY.value:
                sub_target = Special.PROPERTY
            elif key == Special.TASK.value:
                sub_target = Special.TASK
            sub_dict = dict()
            sub_key = _process_value(value, False)
        else:
            if sub_dict is None:
                labels[_process_key(key)] = _process_value(value)
            else:
                _add(key, _process_value(value, False), sub_dict)

    return labels, properties, tasks


def _read_binary_header(file: StrIO, labels: SYSTEM_TYPE) -> Optional[OBJECT_TYPE]:
    try:
        nlb: int = labels[VSL.NLB]
        if nlb == 0:
            return None
        offset: int = labels[VSL.LBLSIZE]
        recsize: int = labels[VSL.RECSIZE]
        file.reset()
        file.seek(offset)
        data = file.read(nlb * recsize).strip()
        matcher = lbl_regex.finditer(data)
        out: Dict[str, Union[str, int, float]] = dict()
        for match in matcher:
            key: str = match.group(lbl_regex_key)
            if key[0] == '\'':
                key = key[1:-1]
            value: str = match.group(lbl_regex_value)
            out[key] = _process_value(value, map_to_enum=False)
        return out
    except KeyError:
        pass
    except UnicodeDecodeError:
        pass
    return None


class __VicarReader:

    def __init__(self, labels: SYSTEM_TYPE):
        self.nbb: int = labels[VSL.NBB]
        self.recsize: int = labels[VSL.RECSIZE]
        self.org: DataOrg = t.cast(DataOrg, labels[VSL.ORG])
        self.n1: int = labels[VSL.N1]
        self.n2: int = labels[VSL.N2]
        self.n3: int = labels[VSL.N3]

        fmt: NumFormat = t.cast(NumFormat, labels[VSL.FORMAT])
        order: str
        if fmt in INT_FORMATS:
            order = labels[VSL.INTFMT].value[1]
        elif fmt in FLOAT_FORMATS:
            order = labels[VSL.REALFMT].value[1]
        else:
            order = "="

        datatype: np.dtype = fmt.value[3].newbyteorder(order)

        self.dtype: np.dtype = datatype
        self.offset = labels[VSL.BEGLBLSIZE]
        try:
            self.offset += labels[VSL.NLB] * self.recsize
        except KeyError:
            pass

    def _make_data_array(self) -> np.ndarray:
        """
        Makes a (z, x, y) array based on VicarDataOrg
        """
        n1: int = self.n1
        n2: int = self.n2
        n3: int = self.n3
        org: VicarEnum = self.org

        shape: Tuple[int, int, int]
        if org == DataOrg.BSQ:
            shape = (n3, n2, n1)
        elif org == DataOrg.BIL:
            shape = (n2, n3, n1)
        elif org == DataOrg.BIP:
            shape = (n1, n3, n2)
        else:
            raise TypeError("Wrong type for org: "
                            + str(type(org))
                            + " expected: "
                            + str(type(DataOrg)))

        return np.zeros(shape, dtype=self.dtype)

    def commit(self, file: BinaryIO) -> Tuple[np.ndarray, List[bytes]]:
        readsize = self.recsize - self.nbb
        file.seek(self.offset)
        # read everything
        # now slicing
        nbb_store: List[bytes] = list()
        data = self._make_data_array()
        for n3 in range(0, self.n3):
            for n2 in range(0, self.n2):
                if self.nbb != 0:
                    nbb = file.read(self.nbb)
                    nbb_store.append(nbb)
                b = file.read(readsize)
                data_row = np.ndarray([self.n1], dtype=self.dtype, buffer=b)
                if self.org == DataOrg.BSQ:
                    for n1 in range(0, self.n1):
                        data[n3][n2][n1] = data_row[n1]
                if self.org == DataOrg.BIP:
                    for n1 in range(0, self.n1):
                        data[n2][n3][n1] = data_row[n1]
                if self.org == DataOrg.BIL:
                    for n1 in range(0, self.n1):
                        data[n1][n3][n2] = data_row[n1]
        return data, nbb_store


@_ensure_io
def read_image(f: Union[str, BinaryIO]) -> VicarImage:
    file: StrIO = StrIO(file=f)
    labels, properties, tasks = _process_labels(_read_labels(file))

    # important defaults
    VSL.fill_dims(labels)

    # check eol
    labels[VSL.BEGLBLSIZE] = labels[VSL.LBLSIZE]
    if VSL.EOL in labels and labels[VSL.EOL]:
        skip_bytes = labels[VSL.NLB] + (
                labels[VSL.N2] * labels[VSL.N3]
        ) * labels[VSL.RECSIZE]
        total_skip = labels[VSL.LBLSIZE] + skip_bytes
        labels, properties, tasks = _process_labels(
            _read_eol_labels(file, total_skip),
            defaults=(labels, properties, tasks)
        )
        labels[VSL.EOLLBLSIZE] = labels[VSL.LBLSIZE]
        labels[VSL.LBLSIZE] = labels[VSL.BEGLBLSIZE]

    # load this shit
    binary_header = _read_binary_header(file, labels)
    data, binary_prefix = __VicarReader(labels).commit(file.unwrap())

    return VicarImage(
        labels=labels,
        properties=properties,
        tasks=tasks,
        data=data,
        binary_header=binary_header,
        binary_prefix=binary_prefix
    )
