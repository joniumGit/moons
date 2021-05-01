from typing import Optional, List, Tuple, Union

import numpy as np
import spiceypy as spice
from vicarutil.image import VicarImage

from ..internal import log
from ..kernels import load_kernels_for_image, release_kernels

log.debug('Initializing SPICE: %s' + spice.tkvrsn('TOOLKIT'))

# https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/req/naif_ids.html
CASSINI = 'CASSINI'
SATURN = 'SATURN'
SUN = 'SUN'

CASSINI_ID = -82
SATURN_ID = 699
SUN_ID = 10

ABCORR = 'LT+S'
J2K = 'J2000'
RADII = 'RADII'
POLE_RA = 'POLE_RA'

FRAME_WAC = 'CASSINI_ISS_WAC'
FRAME_NAC = 'CASSINI_ISS_NAC'
LABEL_WAC = 'ISSWA'
LABEL_NAC = 'ISSNA'

PLANETOCENTRIC = 'PLANETOCENTRIC'
SATURN_FRAME = 'IAU_SATURN'

TARGET_ESTIMATE = "Draw Target Estimate"
SUN_SATURN_VECTORS = "Draw Sun Saturn Vectors"
TARGET_OVERRIDE = "Target Override"
INSTRUMENT_OVERRIDE = "Instrument Override"
SIZE_FRAME = "Size at plane (0: ring, 1: shadow, 2: raw)"
CUBIC = "Show geometry in a cubic frame"


def get_config():
    return {
        TARGET_ESTIMATE: (bool, False),
        SUN_SATURN_VECTORS: (bool, True),
        TARGET_OVERRIDE: (str, None),
        INSTRUMENT_OVERRIDE: (str, None),
        SIZE_FRAME: (int, 1),
        CUBIC: (bool, True)
    }


def get_additional_functions():
    return {
        "View Image Geometry": "view_geometry",
        "View Labels": "view_labels"
    }


class Config(dict):

    def __init__(self, **config):
        super(Config, self).__init__(**config)

    def __getitem__(self, item):
        if item in self:
            return super(Config, self).__getitem__(item)
        else:
            return None


