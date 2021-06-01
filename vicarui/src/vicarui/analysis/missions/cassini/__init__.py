from .autoanalyzer import auto
from .config import get_config
from .geometry import view_geometry
from .labels import view_labels
from .set_info import set_info


def get_additional_functions():
    return {
        "View Image Geometry": "view_geometry",
        "View Labels": "view_labels",
        "Auto-Analyzer": "auto"
    }


__all__ = ['get_config', 'view_labels', 'view_geometry', 'set_info', 'auto']
