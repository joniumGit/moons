from functools import partialmethod
from typing import Type, TypeVar
from typing import cast

T = TypeVar('T')


def partial_cls(cls: Type[T], *args, **kwargs) -> Type[T]:
    result = type('_partial', (cls,), {'__init__': partialmethod(cls.__init__, *args, **kwargs)})
    # Copied from Python namedtuple
    try:
        import sys as _sys
        # noinspection PyUnresolvedReferences
        result.__module__ = _sys._getframe(1).f_globals.get('__name__', '__main__')
    except (AttributeError, ValueError):
        pass

    return cast(Type[T], result)


__all__ = ['partial_cls']
