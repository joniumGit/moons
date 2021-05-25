from typing import NoReturn, Callable, List
from weakref import ref

from .lock import Lock

LISTENER_TYPE = Callable[[bool], NoReturn]
_listeners: List[ref[LISTENER_TYPE]] = list()
_lock = Lock()


def _retrieve_listeners() -> List[LISTENER_TYPE]:
    to_fire = list()
    to_remove = list()
    for idx, weak in enumerate(_listeners):
        listener = weak()
        if listener is not None:
            to_fire.append(listener)
        else:
            to_remove.append(idx)
    for idx in reversed(to_remove):
        _listeners.pop(idx)
    return to_fire


class Busy:

    @staticmethod
    def listen(on_state_change: LISTENER_TYPE) -> NoReturn:
        """
        Adds a listener for busy state
        """
        _lock.run_blocking(lambda: _listeners.append(ref(on_state_change)))

    @staticmethod
    def set(busy: bool):
        to_fire = _lock.run_blocking(_retrieve_listeners)
        if busy:
            map(lambda f: f(True), to_fire)
        else:
            map(lambda f: f(False), to_fire)


__all__ = ['Busy']
