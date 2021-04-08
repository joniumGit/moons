import inspect
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Callable
from typing import TypeVar, Type

import PySide2.QtGui as qg
import PySide2.QtWidgets as qw
from PySide2.QtWidgets import QDialog
from astropy.visualization import (
    HistEqStretch,
    PowerStretch,
    LogStretch,
    SqrtStretch,
    LinearStretch,
    BaseStretch,
    AsymmetricPercentileInterval,
    MinMaxInterval,
    ZScaleInterval,
    ManualInterval
)
from vicarutil.image import VicarImage


class StretchBase(object, ABC):

    def __init__(self, *_, **__):
        super(StretchBase, self).__init__()

    @abstractmethod
    def pre(self, image: Optional[VicarImage] = None):
        pass

    @abstractmethod
    def get(self) -> BaseStretch:
        pass


class HistEqWidget:
    stretch: HistEqStretch

    def __init__(self):
        super(HistEqWidget, self).__init__()


class PowerWidget:
    stretch: PowerStretch


class LogWidget:
    stretch: LogStretch


class SqrtWidget:
    stretch: SqrtStretch


class LinearWidget:
    stretch: LinearStretch


def make_stretch(s: StretchBase, image: VicarImage) -> BaseStretch:
    signature = inspect.signature(s.pre)
    if signature.parameters['image'].default == inspect.Parameter.empty:
        s.pre(image=image)
    else:
        s.pre()
    return s.get()


T = TypeVar('T', int, float, str)


class AskParam(object):
    def __init__(
            self,
            t: Type[T],
            description: Optional[str] = None,
            default: Optional[T] = None,
            _min: Optional[T] = None,
            _max: Optional[T] = None
    ):
        self.t = t
        self.description = description
        self.default = default
        self.min = _min
        self.max = _max

    def set_value(self, value: str):
        if self.t == int:
            self._value = int(value)
        elif self.t == float:
            self._value = float(value)
        else:
            self._value = value

    def get_value(self):
        try:
            return self._value or self.default
        finally:
            self._value = None

    _value: Optional[T]


class BaseWidget(ABC):

    def __init__(self, *_, **__):
        super(BaseWidget, self).__init__()

    @abstractmethod
    def create(self, *_, **__):
        pass


class AsymmetricWidget:
    interval: AsymmetricPercentileInterval


class MinMaxWidget:
    interval: MinMaxInterval


class ManualWidget(BaseWidget):

    def create(
            self,
            vmin=AskParam(float),
            vmax=AskParam(float)
    ):
        return ManualInterval(
            vmin=vmin.get_value(),
            vmax=vmax.get_value()
        )


class ZScaleWidget(BaseWidget):

    def create(
            self,
            nsamples=AskParam(int, default=1000),
            contrast=AskParam(float, default=0.25),
            max_reject=AskParam(float, default=0.5),
            min_npixels=AskParam(int, default=5),
            krej=AskParam(float, default=2.5),
            max_iterations=AskParam(int, default=5)
    ):
        return ZScaleInterval(
            nsamples=nsamples.get_value(),
            contrast=contrast.get_value(),
            max_reject=max_reject.get_value(),
            min_npixels=min_npixels.get_value(),
            krej=krej.get_value(),
            max_iterations=max_iterations.get_value()
        )


def _create_input(name: str, param: AskParam) -> Tuple[qw.QFrame, Callable[[], None]]:
    editor = qw.QLineEdit()
    label = qw.QLabel(text=param.description or name)
    validator: Optional[qg.QValidator] = None
    if param.t == int:
        validator = qg.QIntValidator()
    elif param.t == float:
        validator = qg.QDoubleValidator()
    if validator is not None:
        if param.min is not None:
            validator.setBottom(param.min)
        if param.max is not None:
            validator.setTop(param.max)
    frame = qw.QFrame()
    layout = qw.QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(editor)
    frame.setLayout(layout)
    if param.default is not None:
        if param.t == float:
            editor.setText(f"{param.default:.3f}")
        else:
            editor.setText(str(param.default))

    def callback():
        text = editor.text()
        if text is not None and text.strip() != "":
            param.set_value(text.strip())

    return frame, callback


class Ask(QDialog):

    def __init__(self, target: BaseWidget, on_success: Callable[[], None], parent=None):
        super(Ask, self).__init__(parent)
        self.setWindowTitle("Set parameters")
        params = inspect.signature(target.create).parameters
        callbacks = list()
        components = list()
        for p in params:
            if isinstance(params[p].default, AskParam):
                component, callback = _create_input(p, params[p].default)
                callbacks.append(callback)
                components.append(component)
        layout = qw.QVBoxLayout()
        for c in components:
            layout.addWidget(c)
        btn = qw.QPushButton(text="OK")

        def fire():
            for cb in callbacks:
                cb()
            on_success()

        btn.clicked.connect(fire)
        self.setLayout(layout)
