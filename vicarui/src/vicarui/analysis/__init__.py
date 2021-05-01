from types import ModuleType
from typing import Optional, Dict, Tuple, Union

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


def get_config() -> Optional[Dict[str, Tuple[Union[str, float, int], Union[str, float, int]]]]:
    """
    Returns a default config for the Analysis module
    """
    m = anal_module()
    try:
        if m:
            return m.get_config()
    except AttributeError:
        pass
    return None


def set_info(
        image: VicarImage,
        image_axis=None,
        analysis_axis=None,
        bg_axis=None,
        border: int = 0,
        **config
) -> str:
    """
    Sets info for the subplot axes and returns a title
    """
    m = anal_module()
    try:
        if m:
            return m.set_info(
                image,
                image_axis=image_axis,
                analysis_axis=analysis_axis,
                bg_axis=bg_axis,
                border=border,
                **config
            )
    except AttributeError:
        pass
    return ""


def get_additional_functions() -> Optional[Dict[str, str]]:
    """
    Returns clear and function names for additional functions provided by the analysis module
    """
    m = anal_module()
    try:
        if m:
            return m.get_additional_functions()
    except AttributeError:
        pass
    return None