class ImageHelper:

    def __init__(self, image: VicarImage, **config):
        self.image = image
        self.config = Config(**config)
        self.resolved = dict()

    def __getitem__(self, item: str):
        return self.image.labels.property(item)

    def identification(self):
        return self.image.labels.property('IDENTIFICATION')

    def id(self):
        return str(self.identification()['IMAGE_NUMBER'])

    def target_full(self) -> Tuple[Optional[str], Optional[int]]:
        if 't-data' in self.resolved:
            return self.resolved['t-data']
        else:
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

            self.resolved['t-data'] = (target, target_id)
            return target, target_id

    def target_name(self) -> str:
        return self.target_full()[0]

    def target_id(self):
        return self.target_full()[1]

    def time_utc(self) -> str:
        return self.identification()['IMAGE_TIME']

    def time_et(self) -> float:
        if 'et' in self.resolved:
            return self.resolved['et']
        else:
            et = spice.utc2et(self.time_utc().strip()[:-1])
            self.resolved['et'] = et
            return et

    def frame(self) -> str:
        if 'frame' in self.resolved:
            return self.resolved['frame']
        else:
            frame: str
            ovr = self.config[INSTRUMENT_OVERRIDE]

            if ovr is not None:
                frame = spice.frmnam(spice.bods2c(ovr))
            else:
                raw_instrument = self.identification()['INSTRUMENT_ID']
                if raw_instrument == LABEL_WAC:
                    frame = FRAME_WAC
                elif raw_instrument == LABEL_NAC:
                    frame = FRAME_NAC
                else:
                    frame = FRAME_NAC

            self.resolved['frame'] = frame
            return frame

    def pos(self, target: int, obs: int) -> np.ndarray:
        return spice.spkezp(target, self.time_et(), J2K, ABCORR, obs)[0]

    def pos_in_sat(self, target: int, obs: int) -> np.ndarray:
        return spice.spkezp(target, self.time_et(), SATURN_FRAME, ABCORR, obs)[0]

    def pos_in_frame(self, target: int, obs: int, frame: str = None) -> np.ndarray:
        if frame is not None:
            return spice.spkezp(target, self.time_et(), frame, ABCORR, obs)[0]
        else:
            return spice.spkezp(target, self.time_et(), self.frame(), ABCORR, obs)[0]

    def saturn_equator_offset(self, target: int):
        return spice.spkezp(target, self.time_et(), SATURN_FRAME, ABCORR, SATURN_ID)[0][2]

    def fbb(self):
        _, frame, bore, _, bounds = spice.getfov(spice.bods2c(self.frame()), 4)
        return frame, bore, bounds

    def shadow_angles(self):
        """
        Shadow angle offset from Z and shadow angle in image
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

    def __init__(self, from_frame: str, to_frame: str, et: float):
        self.transform = spice.pxform(from_frame, to_frame, et)

    def __call__(self, *args: np.ndarray) -> Union[np.ndarray, Tuple[np.ndarray, ...]]:
        if len(args) == 1:
            return spice.mxv(self.transform, args[0])
        else:
            return tuple(spice.mxv(self.transform, a) for a in args)


class ShadowPlaneIntersect:

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


def max_mag(bore: np.ndarray, corners: np.ndarray):
    from itertools import combinations
    max_sep = np.sort(np.asarray([np.linalg.norm(a - b) for a, b in combinations(corners, 2)]))

    x, y = np.abs(bore[0:2])

    larger = np.average(max_sep[2:4])
    smaller = np.average(max_sep[0:2])

    log.info("Corner diffs: " + ','.join([f"{a:.5e}" for a in max_sep[:-2]]))

    if x < y:
        # y-diff is bigger
        return smaller, larger
    else:
        return larger, smaller


def norm(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n != 0:
        return v / n
    else:
        return np.zeros(v.shape)


def img_rp_size(helper: ImageHelper) -> Tuple[float, float]:
    """
    Size of image in x, y in kilometers in the Saturn ring plane
    """
    cas = spice.spkezp(CASSINI_ID, helper.time_et(), SATURN_FRAME, ABCORR, SATURN_ID)[0]
    frame, bore, bounds = helper.fbb()
    t = Transformer(frame, SATURN_FRAME, helper.time_et())
    cas_xy = cas[0:2]
    cas_z = cas[2]
    corners = list()
    for b in bounds:
        tb = t(b)
        corners.append(cas_xy + tb[0:2] * (-cas_z / tb[2]))

    return max_mag(t(bore), np.asarray(corners))


def img_sp_size(helper: ImageHelper):
    cassini_pos = helper.pos_in_sat(CASSINI_ID, SATURN_ID)
    sun_vec = helper.pos_in_sat(SUN_ID, helper.target_id())
    target_pos = helper.pos_in_sat(helper.target_id(), SATURN_ID)

    frame, bore, bounds = helper.fbb()
    t = Transformer(frame, SATURN_FRAME, helper.time_et())

    spi = ShadowPlaneIntersect(target_pos, sun_vec, cassini_pos)
    corners = [spi(t(b)) for b in bounds]

    return max_mag(t(bore), np.asarray(corners))


def img_raw_size(helper: ImageHelper):
    frame, bore, bounds = helper.fbb()
    t = Transformer(frame, SATURN_FRAME, helper.time_et())
    bore = t(bore)

    target_pos = helper.pos_in_sat(helper.target_id(), CASSINI_ID)
    cnt = np.linalg.norm(target_pos) / np.linalg.norm(bore)
    corners = [t(b) * cnt for b in bounds]

    return max_mag(t(bore), np.asarray(corners))


def set_info(
        image: VicarImage,
        image_axis=None,
        analysis_axis=None,
        border: int = 0,
        **config
):
    try:
        load_kernels_for_image(image)

        helper = ImageHelper(image, **config)
        config = helper.config

        target, target_id = helper.target_full()
        time = helper.time_et()
        utc = helper.time_utc()
        frame = helper.frame()

        # https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/phaseq_c.html
        pa = spice.phaseq(time, target, SUN, CASSINI, ABCORR) * spice.dpr()

        title = "FROM: %s - %s @ %s %s \nPA=%.5f DEG" % (CASSINI, target, J2K, utc, pa)

        try:
            filters: List[str] = image.labels.properties['INSTRUMENT']['FILTER_NAME']
            title += "  Filters: " + ','.join(filters)
            exposure: float = image.labels.properties['INSTRUMENT']['EXPOSURE_DURATION']
            title += f" Exp: {exposure / 1000:.2f}s"
            number: str = helper.id()
            title += f"  Image n: {number}"
        except KeyError:
            log.warning("Failed to find filter data")

        h1 = helper.saturn_equator_offset(CASSINI_ID)
        h2 = helper.saturn_equator_offset(target_id)

        __sp, __spi = helper.shadow_angles()
        __sa = f'{__sp:.2f} deg'
        __sai = f'{__spi:.2f} deg'

        from ..tex import sci_5
        title += (
            "\n"
            fr"Offset from Ring Target: ${sci_5(h2)}\,km$ Cassini: ${sci_5(h1)}\,km$"
            "\n"
            f"Shadow-Ring angle: {__sa} Angle in image: {__sai}"
        )

        if image_axis is not None:
            try:
                # noinspection PyUnresolvedReferences
                from matplotlib.axes import Axes
                ax: Axes = image_axis

                try:
                    x_size: float
                    y_size: float
                    i_name: str
                    if helper.config[SIZE_FRAME] == 1:
                        i_name = 'Shadow'
                        x_size, y_size = img_sp_size(helper)
                    elif helper.config[SIZE_FRAME] == 2:
                        i_name = 'Target'
                        x_size, y_size = img_raw_size(helper)
                    else:
                        i_name = 'Ring'
                        x_size, y_size = img_rp_size(helper)

                    x_max = len(image.data[0][0])
                    y_max = len(image.data[0])

                    second_x = ax.secondary_xaxis(
                        location=1.07,
                        functions=(
                            lambda a: x_size / x_max * a,
                            lambda a: x_max / x_size * a
                        )
                    )
                    second_y = ax.secondary_yaxis(
                        location=1.07,
                        functions=(
                            lambda a: y_size / y_max * a,
                            lambda a: y_max / y_size * a
                        )
                    )

                    from matplotlib.ticker import AutoMinorLocator
                    second_y.yaxis.set_minor_locator(AutoMinorLocator())
                    second_x.xaxis.set_minor_locator(AutoMinorLocator())

                    from ...support.mpl import MPL_FONT_CONFIG
                    from ..tex import sci_2

                    second_y.set_ylabel(
                        f"At {i_name} intercept $(px = {sci_2(x_size / x_max)}, {sci_2(y_size / y_max)})$ KM",
                        **MPL_FONT_CONFIG
                    )

                    def mod_ax(axes: Axes, vertical: bool = False, **_):
                        ax2 = axes.secondary_xaxis(
                            location=-0.22,
                            functions=(
                                lambda a: y_size / y_max * a,
                                lambda a: y_max / y_size * a
                            ) if vertical else (
                                lambda a: x_size / x_max * a,
                                lambda a: x_max / x_size * a
                            )
                        )
                        ax2.xaxis.set_minor_locator(AutoMinorLocator())

                    analysis_axis.axes_modifier = mod_ax
                except Exception as e:
                    log.exception("Something happened", exc_info=e)

                if config[SUN_SATURN_VECTORS] or config[TARGET_ESTIMATE]:
                    t = Transformer(J2K, frame, time)

                    sun_pos = helper.pos(SUN_ID, helper.target_id())
                    saturn_pos = helper.pos(SATURN_ID, helper.target_id())

                    t_sun, t_saturn = t(sun_pos, saturn_pos)
                    t_sun = -norm(t_sun)
                    t_saturn = -norm(t_saturn)

                    if config[SUN_SATURN_VECTORS]:
                        x = 200
                        y = 200

                        sun_coord = np.vstack([x, y]).ravel() + t_sun[:2] * 1000
                        saturn_coord = np.vstack([x, y]).ravel() + t_saturn[:2] * 1000

                        ax.plot((x, sun_coord[0]), (y, sun_coord[1]), label="Sun", color="y")
                        ax.plot((x, saturn_coord[0]), (y, saturn_coord[1]), label="Saturn", color="r")

                    if config[TARGET_ESTIMATE]:
                        t_cassini = helper.pos_in_frame(target_id, CASSINI_ID)
                        frame_name, bore, boundaries = helper.fbb()

                        x_len = len(image.data[0])
                        y_len = len(image.data[0][0])

                        if border != 0:
                            x_len -= 2 * border
                            y_len -= 2 * border

                        x = -1 * np.arctan(t_cassini[0] / t_cassini[2]) * x_len / boundaries[0][0] + x_len / 2.
                        y = -1 * np.arctan(t_cassini[1] / t_cassini[2]) * y_len / boundaries[0][1] + y_len / 2.

                        log.debug(f"Estimate {x},{y}")

                        ax.scatter(x, y, s=16, c="g")
                        sun_coord = np.vstack([x, y]).ravel() + -t_sun[:2] * 1000
                        ax.plot((x, sun_coord[0]), (y, sun_coord[1]), color="g")

            except ImportError as e:
                log.exception("No matplotlib", exc_info=e)
            except Exception as e:
                log.exception("Something bad happened", exc_info=e)

        return title
    except Exception as e:
        log.exception("Failed to load data: %s", image.name, exc_info=e)
        return "Failed to load data"
    finally:
        release_kernels()


def plot_sphere(c, r, ax):
    g_1, g_2 = np.mgrid[0:2 * spice.pi():50j, 0:spice.pi():25j]
    x = np.cos(g_1) * np.sin(g_2) * r + c[0]
    y = np.sin(g_1) * np.sin(g_2) * r + c[1]
    z = np.cos(g_2) * r + c[2]
    ax.plot_wireframe(x, y, z)


def view_geometry(*_, image: VicarImage = None, **config):
    if image is not None:
        from PySide2.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QSizePolicy, QTextEdit
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
        from matplotlib.pyplot import Figure
        from mpl_toolkits.mplot3d import Axes3D

        d = QDialog()
        d.setWindowTitle("Image Geometry")
        layout = QHBoxLayout()

        sub = QVBoxLayout()

        fig = Figure()
        agg = FigureCanvasQTAgg(figure=fig)
        ax: Axes3D = fig.add_subplot(111, projection='3d')
        sub.addWidget(agg, stretch=1)
        tb = NavigationToolbar2QT(agg, d)
        sub.addWidget(tb)
        layout.addLayout(sub, stretch=1)

        try:
            load_kernels_for_image(image)
            helper = ImageHelper(image, **config)

            cas: np.ndarray
            target_pos: np.ndarray
            sun: np.ndarray

            # Positions in the IAU_SATURN frame
            cas = helper.pos_in_sat(CASSINI_ID, SATURN_ID)
            target_pos = helper.pos_in_sat(helper.target_id(), SATURN_ID)
            sun = helper.pos_in_sat(SUN_ID, helper.target_id())

            # Plotting wireframes is difficult
            xx, yy = np.mgrid[0:2 * spice.pi():24j, 0:0:24j]

            # Here we paint some pretty approximate rings
            def ring(r: float):
                ax.plot_wireframe(np.sin(xx) * r, np.cos(xx) * r, yy, color=(1.0, 0.0, 0.0, 1.0))

            ring(74.5)
            ring(92)
            ring(117.580)
            ring(122.2)
            ring(136.78)
            ring(140.220)

            # Calculating intercepts
            frm, bore, bounds = helper.fbb()
            t = Transformer(frm, SATURN_FRAME, helper.time_et())
            bore = t(bore)
            bore_intercept: np.ndarray
            bound_intersects: List[np.ndarray] = list()
            if helper.config[SIZE_FRAME] == 1:
                # Shadow
                spi = ShadowPlaneIntersect(target_pos, sun, cas)
                bore_intercept = spi(bore)
                bound_intersects = [np.column_stack((cas, spi(t(b)))) for b in bounds]
            elif helper.config[SIZE_FRAME] == 2:
                # Raw
                cnt = np.linalg.norm(helper.pos_in_sat(helper.target_id(), CASSINI_ID)) / np.linalg.norm(bore)
                bore_intercept = cas + bore * cnt
                for b in bounds:
                    tb = t(norm(b))
                    bound_intersects.append(np.column_stack((cas, cas + tb * cnt)))
            else:
                # Ring plane
                bore_intercept = bore * (-cas[2] / bore[2])
                for b in bounds:
                    tb = t(norm(b))
                    pv = cas + tb * (-cas[2] / tb[2])
                    bound_intersects.append(np.column_stack((cas, pv)))
                bore_intercept = cas + bore_intercept

            # some distances
            t_dist = np.linalg.norm(target_pos)
            tc_dist = np.linalg.norm(helper.pos(helper.target_id(), CASSINI_ID))
            c_dist = np.linalg.norm(cas)

            # scale
            sun, cas, target_pos, bore_intercept = (x / 1000 for x in [sun, cas, target_pos, bore_intercept])
            bound_intersects = np.asarray(bound_intersects) / 1000

            # pretty labels that we don't use because the legend doesn't render properly
            from ..tex import sci_5
            cassini_label = (
                "Cassini"
                "\n"fr"Dist Saturn: ${sci_5(c_dist)}\,km$, {helper.target_name()}: ${sci_5(tc_dist)}\,km$"
                "\n"fr"From plane: ${sci_5(helper.saturn_equator_offset(CASSINI_ID))}\,km$"
            )
            target_label = (
                f"{helper.target_name()}"
                "\n" fr"Dist Saturn: ${sci_5(t_dist)}$"
                "\n" fr"From plane: ${sci_5(helper.saturn_equator_offset(helper.target_id()))}\,km$"
            )

            # Plots
            ax.plot(*np.column_stack((cas, bore_intercept)), color='gray')
            for b in bound_intersects:
                ax.plot(*b, color='gray', linestyle='--')
            if len(bound_intersects) == 4:
                coord = [a[:, 1] for a in bound_intersects]
                from itertools import combinations
                for c, rc in combinations(coord, 2):
                    if c is not rc:
                        ax.plot(*np.column_stack((c, rc)), color='gray', linestyle='--')

            ax.scatter(0, 0, 0, c='r', s=16, label='Saturn')
            ax.scatter(cas[0], cas[1], cas[2], c='black', label=cassini_label)
            ax.plot([0, cas[0]], [0, cas[1]], [0, cas[2]], c='black')
            ax.plot([cas[0], cas[0]], [cas[1], cas[1]], [0, cas[2]], c='black')
            ax.scatter(target_pos[0], target_pos[1], target_pos[2], c='b', label=target_label)
            ax.plot([0, target_pos[0]], [0, target_pos[1]], [0, target_pos[2]], c='b')

            # Labels
            ax.set_xlabel(r"X ($10^3\,km$)")
            ax.set_ylabel(r"Y ($10^3\,km$)")
            ax.set_zlabel(r"Z ($10^3\,km$)")

            # What a bummer the quiver values seem to show the wrong direction so using this ad-hoc solution
            ax.autoscale(False)
            ax.plot(*np.column_stack((target_pos, sun)), color='y')

            if helper.config[CUBIC]:
                diff = 1.3 * np.max([np.linalg.norm(bore_intercept - b) for b in bound_intersects[:, :, 1]])
                i = 0
                for f in [ax.set_xlim3d, ax.set_ylim3d, ax.set_zlim3d]:
                    f((bore_intercept[i] - diff, bore_intercept[i] + diff))
                    i += 1

            img_id = helper.id()
            info = QTextEdit()

            info.setFixedWidth(250)
            layout.addWidget(info)

            def lr(left: str, right) -> str:
                # return f"{left}    __<div style='text-align: right;'>{right:.5e} km</div>__"
                if isinstance(right, float):
                    right = f'{right:.5e} km'
                return f"{left}    *{right}*"

            __sp, __spi = helper.shadow_angles()
            __sa = f'{__sp:.5f} deg'
            __sai = f'{__spi:.5f} deg'

            from textwrap import dedent
            info.setMarkdown(dedent(
                f"""
                # IMAGE: {img_id}
                
                ## Cassini:
                
                #### Distances:
                - {lr("Saturn:", c_dist)}
                - {lr(helper.target_name(), tc_dist)}
                
                #### Separation form ring plane:
                - {lr('h:', helper.saturn_equator_offset(CASSINI_ID))}
                
                ## {helper.target_name()}
                
                #### Distances:
                - {lr("Saturn:", t_dist)}
                
                #### Separation from ring plane:
                - {lr('h:', helper.saturn_equator_offset(helper.target_id()))}
                
                #### Shadow:
                - {lr('Offset in Z-direction:', __sa)}
                - {lr('Direction in image: ', __sai)}
                """
            ))
            info.setReadOnly(True)
        finally:
            release_kernels()

        d.setLayout(layout)
        d.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        d.setModal(True)

        agg.draw()
        d.exec_()


def view_labels(image: VicarImage = None, **_):
    if image:
        from PySide2.QtWidgets import QDialog, QTextEdit, QHBoxLayout, QVBoxLayout, QLabel
        from PySide2.QtCore import QSize
        from ...viewer.helper import CT

        dia = QDialog()

        helper = ImageHelper(image)

        dia.setWindowTitle(f"IMAGE: {helper.id()}")
        layout = QHBoxLayout()

        def boxed(title: str, text: str):
            sub = QVBoxLayout()
            t = QTextEdit()
            t.setMinimumWidth(250)
            t.setText(text)
            t.setReadOnly(True)
            sub.addWidget(QLabel(text=title), alignment=CT)
            sub.addWidget(t, stretch=1)
            layout.addLayout(sub, stretch=1)

        boxed("Labels", str(image.labels))

        if image.eol_labels is not None:
            boxed("EOL Labels", str(image.eol_labels))

        dia.setLayout(layout)
        dia.resize(QSize(480, 640))
        dia.exec_()
