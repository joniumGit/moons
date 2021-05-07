from .config import *
from .funcs import rs, get_camera_intersects, scale_to_rs
from .helpers import ImageHelper
from ...kernels import load_kernels_for_image, release_kernels


def plot_sphere(c: Tuple[int, int, int], r: float, ax, color: str):
    """
    Cool sphere plotter
    """
    from mpl_toolkits.mplot3d import Axes3D
    from typing import cast
    from matplotlib.colors import to_rgba

    ax = cast(Axes3D, ax)
    g_1, g_2 = np.mgrid[0:2 * spice.pi():50j, 0:spice.pi():25j]
    x = np.cos(g_1) * np.sin(g_2) * r + c[0]
    y = np.sin(g_1) * np.sin(g_2) * r + c[1]
    z = np.cos(g_2) * r + c[2]

    ax.plot_wireframe(
        x,
        y,
        z,
        alpha=WF_ALPHA,
        linewidth=0.5,
        colors=to_rgba(color, WF_ALPHA),
        zorder=1000
    )


def plot_rings(rings: Iterable[float], ax):
    # Plotting wireframes is difficult
    xx, yy = np.mgrid[0:2 * spice.pi():100j, 0:0:100j]
    for r in rings:
        from matplotlib.colors import to_rgba
        color = SATURN_COLOR
        ax.plot_wireframe(
            np.sin(xx) * r / rs(),
            np.cos(xx) * r / rs(),
            yy,
            alpha=WF_ALPHA,
            linewidth=0.5,
            colors=to_rgba(color, WF_ALPHA),
            zorder=1000
        )


def view_geometry(*_, image: VicarImage = None, **config):
    """
    Geometry viewer
    """
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

            # rings
            plot_rings([74.5e3, 92e3, 117.580e3, 122.2e3, 136.78e3, 140.220e3], ax)

            # some distances
            sat_target_dist = np.linalg.norm(target_pos)
            target_cas_dist = np.linalg.norm(helper.pos(helper.target_id(), CASSINI_ID))
            sat_cas_dist = np.linalg.norm(cas)

            fg = 0
            bg = 10
            mid = 5

            # scale
            sun, cas, target_pos = (scale_to_rs(x) for x in [sun, cas, target_pos])

            # Camera
            bore, bounds = get_camera_intersects(helper)

            # Plots
            ax.plot(*np.column_stack((cas, bore)), color=CAMERA_COLOR, zorder=mid)
            for b in bounds:
                ax.plot(*b, color=CAMERA_COLOR, linestyle='--', zorder=bg, alpha=0.65)
            if len(bounds) == 4:
                coord = [a[:, 1] for a in bounds]
                from itertools import combinations
                for c, rc in combinations(coord, 2):
                    if c is not rc:
                        ax.plot(*np.column_stack((c, rc)), color=CAMERA_COLOR, linestyle='--', zorder=fg)

            # ax.scatter(0, 0, 0, c=SATURN_COLOR, s=16)

            # Saturn
            plot_sphere((0, 0, 0), 1, ax, SATURN_COLOR)

            # cassini
            ax.scatter(cas[0], cas[1], cas[2], c=CASSINI_COLOR, zorder=fg)
            ax.plot([cas[0], cas[0]], [cas[1], cas[1]], [0, cas[2]], c=CASSINI_COLOR, zorder=mid)

            # Target
            plot_sphere(
                (target_pos[0], target_pos[1], target_pos[2]),
                np.average(scale_to_rs(spice.bodvcd(helper.target_id(), 'RADII', 3)[1])),
                ax,
                TARGET_COLOR
            )
            # ax.scatter(target_pos[0], target_pos[1], target_pos[2], c=TARGET_COLOR, zorder=fg)
            ax.plot([0, target_pos[0]], [0, target_pos[1]], [0, target_pos[2]], c=SATURN_COLOR, zorder=mid)

            # Labels
            ax.set_xlabel(r"X ($R_s$)")
            ax.set_ylabel(r"Y ($R_s$)")
            ax.set_zlabel(r"Z ($R_s$)")

            # What a bummer the quiver values seem to show the wrong direction so using this ad-hoc solution
            ax.autoscale(False)
            ss = scale_to_rs(sun)
            sss = ss * 1 / np.linalg.norm(ss)
            ax.plot(*np.column_stack((target_pos, sss)), color=SUN_COLOR, zorder=fg)

            # Take us to a cubic view
            if helper.config[CUBIC]:
                diff = 1.2 * np.max([np.linalg.norm(bore - b) for b in bounds[:, :, 1]])
                i = 0
                for f in [ax.set_xlim3d, ax.set_ylim3d, ax.set_zlim3d]:
                    f((bore[i] - diff, bore[i] + diff))
                    i += 1

            img_id = helper.id
            info = QTextEdit()

            info.setFixedWidth(250)
            layout.addWidget(info)

            def lr(left: str, right) -> str:
                # Sad
                # return f"{left}    __<div style='text-align: right;'>{right:.5e} km</div>__"
                if isinstance(right, float):
                    right = f'{right:.5e} km'
                return f"{left}    *{right}*"

            __sp, __spi = helper.shadow_angles
            __sa = f'{__sp:.5f} deg'
            __sai = f'{__spi:.5f} deg'

            from textwrap import dedent
            info.setMarkdown(dedent(
                f"""
                # IMAGE: {img_id}

                ## Cassini:

                #### Distances:
                - {lr("Saturn:", sat_cas_dist)}
                - {lr(helper.target_name(), target_cas_dist)}

                #### Separation form ring plane:
                - {lr('h:', helper.saturn_equator_offset(CASSINI_ID))}

                ## {helper.target_name()}

                #### Distances:
                - {lr("Saturn:", sat_target_dist)}

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


__all__ = ['view_geometry']
