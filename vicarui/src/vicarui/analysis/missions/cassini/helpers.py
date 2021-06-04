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
        if item in self.identification:
            return self.identification[item]
        return self.image.labels.property(item)

    @property
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
        return str(self.identification['IMAGE_NUMBER'])

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
            target = self.identification['TARGET_NAME']
            target_id = spice.bodn2c(target)
            log.debug(f'TARGET_NAME = {target}')

        return target, target_id

    @property
    def target_name(self) -> str:
        """
        Target name
        """
        return self.target_full[0]

    @property
    def target_id(self):
        """
        Target id
        """
        return self.target_full[1]

    @property
    def time_utc(self) -> str:
        """
        Image time in UTC
        """
        return self.identification['IMAGE_TIME']

    @cached_property
    def time_et(self) -> float:
        """
        Image time in ET
        """
        return spice.utc2et(self.time_utc.strip()[:-1])

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
            frame = l2i(self.identification['INSTRUMENT_ID'])
        return frame

    @cached_property
    def target_distance(self):
        return np.linalg.norm(self.crps(self.target_id))

    @cached_property
    def phase_angle(self) -> float:
        """
        Phase angle of target in radians

        https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/phaseq_c.html

        :return: Phase angle in radians
        """
        return spice.phaseq(self.time_et, self.target_name, SUN, CASSINI, Correction.CNS)

    @cached_property
    def lts(self) -> float:
        """
        Light time correction between target and cassini calculated with LTS
        """
        return spiceypy.spkezp(self.target_id, self.time_et, J2K, Correction.LTS, CASSINI_ID)[1]

    @property
    def target_time(self) -> float:
        """
        Time at Target
        """
        return self.time_et - self.lts

    def trp(self, obj: int, frame: str, correction: str = Correction.LT) -> np.ndarray:
        """
        Target relative position in the specified frame
        """
        return spice.spkezp(obj, self.target_time, frame, correction, self.target_id)[0]

    def trpf(self, obj: int, correction: str = Correction.LT) -> np.ndarray:
        """
        Target Relative Position in Frame
        """
        return self.trp(obj, self.frame, correction)

    def trps(self, obj: int, correction: str = Correction.LT) -> np.ndarray:
        """
        Target Relative Position in Saturn Frame
        """
        return self.trp(obj, SATURN_FRAME, correction)

    def crp(self, obj: int, frame: str, correction: str = Correction.LTS) -> np.ndarray:
        """
        Cassini relative position in the specified frame
        """
        return spice.spkezp(obj, self.time_et, frame, correction, CASSINI_ID)[0]

    def crpf(self, obj: int, correction: str = Correction.LTS) -> np.ndarray:
        """
        Cassini Relative Position in Frame
        """
        return self.crp(obj, self.frame, correction)

    def crps(self, obj: int, correction: str = Correction.LTS) -> np.ndarray:
        """
        Cassini relative position in Saturn Frame
        """
        return self.crp(obj, SATURN_FRAME, correction)

    def ltsp(self, target: int, obs: int, frame: str, correction: str = Correction.LTS) -> np.ndarray:
        """
        Position in Any frame reduced by the image light time (Cassini - Target)

        :param target: The target being observed
        :param obs: The observer
        :param frame: Reference frame to output the vector in
        :param correction: The Aberration correction setting to be used
        :returns: Position as a 3-Vector
        """
        return spice.spkezp(target, self.target_time, frame, correction, obs)[0]

    def pos(self, target: int, obs: int, frame: str, correction: str = Correction.LTS) -> np.ndarray:
        """
        Position in Any frame at image ET

        :param target: The target being observed
        :param obs: The observer
        :param frame: Reference frame to output the vector in
        :param correction: The Aberration correction setting to be used
        :returns: Position as a 3-Vector
        """
        return spice.spkezp(target, self.time_et, frame, correction, obs)[0]

    def pos_in_sat(self, target: int, obs: int, correction: str = Correction.NONE) -> np.ndarray:
        """
        Position is IAU_SATURN frame
        """
        return spice.spkezp(target, self.time_et, SATURN_FRAME, correction, obs)[0]

    def pos_in_frame(self, target: int, obs: int, frame: str = None, correction: str = Correction.NONE) -> np.ndarray:
        """
        Position in frame
        """
        return spice.spkezp(target, self.time_et, frame or self.frame, correction, obs)[0]

    def saturn_equator_offset(self, target: int):
        """
        Offset from Equatorial plane
        """
        return spice.spkezp(target, self.time_et, SATURN_FRAME, Correction.LT, SATURN_ID)[0][2]

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
        return np.average(spice.bodvcd(self.target_id, 'RADII', 3)[1])

    @cached_property
    def bore_angle(self) -> float:
        """
        Angle to bore in radians
        """
        bore = Transformer(self.frame, SATURN_FRAME, self.time_et)(self.fbb[1])
        sun = self.trps(SUN_ID)
        return np.arccos(
            np.dot(-bore, -sun)
            / np.linalg.norm(sun)
            / np.linalg.norm(bore)
        )

    @cached_property
    def shadow_angles(self) -> Tuple[float, float, float]:
        """
        Shadow angle offset and shadow angle in image DEG

        - Shadow angle from xy plane
        - Shadow angle in image
        - Shadow angle to image
        """
        sun_to_target = self.trps(SUN_ID, correction=Correction.LT)
        sun_to_target_xy = np.asarray([*sun_to_target[0:2], 0])
        sun_to_target_in_frame = self.trpf(SUN_ID)[0:2]
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
            (self.phase_angle - spice.pi() / 2) * spiceypy.dpr(),
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
        cas = helper.pos(CASSINI_ID, SATURN_ID, SATURN_FRAME, Correction.NONE)
        target = helper.ltsp(helper.target_id, SATURN_ID, SATURN_FRAME, Correction.NONE)
        sv = helper.trps(SUN_ID)
        self.cas = cas
        self.a_ratio = sv[1] / sv[0]
        self.y_diff = target[1] - cas[1]
        self.x_diff_part = self.a_ratio * (cas[0] - target[0])

    def __call__(self, v: np.ndarray):
        times = (self.y_diff + self.x_diff_part) / (v[1] - self.a_ratio * v[0])
        return self.cas + times * v


__all__ = ['ImageHelper', 'Transformer', 'ShadowPlaneIntersect']
