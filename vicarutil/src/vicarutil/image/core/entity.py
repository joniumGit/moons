"""
Helper entities for dealing with Vicar data
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..definitions import *


@dataclass(frozen=True)
class BinaryPrefix:
    """
    Represents Vicar file binary prefix.

    At the moment just a nested list of bytes.
    Not implemented.
    """
    __slots__ = 'data'
    data: List[List[bytes]]


@dataclass(frozen=True)
class Labels:
    """
    Represents various labels contained in Vicar files

    Provides some utility functions.
    """
    __slots__ = 'system', 'properties', 'tasks'
    system: SYSTEM_TYPE
    properties: Optional[DICT_TYPE]
    tasks: Optional[DICT_TYPE]

    def vsl(self, key: SystemLabel) -> SYSTEM_VALUE_TYPE:
        """Returns a SystemLabel values"""
        return self.system[key]

    def property(self, key: str) -> OBJECT_TYPE:
        """Returns a property value"""
        return self.properties[key]

    def task(self, key: str) -> OBJECT_TYPE:
        """Returns a Task value"""
        return self.tasks[key]

    def has_properties(self):
        """True if this file has any Properties (VICAR)"""
        return self.properties is not None

    def has_tasks(self):
        """True if this file has any Tasks (VICAR)"""
        return self.tasks is not None


@dataclass(frozen=True)
class VicarImageConstraints:
    """
    Constraints containing all the important image data for reading the actual data from the file
    """
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
    __slots__ = 'labels', 'properties', 'tasks', 'data', 'binary_header', 'binary_prefix', 'eol_labels', 'name'
    labels: Labels
    """
    Labels at the beginning of the file
    """
    eol_labels: Labels
    """
    EOL labels if they are present in the file
    """
    data: Optional[np.ndarray]
    """
    Data contained in the image, always in BSQ format when created.
    
    Always BSQ is a design decision for convenience.
    Transform are provided in transforms.py
    """
    binary_header: Optional[bytes]
    """
    Binary header if present.
    
    Might be in ASCII format, but not specified so not processed.
    """
    binary_prefix: Optional[BinaryPrefix]
    """
    Binary prefix
    
    Not processed.
    """
    name: str
    """
    Filename
    """

    def has_data(self):
        """True if this object has image data"""
        return self.data is not None

    def has_binary_header(self):
        """True if this object has binary headers"""
        return self.binary_header is not None

    def has_binary_prefix(self):
        """True if this object has binary prefix"""
        return self.binary_prefix is not None
