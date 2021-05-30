from functools import cached_property
from typing import Callable

import spiceypy

from .config import *


class Config(dict):
    """
    Helper class to wrap dict
    """

    def __init__(self, **config):
        super(Config, self).__init__(**config)

    def __getitem__(self, item):
        if item in self:
            return super(Config, self).__getitem__(item)
        else:
            return None


class ImageHelper:
    """
    Helper class to wrap an image
    """

    def __init__(self, image: VicarImage, **config):
        self.image = image
        self.config = Config(**config)

    def __getitem__(self, item: str):
        if item in self.identification():
            return self.identification()[item]
        return self.image.labels.property(item)

    def identification(self):
        """
        Image identification property
        """
        return self.image.labels.property('IDENTIFICATION')

    @cached_property
    def id(self):
        """
        Image id
        """
        return str(self.identification()['IMAGE_NUMBER'])

    @cached_property
    def target_full(self) -> Tuple[str, int]:
        target_id: int
        target: str
        ovr = self.config[TARGET_OVERRIDE]

        if ovr is not None:
            target = ovr
            target_id = spice.bods2c(ovr)
            log.debug(f'TARGET_OVERRIDE = {ovr}')
        else:
            target = self.identification()['TARGET_NAME']
            target_id = spice.bodn2c(target)
            log.debug(f'TARGET_NAME = {target}')

        return target, target_id

    def target_name(self) -> str:
        """
        Target name
        """
        return self.target_full[0]

    def target_id(self):
        """
        Target id
        """
        return self.target_full[1]

    def time_utc(self) -> str:
        """
        Image time in UTC
        """
        return self.identification()['IMAGE_TIME']

    @cached_property
    def time_et(self) -> float:
        """
        Image time in ET
        """
        return spice.utc2et(self.time_utc().strip()[:-1])

    @cached_property
    def frame(self) -> str:
        """
        Resolve frame
        """
        frame: str
        ovr = self.config[INSTRUMENT_OVERRIDE]
        if ovr is not None and ovr != "":
            frame = spice.frmnam(spice.bods2c(ovr))
        else:
            frame = l2i(self.identification()['INSTRUMENT_ID'])
        return frame

    def pos(self, target: int, obs: int) -> np.ndarray:
        """
        Position in J2K frame
        """
        return spice.spkezp(target, self.time_et, J2K, ABCORR, obs)[0]

    def pos_in_sat(self, target: int, obs: int) -> np.ndarray:
        """
        Position is IAU_SATURN frame
        """
        return spice.spkezp(target, self.time_et, SATURN_FRAME, ABCORR, obs)[0]

    def pos_in_frame(self, target: int, obs: int, frame: str = None) -> np.ndarray:
        """
        Position in frame
        """
        if frame is not None:
            return spice.spkezp(target, self.time_et, frame, ABCORR, obs)[0]
        else:
            return spice.spkezp(target, self.time_et, self.frame, ABCORR, obs)[0]

    def saturn_equator_offset(self, target: int):
        """
        Offset from Equatorial plane
        """
        return spice.spkezp(target, self.time_et, SATURN_FRAME, ABCORR, SATURN_ID)[0][2]

    @cached_property
    def fbb(self):
        """
        Frame, Bore, Bounds
        """
        _, frame, bore, _, bounds = spice.getfov(spice.bods2c(self.frame), 4)
        log.debug(f"FRAME: {frame} BORE: {bore} BOUNDS: "f"{bounds}".replace("\n", ""))
        return frame, bore, bounds

    @cached_property
    def target_radii(self) -> float:
        return np.average(spice.bodvcd(self.target_id(), 'RADII', 3)[1])

    @cached_property
    def bore_angle(self) -> float:
        """
        Angle to bore in radians
        """
        inverse_bore = -Transformer(self.frame, SATURN_FRAME, self.time_et)(self.fbb[1])
        sun_to_target = self.pos_in_sat(self.target_id(), SUN_ID)
        return np.arccos(
            np.dot(inverse_bore, sun_to_target)
            / np.linalg.norm(inverse_bore)
            / np.linalg.norm(sun_to_target)
        )

    @cached_property
    def shadow_angles(self) -> Tuple[float, float, float]:
        """
        Shadow angle offset and shadow angle in image

        - Shadow angle from xy plane
        - Shadow angle in image
        - Shadow angle to bore vector
        """
        sun_to_target = self.pos_in_sat(self.target_id(), SUN_ID)
        sun_to_target_xy = np.asarray([*sun_to_target[0:2], 0])
        sun_to_target_in_frame = self.pos_in_frame(SUN_ID, self.target_id())[0:2]
        return np.round(
            np.arccos(
                np.dot(sun_to_target, sun_to_target_xy)
                / np.linalg.norm(sun_to_target)
                / np.linalg.norm(sun_to_target_xy)
            ) * spice.dpr(),
            7
        ), np.round(
            np.arctan(sun_to_target_in_frame[1] / sun_to_target_in_frame[0]) * spice.dpr(),
            7
        ), np.round(
            self.bore_angle * spiceypy.dpr(),
            7
        )

    @property
    def y_max(self) -> int:
        return len(self.image.data[0])

    @property
    def x_max(self) -> int:
        return len(self.image.data[0][0])

    @cached_property
    def size_at_shadow(self) -> Tuple[float, float]:
        from .funcs import img_sp_size
        return img_sp_size(self)

    @cached_property
    def size_at_ring(self) -> Tuple[float, float]:
        from .funcs import img_rp_size
        return img_rp_size(self)

    @cached_property
    def size_at_target(self) -> Tuple[float, float]:
        from .funcs import img_raw_size
        return img_raw_size(self)

    def per_px(self, km_size: Tuple[float, float]):
        return np.divide(km_size[0], self.x_max), np.divide(km_size[1], self.y_max)

    @property
    def size(self) -> Tuple[float, float]:
        sf = self.config[SIZE_FRAME]
        if sf == SIZE_AT_RING:
            return self.size_at_ring
        elif sf == SIZE_AT_SHADOW:
            return self.size_at_shadow
        else:
            return self.size_at_target

    @property
    def size_name(self) -> str:
        sf = self.config[SIZE_FRAME]
        if sf == SIZE_AT_RING:
            return "Ring"
        elif sf == SIZE_AT_SHADOW:
            return "Shadow"
        else:
            return "Target"

    @property
    def size_selection(self) -> int:
        try:
            return self.config[SIZE_FRAME]
        except KeyError:
            return 0

    @property
    def size_per_px(self):
        return self.per_px(self.size)

    @property
    def size_x_transforms(self) -> Tuple[Callable, Callable]:
        return (
            lambda x: self.size_per_px[0] * x,
            lambda x: np.reciprocal(self.size_per_px[0]) * x
        )

    @property
    def size_y_transforms(self) -> Tuple[Callable, Callable]:
        return (
            lambda y: self.size_per_px[1] * y,
            lambda y: np.reciprocal(self.size_per_px[1]) * y
        )


