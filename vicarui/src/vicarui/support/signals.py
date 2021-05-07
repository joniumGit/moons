from typing import TypeVar, Generic, Callable, Type, cast

from PySide2.QtCore import Signal

_T = TypeVar('_T')


class SimpleSignal:
    def __init__(self):
        pass

    def emit(self):
        pass

    def connect(self, c: Callable[[], None]):
        pass


class TypedSignal(Generic[_T]):
    def __init__(self, t: Type[_T]):
        pass

    def emit(self, o: _T):
        pass

    def connect(self, c: Callable[[_T], None]):
        pass


def typedsignal(t: Type[_T]) -> TypedSignal[_T]:
    return cast(TypedSignal[_T], Signal(t))


def signal() -> SimpleSignal:
    return cast(SimpleSignal, Signal())
