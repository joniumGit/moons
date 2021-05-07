import logging
import sys
from functools import wraps
from typing import Any, Optional

_logger = logging.getLogger("vicarui")


def info(message: str, *args) -> None:
    _logger.info(message, *args)


def debug(message: str, *args) -> None:
    _logger.debug(message, *args)


def warn(message: str, *args) -> None:
    _logger.warning(message, *args)


def handle_exception(e: Optional[BaseException]) -> None:
    if e is not None:
        _logger.exception("An exception occurred", exc_info=e)


def log_object(o: Any, message: str = "Object information: %s") -> None:
    _logger.debug(message, str(o))


def init_logging():
    fmt = logging.Formatter('{asctime:s}|{levelname:<8s}|{name:<20s}|{message:s}', style='{')
    _logger.setLevel(logging.INFO)
    _logger.propagate = 0

    info_handler = logging.StreamHandler(stream=sys.stderr)
    info_handler.setLevel(logging.WARNING)
    info_handler.setFormatter(fmt)

    class CustomFilter(logging.Filter):

        def filter(self, record: logging.LogRecord) -> bool:
            if record.levelno < logging.WARNING:
                return True
            return False

    debug_handler = logging.StreamHandler(stream=sys.stdout)
    debug_handler.addFilter(CustomFilter())
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(fmt)

    _logger.addHandler(info_handler)
    _logger.addHandler(debug_handler)

    if '--verbose' in sys.argv:
        _logger.info("Setting level to DEBUG")
        _logger.setLevel(logging.DEBUG)
        _logger.warning("Testing error log")
        _logger.warning("warning")
        _logger.critical("critical")
        try:
            warn("Incoming test error")
            raise Exception("Testing exception log...")
        except Exception as e:
            handle_exception(e)


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
            _logger.debug("Timed call for %s took %.3f ms", f.__name__, (end - start) / 1E6)

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
            _logger.debug("Timed call for %s took %.3f ms", f.__name__, (end - start) / 1E6)

    return timing_wrapper