class Transformer:
    """
    Wraps a frame transformation
    """

    def __init__(self, from_frame: str, to_frame: str, et: float):
        self.from_frame = from_frame
        self.to_frame = from_frame
        self.et = et
        self.transform = spice.pxform(from_frame, to_frame, et)

    def __call__(self, *args: np.ndarray) -> Union[np.ndarray, Tuple[np.ndarray, ...]]:
        if len(args) == 1:
            return spice.mxv(self.transform, args[0])
        else:
            return tuple(spice.mxv(self.transform, a) for a in args)

    def __neg__(self):
        return Transformer(self.to_frame, self.from_frame, self.et)


class ShadowPlaneIntersect:
    """
    Transforms a vector to point to the nearest point to shadow CASSINI ONLY

    Tries to transform a fov boundary vector to a point where it intersects the X,Y-projection
    of the shadow or sun vector
    """

    def __init__(self, helper: ImageHelper):
        cas = helper.pos_in_sat(CASSINI_ID, SATURN_ID)
        target = helper.pos_in_sat(helper.target_id(), SATURN_ID)
        sv = helper.pos_in_sat(SUN_ID, helper.target_id())
        self.cas = cas
        self.a_ratio = sv[1] / sv[0]
        self.y_diff = target[1] - cas[1]
        self.x_diff_part = self.a_ratio * (cas[0] - target[0])

    def __call__(self, v: np.ndarray):
        times = (self.y_diff + self.x_diff_part) / (v[1] - self.a_ratio * v[0])
        return self.cas + times * v


__all__ = ['ImageHelper', 'Transformer', 'ShadowPlaneIntersect']
