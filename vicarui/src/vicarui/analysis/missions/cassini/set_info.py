from .config import *
from .funcs import img_sp_size, img_raw_size, img_rp_size, norm
from .helpers import ImageHelper, Transformer
from ...kernels import load_kernels_for_image, release_kernels
from ...tex import sci_2


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

        target, target_id = helper.target_full
        time = helper.time_et
        utc = helper.time_utc()
        frame = helper.frame

        # https://naif.jpl.nasa.gov/pub/naif/toolkit_docs/C/cspice/phaseq_c.html
        pa = spice.phaseq(time, target, SUN, CASSINI, ABCORR) * spice.dpr()

        title = "FROM: %s - %s @ UTC %s \nPA=%.2f DEG" % (CASSINI, target, utc, pa)

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
                        frame_name, bore, boundaries = helper.fbb

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


__all__ = ['set_info']
