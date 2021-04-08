"""
Definitions for different labels present in Vicar files.

This is a collection for their values and types collected into enums.
The reader will try to convert all the SystemLabels into other label types where applicable.
"""
from enum import Enum
from typing import Type, Dict, List, Tuple, Optional, Set

import numpy as np

LABEL_ENCODING = 'ASCII'
LABEL_SEPARATOR = '='


class VicarEnum(Enum):
    """
    Some stuff for cross linking this stuff
    """

    @classmethod
    def has_value(cls, o) -> bool:
        return o in cls._value2member_map_

    @classmethod
    def map2member(cls, val: str):
        if val in cls._value2member_map_:
            return cls._value2member_map_[val]
        else:
            return None

    def __repr__(self):
        return f'{self.value}'

    def __str__(self):
        return self.__repr__()


class VicarMultiEnum(VicarEnum):
    """
    Continuing the abuse of enums
    """

    @classmethod
    def __fill_lookup(cls):
        if not hasattr(cls, '__lookup_filled__'):
            cls.__lookup_filled__ = True
            cls.__member_lookup__ = dict()
            for v, m in cls._value2member_map_.items():
                cls.__member_lookup__[v[0]] = m
        cls.__lookup_ok = True

    @classmethod
    def has_value(cls, value) -> bool:
        cls.__fill_lookup()
        return value in cls.__member_lookup__

    @classmethod
    def map2member(cls, value: str):
        cls.__fill_lookup()
        return cls.__member_lookup__[value]

    def __repr__(self):
        return f'{self.value[0]}'


class NumberFormat(VicarMultiEnum):
    """
    Vicar file number formats

    Values:
        0: Name
        1: Byte width
        2: Python struct unpack type
        3: Numpy datatype
    """
    BYTE = 'BYTE', 1, 'B', np.dtype('uint8')
    HALF = 'HALF', 2, 'h', np.dtype('int16')
    FULL = 'FULL', 4, 'i', np.dtype('int32')
    REAL = 'REAL', 4, 'f', np.dtype('single')
    DOUB = 'DOUB', 8, 'd', np.dtype('double')
    COMP = 'COMP', 8, 'f', np.dtype('complex64')  # .       SPECIAL re(f) + im(f)
    WORD = 'WORD', 2, 'h', np.dtype('int16')  # .           HALF Obsolete
    LONG = 'LONG', 4, 'i', np.dtype('int32')  # .           FULL Obsolete
    COMPLEX = 'COMPLEX', 8, 'f', np.dtype('complex64')  # . COMP, SPECIAL re(f) + im(f) Obsolete


INT_FORMATS: Set[NumberFormat] = {
    NumberFormat.BYTE,
    NumberFormat.HALF,
    NumberFormat.FULL,
    NumberFormat.WORD,
    NumberFormat.LONG
}

FLOAT_FORMATS: Set[NumberFormat] = {
    NumberFormat.REAL,
    NumberFormat.DOUB,
    NumberFormat.COMP,
    NumberFormat.COMPLEX
}


def isIntFormat(fmt: NumberFormat) -> bool:
    """
    Checks whether the provided NumberFormat is an IntFormat
    """
    return fmt in INT_FORMATS


def isRealFormat(fmt: NumberFormat) -> bool:
    """
    Checks whether the provided NumberFormat is a RealFormat
    """
    return fmt in FLOAT_FORMATS


def isFloatFormat(fmt: NumberFormat) -> bool:
    """
    Alias for isRealFormat
    """
    return fmt in FLOAT_FORMATS


class DataType(VicarEnum):
    """
    Vicar file data types
    """
    IMAGE = 'IMAGE'
    PARAMS = 'PARAMS'  # .                      Very old
    PARM = 'PARM'  # .                          Old
    PARAM = 'PARAM'  # .                        Parameter file
    GRAPH1 = 'GRAPH1'  # .                      IBIS Graphics
    GRAPH2 = 'GRAPH2'
    GRAPH3 = 'GRAPH3'
    TABULAR = 'TABULAR'


class DataOrg(VicarEnum):
    """
    Data format inside the file

    Notes:
        N1 - Varies fastest, N3 - Slowest

    Different representations:
        BSQ - Band SeQuential (samples, lines, bands)
        BIL - Band Interleaved by Line (samples, bands, lines)
        BIP - Band Interleaved by Pixel (bands, samples, lines)

    Image(s):
        - B: bands (images)
        - L: lines
        - S: sample

    Provide data order and representation (B, L, S):
        BSQ - Image samples (S) for lines (L) in blocks, blocks are bands (images)
            => (0,0,0) -> (0,0,1) -> (0,0,2) --> (1,0,0)
        BIL - Image samples (S) for bands in blocks, blocks are lines (L)
            => (0,0,0) -> (0,0,1) -> (0,0,2) --> (0,1,0)
        BIP - Image bands for samples (S) in blocks, blocks are lines (L)
            => (0,0,0) -> (1,0,0) -> (2,0,0) --> (0,1,0)

    Numpy data array (B, L, S)
    """
    BSQ = 'BSQ'  # .                            N1 samples, N2 lines, N3 bands
    BIL = 'BIL'  # .                            N1 samples, N2 bands, N3 lines
    BIP = 'BIP'  # .                            N1 bands, N2 samples, N3 lines


