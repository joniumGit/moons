from collections import Generator
from dataclasses import dataclass
from typing import Any

from ..config import *
from ..funcs import norm
from ..helpers import ImageHelper, Transformer
from ....fitting import DataPacket
from ....fitting import contrast_2nd_deg, integrate_2nd_deg
from ....wrapper import ImageWrapper


@dataclass(frozen=False)
class Selection:
    initial_position: Tuple[float, float]
    target_position: Tuple[float, float]
    is_vertical: bool
    shadow_radius: float
    width: int
    window: int
    length: int


@dataclass(frozen=True)
class Fit:
    arg_max: float
    contrast: float
    integral: float
    distance_px: Tuple[float, float]

    def is_finite(self):
        return np.alltrue(np.isfinite([self.contrast, self.integral])) and self.contrast > 0 and self.integral > 0

    def __getitem__(self, i: int):
        if i == 0:
            return self.contrast
        elif i == 1:
            return self.integral
        elif i == 2:
            return self.distance_px
        else:
            return self.arg_max


class AutoFit:
    packet: DataPacket
    start_x: int
    start_y: int

    def __init__(self, packet: DataPacket):
        self.packet = packet
        self.start_x = 0
        self.start_y = 0

    def select(self, x: int, y: int, vertical: bool = False) -> Any:
        return self.packet.select(x, y, vertical)

    def fit(self, x: float, y: float) -> Fit:
        data = self.packet.fit(x, y, suppress=True)
        bg = data['BG']['equation']
        fg = data['FIT']['equation']

        x_val, contrast = contrast_2nd_deg(bg, fg)
        integral = integrate_2nd_deg(bg, fg)
        dist_px = (np.abs(self.start_x - x), np.abs(self.start_y - y))
        return Fit(
            arg_max=x_val,
            contrast=contrast,
            integral=integral,
            distance_px=dist_px
        )


class FitHelper:

    def __init__(self, image: ImageWrapper, helper: ImageHelper):
        self.data = image.processed
        self.packet = DataPacket(self.data)
        self.autofit = AutoFit(self.packet)
        self.shadow = norm(Transformer(SATURN_FRAME, helper.frame, helper.time_et)(
            helper.pos_in_sat(SUN_ID, helper.target_id()))
        )[0:2]
        self.im_helper = helper

    def __call__(self, s: Selection) -> Generator[Tuple[Any, Fit]]:
        self.packet.configure(s.width, s.window)

        iterations = s.length
        radius = s.shadow_radius
        vertical = s.is_vertical

        shadow = self.shadow
        initial = s.initial_position

        autofit = self.autofit
        autofit.start_x, autofit.start_y = s.target_position

        if vertical:
            for i in range(
                    int(initial[0]),
                    int(initial[0] + iterations * np.sign(shadow[0])),
                    int(1 * np.sign(shadow[0]))
            ):
                rect = autofit.select(int(initial[0]), int(initial[1]), vertical)
                fit = autofit.fit(initial[1] - radius, initial[1] + radius)
                yield rect, fit
                initial = (i, initial[1] + shadow[1] * np.abs(1 / shadow[0]))
        else:
            for i in range(
                    int(initial[1]),
                    int(initial[1] + iterations * np.sign(shadow[1])),
                    int(1 * np.sign(shadow[1]))
            ):
                rect = autofit.select(int(initial[0]), int(initial[1]))
                fit = autofit.fit(initial[0] - radius, initial[0] + radius)
                yield rect, fit
                initial = (initial[0] + shadow[0] * np.abs(1 / shadow[1]), i)


__all__ = [
    'Selection',
    'AutoFit',
    'Fit',
    'FitHelper'
]
