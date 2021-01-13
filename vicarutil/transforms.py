import numpy as np


def bsq_to_bip(data: np.ndarray) -> np.ndarray:
    return data.transpose((1, 2, 0))


def bip_to_bsq(data: np.ndarray) -> np.ndarray:
    return data.transpose((2, 0, 1))


def bsq_to_bil(data: np.ndarray) -> np.ndarray:
    return data.transpose((1, 0, 2))


def bil_to_bsq(data: np.ndarray) -> np.ndarray:
    return data.transpose((1, 0, 2))


def bip_to_bil(data: np.ndarray) -> np.ndarray:
    return data.transpose((0, 2, 1))


def bil_to_bip(data: np.ndarray) -> np.ndarray:
    return data.transpose((0, 2, 1))
