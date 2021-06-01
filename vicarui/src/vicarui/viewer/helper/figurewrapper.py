from typing import Callable, Optional, Any, Union, Tuple, Dict

import numpy as np
from PySide2.QtCore import QThread
from astropy.visualization import ImageNormalize
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from .imageevent import VicarEvent
from ...analysis import set_info
from ...logging import log
from ...support import stop_progress, start_progress, signal, BRTask, ImageWrapper


class FigureWrapper(FigureCanvasQTAgg):
    event_handler: Optional[VicarEvent] = None
    image_shown = signal()

    class Holder:
        image: ImageWrapper

        data: Axes = None
        original: Axes = None
        background: Axes = None
        line: Axes = None

        norm: ImageNormalize = None
        click: Callable[[], Tuple[int, int]] = None

    _holder: Holder = None
    _task: QThread = None

    def __init__(self, width=7.5, height=7.5, dpi=125):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(FigureWrapper, self).__init__(self.fig)

    def clear(self, restore: bool = False):
        if hasattr(self, '_data'):
            if restore:
                try:
                    self._limits = self._data.images[0].get_clim()
                    delattr(self, '_data')
                except IndexError:
                    pass
            else:
                if hasattr(self, '_limits'):
                    delattr(self, '_limits')
                delattr(self, '_data')
        if self.event_handler is not None:
            self.event_handler.detach()
            self.event_handler = None
        self.fig.clf(keep_observers=True)

    def _data_limits(self, ax: Axes):
        if hasattr(self, '_limits'):
            try:
                ax.images[0].set_clim(self._limits)
                delattr(self, '_limits')
            except IndexError:
                pass

    def _show_image_2(self):
        og = self._holder.original
        bg = self._holder.background
        norm = self._holder.norm
        line = self._holder.line
        data = self._holder.data
        image = self._holder.image

        self.event_handler = VicarEvent(image.processed, data, line, self._holder.click)

        reduced = image.normalize(image.processed)
        normalizer = norm(reduced)
        data.imshow(reduced, norm=normalizer, cmap="gray", aspect="equal", interpolation='none', origin='upper')
        og.imshow(image.original, cmap="gray", interpolation='none', origin='upper')
        bg.imshow(image.background, cmap="coolwarm", interpolation='none', origin='upper')
        bg.imshow(image.outliers, cmap='binary_r', interpolation="none", origin="upper", alpha=0.3)
        bg.set_title(bg.get_title() + f" mse: {image.mse:.5e}")

        self._data_limits(data)
        data.minorticks_on()

        self.figure.set_tight_layout('true')

        self.draw()
        self.flush_events()

        self._holder = None
        self._task = None
        self.image_shown.emit()

        stop_progress()

    def _show_image_1(self, image: ImageWrapper, **kwargs):
        self._data: Axes = self.fig.add_subplot(3, 3, (2, 6), label='Image Display')
        data = self._data

        og = self.fig.add_subplot(331, label="Original Image")
        bg = self.fig.add_subplot(334, label="Background")
        line = self.fig.add_subplot(3, 3, (7, 9), label="Line")

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
            click_area: Callable[[], Tuple[int, int]],
            restore: bool = False,
            **kwargs
    ):
        start_progress()
        self.clear(restore)

        self._holder = self.Holder()
        self._holder.image = image
        self._holder.norm = norm
        self._holder.click = click_area
        self._show_image_1(image, **kwargs)
        self._task = BRTask(image, br_pack)
        self._task.done.connect(self._show_image_2)

        self._task.start()

    def click(self, pkg: Tuple[float, float, bool]):
        x, y, right = pkg
        try:
            handler = self.event_handler
            from matplotlib.backend_bases import MouseButton
            handler.data_axis_handler(x, y, MouseButton.RIGHT if right else MouseButton.LEFT)
        except AttributeError:
            pass


__all__ = ['FigureWrapper']
