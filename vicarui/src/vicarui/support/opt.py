from typing import TypeVar, Generic, Callable, Any

T = TypeVar('T')
V = TypeVar('V')


class _Opt(Generic[T]):
    value: T
    pass


class Opt(_Opt):

    def __init__(self, value):
        super(Opt, self).__init__()
        self.value = value

    @staticmethod
    def of(o: T):  # Opt[T]
        if o is None:
            return EmptyOpt()
        else:
            return Opt(o)

    @staticmethod
    def empty():  # EmptyOpt
        return EmptyOpt()

    def map(self, f: Callable[[T], V]):
        result = f(self.value)
        if result is None:
            return Opt.empty()
        else:
            return Opt.of(result)

    def flatmap(self, f: Callable[[T], _Opt[V]]):
        return Opt.of(f(self.value).value)

    def is_present(self):
        return self.value is not None

    def get_or_else(self, o: T) -> T:
        if self.value is not None:
            return self.value
        else:
            return o

    def if_present(self, f: Callable[[T], Any]) -> None:
        if self.value is not None:
            f(self.value)


class EmptyOpt(Opt):

    def __init__(self):
        super(EmptyOpt, self).__init__(None)

    def map(self, f: Callable[[T], V]):  # EmptyOpt
        return Opt.empty()

    def flatmap(self, f: Callable[[T], _Opt[V]]):  # EmptyOpt
        return Opt.empty()

    def is_present(self):
        return False

    def get_or_else(self, o: T) -> T:
        return o

    def if_present(self, f: Callable[[T], Any]) -> None:
        pass
