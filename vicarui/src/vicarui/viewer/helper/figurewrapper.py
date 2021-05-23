from typing import Callable, Optional, Any, Union, Tuple, Dict

import numpy as np
from PySide2.QtCore import QThread
from astropy.visualization import ImageNormalize
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from .imageevent import VicarEvent
from ...analysis import ImageWrapper, set_info
from ...support import logging as log
from ...support import stop_progress, start_progress


class BRTask(QThread):
    from ...support import typedsignal
    done = typedsignal(tuple)

    def __init__(self, image: ImageWrapper, br_pack: Dict):
        super(BRTask, self).__init__()
        self._image = image
        self._br_pack = br_pack

    def run(self) -> None:
        from ...analysis import br_reduction
        image = self._image
        varargs = self._br_pack
        data, mask, err = br_reduction(image, **varargs)
        self.done.emit((data, mask, err))
        self.quit()


class FigureWrapper(FigureCanvasQTAgg):
    event_handler: Optional[VicarEvent] = None
    from ...support import signal
    image_shown = signal()

    class Holder:
        image: ImageWrapper

        data: Axes = None
        original: Axes = None
        background: Axes = None
        line: Axes = None

        norm: ImageNormalize = None
        click: Tuple[int, int] = None

    _holder: Holder = None
    _task: QThread = None

    def __init__(self, width=7.5, height=7.5, dpi=125):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(FigureWrapper, self).__init__(self.fig)

    def clear(self):
        if self.event_handler is not None:
            self.event_handler.detach()
            self.event_handler = None
        self.fig.clf(keep_observers=True)

    def _show_image_2(self, from_task: Tuple[np.ndarray, np.ndarray, float]):
        reduced, mask, err = from_task
        og = self._holder.original
        bg = self._holder.background
        norm = self._holder.norm
        line = self._holder.line
        image = self._holder.image
        data = self._holder.data

        og.imshow(image.get_image(), cmap="gray", interpolation='none', origin='upper')
        bg.imshow(mask, cmap="coolwarm", interpolation='none', origin='upper')
        bg.imshow(image.get_outliers(), cmap='binary_r', interpolation="none", origin="upper", alpha=0.3)
        bg.set_title(bg.get_title() + f" mse: {err:.5e}")

        normalizer = norm(reduced)
        data.imshow(
            reduced,
            norm=normalizer,
            cmap="gray",
            aspect="equal",
            interpolation='none',
            origin='upper'
        )
        data.minorticks_on()

        if normalizer:
            reduced = normalizer(reduced)

        self.event_handler = VicarEvent(reduced, data, line, self._holder.click)
        self.figure.set_tight_layout('true')
        self.draw()

        self._holder = None
        self._task = None
        self.image_shown.emit()
        stop_progress()

    def _show_image_1(self, image: ImageWrapper, **kwargs):
        data = self.fig.add_subplot(3, 3, (2, 6))
        og = self.fig.add_subplot(331)
        bg = self.fig.add_subplot(334)
        line = self.fig.add_subplot(3, 3, (7, 9))

        self._holder.data = data
        self._holder.original = og
        self._holder.background = bg
        self._holder.line = line

        data.set_title("image")
        og.set_title("original")
        bg.set_title("background")
        line.set_title("line")

        try:
            self.fig.suptitle(
                set_info(
                    image,
                    image_axis=data,
                    analysis_axis=line,
                    background=bg,
                    **kwargs
                ),
                fontsize='small',
                fontfamily='monospace'
            )
        except Exception as e:
            log.exception("Failed to set info", exc_info=e)

    def show_image(
            self,
            image: ImageWrapper,
            norm: Callable[[np.ndarray], Union[ImageNormalize, None]],
            br_pack: Dict[str, Any],
            click_area: Tuple[int, int],
            **kwargs
    ):
        start_progress()
        self._holder = self.Holder()
        self._holder.image = image
        self._holder.norm = norm
        self._holder.click = click_area
        self._show_image_1(image, **kwargs)
        self._task = BRTask(image, br_pack)
        self._task.done.connect(self._show_image_2)
        self._task.start()


__all__ = ['FigureWrapper']
