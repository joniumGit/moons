from threading import RLock
from typing import Callable, TypeVar
from warnings import warn

T = TypeVar('T')


class Lock:
    """
    Class that wraps a re-entrant lock and provides a method for running with it
    """
    _lock: RLock

    def __init__(self):
        super(Lock, self).__init__()
        self._lock = RLock()

    def run_blocking(self, runnable: Callable[[], T]) -> T:
        """
        Acquire and run
        """
        if self._lock.acquire(blocking=True):
            try:
                return runnable()
            finally:
                self._lock.release()
        else:
            warn("Failed to append listener")


__all__ = ['Lock']
