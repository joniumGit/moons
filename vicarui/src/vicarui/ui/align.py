from PySide2.QtCore import Qt

N = Qt.AlignTop
S = Qt.AlignBottom
E = Qt.AlignRight
W = Qt.AlignLeft
C = Qt.AlignCenter

HC = Qt.AlignHCenter
VC = Qt.AlignVCenter

CT = HC | N
CB = HC | S
CL = VC | W
CR = VC | E

NW = N | W
NE = N | E
SE = S | E
SW = S | W
