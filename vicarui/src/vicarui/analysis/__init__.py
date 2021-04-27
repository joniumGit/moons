from types import ModuleType
from typing import Optional, Dict

from vicarutil.image import VicarImage

from .fitting import DataPacket
from .kernels import provide_kernels
from .reduction import br_reduction
from .wrapper import ImageWrapper

SELECTED: str = "cassini"


def anal_module() -> Optional[ModuleType]:
    import importlib
    try:
        if '.' in SELECTED:
            __i = importlib.import_module(f"{SELECTED}")
        else:
            __i = importlib.import_module(f".missions.{SELECTED}", package=__package__)
        return __i
    except (ImportError, AttributeError) as e:
        from .internal import log
        log.exception("Exception in mission fetching", exc_info=e)
    return None


def get_config() -> Optional[Dict]:
    m = anal_module()
    try:
        if m:
            return m.get_config()
    except AttributeError:
        pass
    return None


def set_info(image: VicarImage, axes=None, border: int = 0, **config) -> str:
    m = anal_module()
    try:
        if m:
            return m.set_info(image, axes, border, **config)
    except AttributeError:
        pass
    return "Failed"


def get_additional_functions() -> Dict[str, str]:
    m = anal_module()
    try:
        if m:
            return m.get_additional_functions()
    except AttributeError:
        pass
    return dict()
