from enum import Enum
from typing import Type, Dict, List, Tuple, Optional, Set

import numpy as np

encoding = 'ASCII'
separator = '='


class VicarEnum(Enum):

    @classmethod
    def has_value(cls, o) -> bool:
        return o in cls._value2member_map_

    @classmethod
    def map2member(cls, val: str):
        if val in cls._value2member_map_:
            return cls._value2member_map_[val]
        else:
            return None


class VicarMultiEnum(VicarEnum):

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


class NumFormat(VicarMultiEnum):
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


INT_FORMATS: Set[NumFormat] = {NumFormat.BYTE, NumFormat.HALF, NumFormat.FULL, NumFormat.WORD, NumFormat.LONG}
FLOAT_FORMATS: Set[NumFormat] = {NumFormat.REAL, NumFormat.DOUB, NumFormat.COMP, NumFormat.COMPLEX}


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
        - x: lines
        - y: sample
        - z: bands (images)

    Provide data order and representation (z, x, y):
        BSQ - Image samples (y) for lines (x) in blocks, blocks are bands (images)
            => (0,0,0) -> (0,0,1) -> (0,0,2) --> (1,0,0)
        BIL - Image samples (y) for bands in blocks, blocks are lines (x)
            => (0,0,0) -> (0,1,0) -> (0,2,0) --> (0,0,1)
        BIP - Image bands for samples (y) in blocks, blocks are lines (x)
            => (0,0,0) -> (1,0,0) -> (2,0,0) --> (0,0,1)

    Numpy data array (z, x, y)
    """
    BSQ = 'BSQ'  # .                            N1 samples, N2 lines, N3 bands
    BIL = 'BIL'  # .                            N1 samples, N2 bands, N3 lines
    BIP = 'BIP'  # .                            N1 bands, N2 samples, N3 lines


class HostType(VicarEnum):
    """
    Host types, not really useful
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


class IFMT(VicarMultiEnum):
    """
    Integer Endian settings in data
    """
    HIGH = 'HIGH', '>'  # .                     high first Big-Endian
    LOW = 'LOW', '<'  # .                       low first Little-Endian


class RFMT(VicarMultiEnum):
    """
    Float bit order in data

    VAX (and VAX-VMS) is unimplemented
    """
    IEEE = 'IEEE', '>'  # .                     IEEE 754 high first
    RIEEE = 'RIEEE', '<'  # .                   Reverse, documentation says only on DECSTATN
    VAX = 'VAX', ''  # .                        VAX format, double VAX D, only VAX-VMS NOT IMPLEMENTED


class VSL(VicarMultiEnum):
    """
    System labels that define Vicar file properties
    """
    LBLSIZE = 'LBLSIZE', int  # .               Multiple of RECSIZE                 MANDATORY
    FORMAT = 'FORMAT', NumFormat  # .   Format of data                      MANDATORY
    TYPE = 'TYPE', DataType  # .           Data type                           default IMAGE
    BUFSIZ = 'BUFSIZ', int  # .                 Buffer size              (obsolete) default RECSIZE
    DIM = 'DIM', int  # .                       Data dimensions  (2 in old, but =3) SET 3
    EOL = 'EOL', int  # .                       0, 1 End of file labels             default 0
    RECSIZE = 'RECSIZE', int  # .               Record size     (NBB + N1 * FORMAT) MANDATORY
    ORG = 'ORG', DataOrg  # .              Data organization                   default BSQ
    NL = 'NL', int  # .                         Number of lines                     MANDATORY
    NS = 'NS', int  # .                         Number of samples                   MANDATORY
    NB = 'NB', int  # .                         Number of bands                     MANDATORY
    N1 = 'N1', int  # .                         Fastest dim                         default max(NS,NB)
    N2 = 'N2', int  # .                         Mid dim                             default mid(NL,NS,NB)
    N3 = 'N3', int  # .                         Slowest dim                         default min(NL,NB)
    N4 = 'N4', int  # .                         Not implemented in standard         SET 0
    NBB = 'NBB', int  # .                       Binary prefix                       default 0
    NLB = 'NLB', int  # .                       Binary header                       default 0
    HOST = 'HOST', HostType  # .           Host                         (doc)  default VAX-VMS
    INTFMT = 'INTFMT', IFMT  # .      Integer format                      default LOW
    REALFMT = 'REALFMT', RFMT  # .   Float format                        default VAX
    BHOST = 'BHOST', HostType  # .         Binary host                  (doc)  default VAX-VMS
    BINTFMT = 'BINTFMT', IFMT  # .    Binary Int format                   default LOW
    BREALFMT = 'BREALFMT', RFMT  # . Binary Float format                 default VAX
    BLTYPE = 'BLTYPE', str  # .                 Binary label/prefix host     (doc)  default \x00
    EOLLBLSIZE = 'eol_labels', int  # .         Custom - Eol lbl size        (custom)
    BEGLBLSIZE = 'beg_labels', int  # .         Custom - Eol lbl size        (custom)

    @staticmethod
    def fill_dims(labels: Dict):
        org: Optional[DataOrg] = None
        try:
            org = labels[VSL.ORG]
        except KeyError:
            labels[VSL.ORG] = DataOrg.BSQ
        defaults: Tuple[VSL, VSL, VSL]
        if org == DataOrg.BIL:
            defaults = (VSL.NS, VSL.NB, VSL.NL)
        elif org == DataOrg.BIP:
            defaults = (VSL.NB, VSL.NS, VSL.NL)
        else:
            defaults = (VSL.NS, VSL.NL, VSL.NB)
        for i, m in enumerate((VSL.N1, VSL.N2, VSL.N3)):
            if m not in labels:
                labels[m] = defaults[i]
        if VSL.N4 not in labels:
            labels[VSL.N4] = 0
        if VSL.NBB not in labels:
            labels[VSL.NBB] = 0
        if VSL.NLB not in labels:
            labels[VSL.NLB] = 0


class Special(VicarEnum):
    """
    Markers for special sections in file labels
    """
    PROPERTY = 'PROPERTY'
    TASK = 'TASK'


CLASSLIST: List[Type[VicarEnum]] = [
    NumFormat,
    DataType,
    DataOrg,
    #  HostType, this is not used and not all values are known
    IFMT,
    RFMT,
    VSL
]
