from functools import cached_property

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
        if ovr is not None:
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
        return frame, bore, bounds

    @cached_property
    def shadow_angles(self):
        """
        Shadow angle offset and shadow angle in image

        - Shadow angle from xy plane
        - Shadow angle in image
        """
        __sp = self.pos_in_sat(self.target_id(), SUN_ID)
        __tp = __sp.copy()
        __tp[2] = 0
        __spi = self.pos_in_frame(SUN_ID, self.target_id())[0:2]
        return np.round(
            np.arccos(np.dot(__sp, __tp) / np.linalg.norm(__sp) / np.linalg.norm(__tp)) * spice.dpr(),
            7
        ), np.round(
            np.arctan(__spi[1] / __spi[0]) * spice.dpr(),
            7
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
    Transforms to shadow plane
    """

    def __init__(
            self,
            target_pos: np.ndarray,
            sun_pos: np.ndarray,
            cas_pos: np.ndarray
    ):
        z = np.linalg.norm(sun_pos[0:2])
        x = -sun_pos[2] * sun_pos[0] / z
        y = -sun_pos[2] * sun_pos[1] / z
        self.cas = cas_pos
        self.n = np.asarray([x, y, z])
        self.top = np.dot(self.n, target_pos - cas_pos)

    def __call__(self, v: np.ndarray):
        return self.cas + v * self.top / np.dot(self.n, v)


__all__ = ['ImageHelper', 'Transformer', 'ShadowPlaneIntersect']
