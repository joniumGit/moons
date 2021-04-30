"""
Collection of types used across this program
"""

from typing import Dict, List
from typing import Union

from .definitions import VicarEnum

ARRAY_TYPE = List[Union[str, int, float]]
"""
Possible array type in Vicar files
"""
OBJECT_TYPE = Dict[str, Union[str, int, float, ARRAY_TYPE]]
"""
Represents a Object in Vicar files
"""

DICT_TYPE = Dict[str, OBJECT_TYPE]
"""
Represents a Dictionary of label values, usually used with SpecialLabels
"""

VALUE_TYPE = Union[str, int, float, ARRAY_TYPE, OBJECT_TYPE]
"""
Possible values present in Vicar label files
"""

SYSTEM_VALUE_TYPE = Union[VicarEnum, int, str]
"""
Possible types for System labels.

Look into mpl.py for more infor on these.
"""

SYSTEM_TYPE = Dict[VicarEnum, SYSTEM_VALUE_TYPE]
"""
Type for dictionary representing Vicar SystemLabels
"""
