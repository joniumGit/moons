"""
Utility functions for transforming DataOrg types into other ones.

These transforms should be fine to be combined in any way possible.
All of these should work both ways.
"""

import numpy as np


def bsq_to_bip(data: np.ndarray) -> np.ndarray:
    """BSQ to BIP transformation"""
    return data.transpose((1, 2, 0))


def bip_to_bsq(data: np.ndarray) -> np.ndarray:
    """BIP to BSQ transformation"""
    return data.transpose((2, 0, 1))


def bsq_to_bil(data: np.ndarray) -> np.ndarray:
    """BSQ to BIL transformation"""
    return data.transpose((1, 0, 2))


def bil_to_bsq(data: np.ndarray) -> np.ndarray:
    """BIL to BSQ transformation"""
    return data.transpose((1, 0, 2))


def bip_to_bil(data: np.ndarray) -> np.ndarray:
    """BIP to BIL transformation"""
    return data.transpose((0, 2, 1))


def bil_to_bip(data: np.ndarray) -> np.ndarray:
    """BIL to BIP transformation"""
    return data.transpose((0, 2, 1))
