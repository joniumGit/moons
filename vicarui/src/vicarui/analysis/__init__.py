from types import ModuleType
from typing import Optional, Dict, Tuple, Union, Callable, List

from .fitting import DataPacket
from .kernels import provide_kernels
from .pipe import Pipe, OLSWrapper
from .reduction import br_reduction
from .tex import *
from .wrapper import ImageWrapper


class _Holder(object):
    mission: str = "cassini"
    listeners: List[Callable[[str], None]] = list()


def select_mission(mission: str):
    if mission is None:
        mission = "empty"
    mission = mission.strip()
    _Holder.mission = mission
    for listener in _Holder.listeners:
        listener(mission)


def get_mission() -> str:
    return _Holder.mission


def register_mission_listener(listener: Callable[[str], None]):
    _Holder.listeners.append(listener)


def remove_mission_listener(listener: Callable[[str], None]):
    _Holder.listeners.remove(listener)


def anal_module() -> Optional[ModuleType]:
    import importlib
    try:
        mission = get_mission()
        if '.' in mission:
            __i = importlib.import_module(f"{mission}")
        else:
            __i = importlib.import_module(f".missions.{mission}", package=__package__)
        return __i
    except (ImportError, AttributeError) as e:
        from .internal import log
        log.exception("Exception in mission fetching", exc_info=e)
        select_mission("empty")
    return None


def get_config() -> Optional[Dict[str, Tuple[Union[str, float, int], Union[str, float, int]]]]:
    """
    Returns a default config for the Analysis module
    """
    m = anal_module()
    try:
        if m:
            # noinspection PyUnresolvedReferences
            return m.get_config()
    except AttributeError:
        pass
    return None


def set_info(
        image: ImageWrapper,
        image_axis=None,
        analysis_axis=None,
        bg_axis=None,
        **config
) -> str:
    """
    Sets info for the subplot axes and returns a title
    """
    m = anal_module()
    try:
        if m:
            # noinspection PyUnresolvedReferences
            return m.set_info(
                image,
                image_axis=image_axis,
                analysis_axis=analysis_axis,
                bg_axis=bg_axis,
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
            # noinspection PyUnresolvedReferences
            return m.get_additional_functions()
    except AttributeError:
        pass
    return None
