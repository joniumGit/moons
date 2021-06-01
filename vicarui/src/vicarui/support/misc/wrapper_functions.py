from functools import wraps
from typing import Any

from ...logging import handle_exception, debug


def invoke_safe(f):
    @wraps(f)
    def log_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            handle_exception(e)
        return None

    return log_function


def invoke_safe_or_default(default: Any = None):
    def safe_or_default(f):
        @wraps(f)
        def log_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                handle_exception(e)
            return default

        return log_function

    return safe_or_default


def timed(f):
    import time

    @wraps(f)
    def timing_wrapper(*args, **kwargs):
        start = time.process_time_ns()
        try:
            return f(*args, **kwargs)
        finally:
            end = time.process_time_ns()
            debug("Timed call for %s took %.3f ms", f.__name__, (end - start) / 1E6)

    return timing_wrapper


def aio_invoke_safe(f):
    @wraps(f)
    async def log_function(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            handle_exception(e)
        return None

    return log_function


def aio_invoke_safe_or_default(default: Any = None):
    def safe_or_default(f):

        @wraps(f)
        async def log_function(*args, **kwargs):
            try:
                return await f(*args, **kwargs)
            except Exception as e:
                handle_exception(e)
            return default

        return log_function

    return safe_or_default


def aio_timed(f):
    import time

    @wraps(f)
    async def timing_wrapper(*args, **kwargs):
        start = time.process_time_ns()
        try:
            return await f(*args, **kwargs)
        finally:
            end = time.process_time_ns()
            debug("Timed call for %s took %.3f ms", f.__name__, (end - start) / 1E6)

    return timing_wrapper


__all__ = [
    'invoke_safe',
    'invoke_safe_or_default',
    'aio_invoke_safe',
    'aio_invoke_safe_or_default',
    'timed',
    'aio_timed'
]
