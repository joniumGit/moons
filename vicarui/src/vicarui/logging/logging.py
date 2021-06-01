import logging
import sys
from typing import Any, Optional, NoReturn

log = logging.getLogger("vicarui")


def child(logger: str) -> logging.Logger:
    return log.getChild(logger)


def info(message: str, *args) -> NoReturn:
    log.info(message, *args)


def debug(message: str, *args) -> NoReturn:
    log.debug(message, *args)


def warn(message: str, *args) -> NoReturn:
    log.warning(message, *args)


def exception(message: str, e: BaseException) -> NoReturn:
    log.exception(message, exc_info=e)


def handle_exception(e: Optional[BaseException]) -> NoReturn:
    if e is not None:
        log.exception("An exception occurred", exc_info=e)


def log_object(o: Any, message: str = "Object information: %s") -> NoReturn:
    log.debug(message, repr(o))


def init_logging():
    fmt = logging.Formatter('{asctime:s}|{levelname:<8s}|{name:<20s}|{message:s}', style='{')
    log.setLevel(logging.INFO)
    log.propagate = 0

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

    log.addHandler(info_handler)
    log.addHandler(debug_handler)

    if '--verbose' in sys.argv:
        log.info("Setting level to DEBUG")
        log.setLevel(logging.DEBUG)
        log.warning("Testing error log")
        log.warning("warning")
        log.critical("critical")
        try:
            warn("Incoming test error")
            raise Exception("Testing exception log...")
        except Exception as e:
            handle_exception(e)


__all__ = [
    'init_logging',
    'child',
    'info',
    'debug',
    'warn',
    'handle_exception',
    'log_object',
    'log'
]
