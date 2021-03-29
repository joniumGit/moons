import logging
import sys

_fmt = logging.Formatter('[{name:s}:{asctime:s}] {levelname:<8s} - {message:s}', style='{')


class __CustomFilter(logging.Filter):

    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < logging.WARNING:
            return True
        return False


_logger = logging.getLogger("vicarutil")
_logger.propagate = 0
_logger.setLevel(logging.INFO)
if "--verbose" in sys.argv:
    _logger.setLevel(logging.DEBUG)

info_handler = logging.StreamHandler(stream=sys.stderr)
info_handler.setLevel(logging.WARNING)
info_handler.setFormatter(_fmt)

debug_handler = logging.StreamHandler(stream=sys.stdout)
debug_handler.addFilter(__CustomFilter())
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(_fmt)

_logger.addHandler(info_handler)
_logger.addHandler(debug_handler)


def log() -> logging.Logger:
    return _logger


__all__ = ['log']
