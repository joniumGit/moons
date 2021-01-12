from typing import Union, List, Dict

from .definitions import VicarEnum

ARRAY_TYPE = List[Union[str, int, float]]
OBJECT_TYPE = Dict[str, Union[str, int, float, ARRAY_TYPE]]
DICT_TYPE = Dict[str, OBJECT_TYPE]
VALUE_TYPE = Union[str, int, float, ARRAY_TYPE, OBJECT_TYPE]
SYSTEM_VALUE_TYPE = Union[VicarEnum, int, str]
SYSTEM_TYPE = Dict[VicarEnum, SYSTEM_VALUE_TYPE]
