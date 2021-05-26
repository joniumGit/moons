from typing import TypeVar, Generator, Iterable, Union, Callable, Sequence, Any

T = TypeVar('T')


def looping_pairs(
        iterable: Union[Iterable[T], Callable[[], T], Sequence[T]],
        sentinel: Any = None
) -> Generator[T, None, None]:
    """
    https://stackoverflow.com/questions/1257413/iterate-over-pairs-in-a-list-circular-fashion-in-python/1257446#1257446
    """
    if sentinel is not None:
        i = iter(iterable, sentinel)
    else:
        i = iter(iterable)
    first = prev = item = next(i)
    for item in i:
        yield prev, item
        prev = item
    yield item, first


__all__ = ['looping_pairs']
