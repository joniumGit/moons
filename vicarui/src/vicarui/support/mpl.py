from matplotlib.axes import Axes

MPL_FONT_CONFIG = {'fontfamily': 'monospace', 'fontsize': 'small'}
PAD = {'pad': 3}


class AxesWrapper(Axes):
    def get_first_left(self) -> str:
        pass

    def set_title(self, title: str, loc: str = None, **kwargs):
        pass

    def append(self, title: str, loc: str = None, **kwargs):
        pass

    def set_left(self, title: str, **kwargs):
        pass

    def append_left(self, title: str, **kwargs):
        pass

    def legend(self, **kwargs):
        pass

    def refresh(self):
        pass

    def clear_lines(self):
        pass


def append_to_axes():
    def get_first_left(self) -> str:
        return self.get_title(loc='left').split("\n")[0]

    stc = Axes.set_title

    def set_title(self, title: str, loc: str = None, **kwargs):
        stc(self, title, loc=loc, **PAD, **MPL_FONT_CONFIG, **kwargs)

    def append(self, title: str, loc: str = None, **kwargs):
        self.set_title(self.get_title(loc=loc) + "\n" + title, loc=loc, **kwargs)

    def set_left(self, title: str, **kwargs):
        self.set_title(title, loc='left', **kwargs)

    def append_left(self, title: str, **kwargs):
        self.append(title, loc='left', **kwargs)

    ldc = Axes.legend

    def legend(self, **kwargs):
        ldc(self, fontsize='small', **kwargs)

    def refresh(self):
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    def clear_lines(self):
        self.lines.clear()

    Axes.get_first_left = get_first_left

    Axes.set_title = set_title

    Axes.append = append
    Axes.set_left = set_left
    Axes.append_left = append_left
    Axes.legend = legend
    Axes.refresh = refresh
    Axes.clear_lines = clear_lines
