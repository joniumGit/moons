from enum import Enum

encoding = 'ASCII'
separator = '='

class Format(Enum):
    BYTE = ('BYTE', 1, 'B')
    HALF = ('HALF', 2, 'h')
    FULL = ('FULL', 4, 'i')
    REAL = ('REAL', 4, 'f')
    DOUB = ('DOUB', 8, 'd')
    COMP = ('COMP', 8, 'f')  # SPECIAL re(f) + im(f)
    WORD = ('WORD', 2, 'h')  # HALF
    LONG = ('LONG', 4, 'i')  # FULL
    COMPLEX = ('COMPLEX', 8, 'f')  # COMP, SPECIAL re(f) + im(f)


class Type(Enum):
    IMAGE = 'IMAGE'
    PARAMS = 'PARAMS'  # Very old
    PARM = 'PARM'  # Old
    PARAM = 'PARAM'  # Parameter file
    GRAPH1 = 'GRAPH1'  # IBIS Graphics
    GRAPH2 = 'GRAPH2'
    GRAPH3 = 'GRAPH3'
    TABULAR = 'TABULAR'


class Org(Enum):
    BSQ = 'BSQ'  # N1 samples, N2 lines, N3 bands
    BIL = 'BIL'  # N1 samples, N2 bands, N3 lines
    BIP = 'BIP'  # N1 bands, N2 samples, N3 lines


class Host(Enum):
    ALLIANT = 'ALLIANT'
    CRAY = 'CRAY'  # Unimplementedin standard
    DECSTATN = 'DECSTATN'
    HP700 = 'HP-700'
    MACAUX = 'MAC-AUX'
    MACMPW = 'MAC-MPW'
    SGI = 'SGI'
    SUN3 = 'SUN-3'
    SUN4 = 'SUN-4'
    TEK = 'TEK'
    VAS = 'VAX-VMS'


class Intfmt(Enum):
    HIGH = ('HIGH', '>')  # high first Big-Enidian
    LOW = ('LOW', '<')  # low first Little-Enidian


class Realfmt(Enum):
    IEEE = ('IEEE', '>')  # IEEE 754 high first
    RIEEE = ('RIEEE', '<')  # Reverse, documentation says only on DECSTATN
    VAX = ('VAX', '')  # VAX format, double VAX D, only VAX-VMS NOT IMPLEMENTED


class System(Enum):
    LBLSIZE = 'LBLSIZE'  # Multiple of RECSIZE
    FORMAT = 'FORMAT'
    TYPE = 'TYPE'
    BUFSIZ = 'BUFSIZ'
    DIM = 'DIM'
    EOL = 'EOL'
    RECSIZE = 'RECSIZE'  # NBB + N1
    ORG = 'ORG'
    NL = 'NL'  # Number of lines
    NS = 'NS'  # Number of samples
    NB = 'NB'  # Number of bands
    N1 = 'N1'  # Not present; default to NL, NS, NB = Fastest varying
    N2 = 'N2'  # Not present; default to NL, NS, NB = Second fastest varying
    N3 = 'N3'  # Not present; default to NL, NS, NB = Slowest varying
    N4 = 'N4'  # Not implemented in standard
    NBB = 'NBB'  # Binary prefix
    NLB = 'NLB'  # Binary header
    HOST = 'HOST'  # Default: VAX-VMS not important
    INTFMT = 'INTFMT'  # Integer format
    REALFMT = 'REALFMT'  # Float format
    BHOST = 'BHOST'  # Binary representation host
    BINTFMT = 'BINTFMT'
    BREALFMT = 'BREALFMT'
    BLTYPE = 'BLTYPE'  # Documentation for type of binary label


class Special(Enum):
    PROPERTY = 'PROPERTY'
    TASK = 'TASK'