class HostType(VicarEnum):
    """
    Host types, not really useful, prefer strings over these as not all are known
    """
    ALLIANT = 'ALLIANT'
    CRAY = 'CRAY'  # .                          Unimplemented standard
    DECSTATN = 'DECSTATN'
    HP700 = 'HP-700'
    MACAUX = 'MAC-AUX'
    MACMPW = 'MAC-MPW'
    SGI = 'SGI'
    SUN3 = 'SUN-3'
    SUN4 = 'SUN-4'
    TEK = 'TEK'
    VAS = 'VAX-VMS'
    PC = 'PC_X86_64'


class IntFormat(VicarMultiEnum):
    """
    Integer Endian settings in data
    """
    HIGH = 'HIGH', '>'  # .                     high first Big-Endian
    LOW = 'LOW', '<'  # .                       low first Little-Endian


class RealFormat(VicarMultiEnum):
    """
    Float bit order in data

    VAX (and VAX-VMS) is unimplemented
    """
    IEEE = 'IEEE', '>'  # .                     IEEE 754 high first
    RIEEE = 'RIEEE', '<'  # .                   Reverse, documentation says only on DECSTATN
    VAX = 'VAX', ''  # .                        VAX format, double VAX D, only VAX-VMS NOT IMPLEMENTED


class SystemLabel(VicarMultiEnum):
    """
    System labels that define Vicar file properties
    """
    LBLSIZE = 'LBLSIZE', int  # .               Multiple of RECSIZE                 MANDATORY
    FORMAT = 'FORMAT', NumberFormat  # .        Format of data                      MANDATORY
    TYPE = 'TYPE', DataType  # .                Data type                           default IMAGE
    BUFSIZ = 'BUFSIZ', int  # .                 Buffer size              (obsolete) default RECSIZE
    DIM = 'DIM', int  # .                       Data dimensions  (2 in old, but =3) SET 3
    EOL = 'EOL', int  # .                       0, 1 End of file labels             default 0
    RECSIZE = 'RECSIZE', int  # .               Record size     (NBB + N1 * FORMAT) MANDATORY
    ORG = 'ORG', DataOrg  # .                   Data organization                   default BSQ
    NL = 'NL', int  # .                         Number of lines                     MANDATORY
    NS = 'NS', int  # .                         Number of samples                   MANDATORY
    NB = 'NB', int  # .                         Number of bands                     MANDATORY
    N1 = 'N1', int  # .                         Fastest dim                         default max(NS,NB)
    N2 = 'N2', int  # .                         Mid dim                             default mid(NL,NS,NB)
    N3 = 'N3', int  # .                         Slowest dim                         default min(NL,NB)
    N4 = 'N4', int  # .                         Not implemented in standard         SET 0
    NBB = 'NBB', int  # .                       Binary prefix                       default 0
    NLB = 'NLB', int  # .                       Binary header                       default 0
    HOST = 'HOST', HostType  # .                Host                         (doc)  default VAX-VMS
    INTFMT = 'INTFMT', IntFormat  # .           Integer format                      default LOW
    REALFMT = 'REALFMT', RealFormat  # .        Float format                        default VAX
    BHOST = 'BHOST', HostType  # .              Binary host                  (doc)  default VAX-VMS
    BINTFMT = 'BINTFMT', IntFormat  # .         Binary Int format                   default LOW
    BREALFMT = 'BREALFMT', RealFormat  # .      Binary Float format                 default VAX
    BLTYPE = 'BLTYPE', str  # .                 Binary label/prefix host     (doc)  default \x00

    @staticmethod
    def fill_dims(labels: Dict):
        """
        Fills alternate dimension according to standard
        """
        org: Optional[DataOrg] = None
        try:
            org = labels[SystemLabel.ORG]
        except KeyError:
            labels[SystemLabel.ORG] = DataOrg.BSQ
        defaults: Tuple[SystemLabel, SystemLabel, SystemLabel]
        if org == DataOrg.BIL:
            defaults = (SystemLabel.NS, SystemLabel.NB, SystemLabel.NL)
        elif org == DataOrg.BIP:
            defaults = (SystemLabel.NB, SystemLabel.NS, SystemLabel.NL)
        else:
            defaults = (SystemLabel.NS, SystemLabel.NL, SystemLabel.NB)
        for i, m in enumerate((SystemLabel.N1, SystemLabel.N2, SystemLabel.N3)):
            if m not in labels:
                labels[m] = defaults[i]
        if SystemLabel.N4 not in labels:
            labels[SystemLabel.N4] = 0
        if SystemLabel.NBB not in labels:
            labels[SystemLabel.NBB] = 0
        if SystemLabel.NLB not in labels:
            labels[SystemLabel.NLB] = 0


class SpecialLabel(VicarEnum):
    """
    Markers for special sections in file labels
    """
    PROPERTY = 'PROPERTY'
    TASK = 'TASK'


SYSTEM_CLASS_LIST: List[Type[VicarEnum]] = [
    NumberFormat,
    DataType,
    DataOrg,
    IntFormat,
    RealFormat,
    SystemLabel
]


def getSystemTypes() -> List[Type[VicarEnum]]:
    return SYSTEM_CLASS_LIST
