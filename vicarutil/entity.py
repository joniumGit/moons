from dataclasses import dataclass
from typing import Optional, List

import numpy as np

from .definitions.definitions import VSL, DataOrg
from .definitions.types import SYSTEM_TYPE, DICT_TYPE, SYSTEM_VALUE_TYPE, OBJECT_TYPE


@dataclass(frozen=True)
class BinaryPrefix:
    __slots__ = 'data'
    data: Optional[List[List[bytes]]]


@dataclass(frozen=True)
class Labels:
    """
    Represents various labels contained in Vicar files
    """
    __slots__ = 'system', 'properties', 'tasks'
    system: SYSTEM_TYPE
    properties: Optional[DICT_TYPE]
    tasks: Optional[DICT_TYPE]

    def vsl(self, key: VSL) -> SYSTEM_VALUE_TYPE:
        return self.system[key]

    def property(self, key: str) -> OBJECT_TYPE:
        return self.properties[key]

    def task(self, key: str) -> OBJECT_TYPE:
        return self.tasks[key]

    def has_properties(self):
        return self.properties is not None

    def has_tasks(self):
        return self.tasks is not None


@dataclass(frozen=True)
class VicarImageConstraints:
    __slots__ = 'n1', 'n2', 'n3', 'org', 'recsize', 'dtype', 'nbb', 'nbh'
    n1: int
    n2: int
    n3: int
    recsize: int
    nbb: int
    nbh: int
    dtype: np.dtype
    org: DataOrg


@dataclass(frozen=False)
class VicarImage:
    """
    Represents a Vicar image file
    """
    __slots__ = 'labels', 'properties', 'tasks', 'data', 'binary_header', 'binary_prefix', 'eol_labels'
    labels: Labels
    eol_labels: Labels
    """
    Data contained in the image, always in BSQ format when created
    """
    data: Optional[np.ndarray]
    binary_header: bytes
    binary_prefix: BinaryPrefix

    def has_data(self):
        return self.data is not None

    def has_binary_header(self):
        return self.binary_header is not None

    def has_binary_prefix(self):
        return self.binary_prefix is not None
