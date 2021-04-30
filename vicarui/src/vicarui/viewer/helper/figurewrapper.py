from typing import Callable, Optional, Any, Union, Tuple, Dict

import numpy as np
from astropy.visualization import ImageNormalize
from matplotlib.axes import Axes
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from .imageevent import VicarEvent
from ...analysis import br_reduction, ImageWrapper, set_info
from ...support import logging as log


class FigureWrapper(FigureCanvasQTAgg):
    event_handler: Optional[VicarEvent] = None

    def __init__(self, width=7.5, height=7.5, dpi=125):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(FigureWrapper, self).__init__(self.fig)

    def clear(self):
        if self.event_handler is not None:
            self.event_handler.detach()
            self.event_handler = None
        self.fig.clf(keep_observers=True)

    def show_image(
            self,
            image: ImageWrapper,
            norm: Callable[[np.ndarray], Union[ImageNormalize, None]],
            br_pack: Dict[str, Any],
            click_area: Tuple[int, int],
            **kwargs
    ):
        data_axis: Axes = self.fig.add_subplot(3, 3, (2, 6))
        og_axis = self.fig.add_subplot(331)
        bg_axis = self.fig.add_subplot(334)
        line_axis = self.fig.add_subplot(3, 3, (7, 9))

        data_axis.set_title("Post-Processed")
        og_axis.set_title("original")
        bg_axis.set_title("background")
        line_axis.set_title("line")

        try:
            self.fig.suptitle(
                set_info(image.get_raw(), axes=data_axis, border=br_pack['border'] or 0, **kwargs),
                fontsize='small',
                fontfamily='monospace'
            )
        except Exception as e:
            log.exception("Failed to set info", exc_info=e)

        data, mask, err = br_reduction(image, **br_pack)

        og_axis.imshow(image.get_image(), cmap="gray", interpolation='none')
        bg_axis.imshow(mask, cmap="coolwarm", interpolation='none')
        bg_axis.set_title(bg_axis.get_title() + f" mse: {err:.5e}")

        normalizer = norm(data)
        data_axis.imshow(
            data,
            norm=normalizer,
            cmap="gray",
            aspect="equal",
            interpolation='none'
        )
        data_axis.minorticks_on()

        for x in self.fig.axes:
            if x != line_axis:
                x.invert_yaxis()

        if normalizer:
            data = normalizer(data)
        else:
            data_axis.set_title("No Post-Processing")

        self.event_handler = VicarEvent(data, data_axis, line_axis, click_area)
        self.figure.set_tight_layout('true')
        self.draw()
