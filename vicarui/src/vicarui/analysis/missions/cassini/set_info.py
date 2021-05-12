from vicarui.analysis import ImageWrapper

from .config import *
from .funcs import img_sp_size, img_raw_size, img_rp_size, norm
from .helpers import ImageHelper, Transformer
from ...kernels import load_kernels_for_image, release_kernels
from ...tex import sci_2


def set_info(
        image: ImageWrapper,
        image_axis=None,
        analysis_axis=None,
        **config
):
    raw = image.get_raw()
    try:
        load_kernels_for_image(raw)

        helper = ImageHelper(raw, **config)
        config = helper.config

        target, target_id = helper.target_full
        time = helper.time_et
        utc = helper.time_utc()

        # https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/phaseq_c.html
        pa = spice.phaseq(time, target, SUN, CASSINI, ABCORR) * spice.dpr()

        title = "%s FROM: %s - %s @ UTC %s \nPA=%.2f DEG" % (helper.id, CASSINI, target, utc, pa)

        try:
            filters: List[str] = helper['INSTRUMENT']['FILTER_NAME']
            title += "  Filters: " + ','.join(filters)
            exposure: float = helper['INSTRUMENT']['EXPOSURE_DURATION']
            title += f" Exp: {exposure / 1000:.2f}s"
            number: str = helper.id
            title += f"  Image n: {number}"
            h1 = helper.saturn_equator_offset(CASSINI_ID)
            h2 = helper.saturn_equator_offset(target_id)

            __sp, __spi = helper.shadow_angles
            __sa = f'{__sp:.2f} deg'
            __sai = f'{__spi:.2f} deg'

            title += (
                "\n"
                fr"Target from Ring Plane: ${sci_2(h2):}\,km$ Cassini from Ring Plane: ${sci_2(h1)}\,km$"
                "\n"
                f"Shadow-Ring angle: {__sa} Angle in image: {__sai}"
            )
        except Exception as e:
            log.warning("Failed to find some data", exc_info=e)

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

                    x_max = len(raw.data[0][0])
                    y_max = len(raw.data[0])

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

                    from ....support.mpl import MPL_FONT_CONFIG
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
                    t = Transformer(J2K, helper.frame, time)
                    sun_pos = helper.pos(SUN_ID, helper.target_id())
                    if helper.target_id() == SATURN_ID:
                        it = -t
                        t_cas = helper.pos_in_sat(CASSINI_ID, SATURN_ID)
                        t_bore = it(helper.fbb[1])
                        saturn_pos = -(t_cas + t_bore * -t_cas[2] / t_bore[2])
                    else:
                        saturn_pos = helper.pos(SATURN_ID, helper.target_id())
                    t_sun, t_saturn = (-norm(v)[0:2] for v in t(sun_pos, saturn_pos))

                    if config[SUN_SATURN_VECTORS]:
                        x = 70
                        y = 70

                        sun = np.column_stack(
                            (
                                [x, y],
                                [
                                    x + t_sun[0] * 60 / np.linalg.norm(t_sun),
                                    y + t_sun[1] * 60 / np.linalg.norm(t_sun)
                                ]
                            )
                        )

                        sat = np.column_stack(
                            (
                                [x, y],
                                [
                                    x + t_saturn[0] * 60 / np.linalg.norm(t_saturn),
                                    y + t_saturn[1] * 60 / np.linalg.norm(t_saturn)
                                ]
                            )
                        )

                        ax.plot(*sun, label="Sun", color="y", linewidth=1)
                        ax.plot(*sat, label="Saturn", color="r", linewidth=1)

                    if config[TARGET_ESTIMATE]:
                        t_pos = helper.pos_in_frame(target_id, CASSINI_ID)
                        frame_name, bore, boundaries = helper.fbb

                        x_len = len(raw.data[0])
                        y_len = len(raw.data[0][0])

                        x = x_len / 2.
                        y = y_len / 2.

                        b = boundaries[np.argmin([np.linalg.norm(b) for b in boundaries])]
                        x += np.arctan(t_pos[0] / t_pos[2]) / np.arctan(b[0] / b[2]) * x_len / 2. * np.sign(t_pos[0])
                        y += np.arctan(t_pos[1] / t_pos[2]) / np.arctan(b[1] / b[2]) * y_len / 2. * np.sign(t_pos[1])

                        if image.invalid_indices is not None:
                            for i in image.invalid_indices[::-1]:
                                if i <= y:
                                    y -= 1

                        if image.border != 0:
                            x -= image.border
                            y -= image.border

                        log.debug(f"Estimate {x},{y}")
                        ax.scatter(x, y, s=16, c="g", alpha=0.65)
            except ImportError as e:
                log.exception("No matplotlib", exc_info=e)
            except Exception as e:
                log.exception("Something bad happened", exc_info=e)

        return title
    except Exception as e:
        log.exception("Failed to load data: %s", raw.name, exc_info=e)
        return "Failed to load data"
    finally:
        release_kernels()


__all__ = ['set_info']
