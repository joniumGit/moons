import numpy as np


def bsq_to_bip(data: np.ndarray) -> np.ndarray:
    return data.swapaxes(0, 1).swapaxes(0, 2)


def bip_to_bsq(data: np.ndarray) -> np.ndarray:
    return data.swapaxes(2, 0).swapaxes(1, 0)


def bsq_to_bil(data: np.ndarray) -> np.ndarray:
    return data.swapaxes(1, 2)


def bil_to_bsq(data: np.ndarray) -> np.ndarray:
    return data.swapaxes(2, 1)


def bip_to_bil(data: np.ndarray) -> np.ndarray:
    return data.swapaxes(0, 1)


def bil_to_bip(data: np.ndarray) -> np.ndarray:
    return data.swapaxes(1, 0)
