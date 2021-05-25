from typing import NoReturn, Callable, List, Any, MutableMapping
from weakref import WeakKeyDictionary

from .lock import Lock

LISTENER_TYPE = Callable[[bool], NoReturn]
_listeners: MutableMapping[Any, List[LISTENER_TYPE]] = WeakKeyDictionary()
_lock = Lock()


def _retrieve_listeners() -> List[LISTENER_TYPE]:
    return [listener for ll in _listeners.values() for listener in ll]


def _append(referent: Any, listener: LISTENER_TYPE) -> NoReturn:
    if referent in _listeners:
        _listeners[referent].append(listener)
    else:
        _listeners[referent] = [listener]


class Busy:

    @staticmethod
    def listen(referent: Any, on_state_change: LISTENER_TYPE) -> NoReturn:
        """
        Adds a listener for busy state
        """
        _lock.run_blocking(lambda: _append(referent, on_state_change))

    @staticmethod
    def set(busy: bool):
        to_fire = _lock.run_blocking(_retrieve_listeners)
        if busy:
            for f in to_fire:
                f(True)
        else:
            for f in to_fire:
                f(False)

    @staticmethod
    def set_busy():
        Busy.set(True)

    @staticmethod
    def clear():
        Busy.set(False)


__all__ = ['Busy']
