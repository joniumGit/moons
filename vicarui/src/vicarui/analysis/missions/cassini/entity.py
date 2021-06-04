from .config import *
from .funcs import rs, scale_to_rs, get_camera_intersects
from .helpers import ImageHelper


class PlotPacket:
    from mpl_toolkits.mplot3d import Axes3D
    ax: Axes3D
    rings: np.ndarray

    def __init__(self, helper: ImageHelper, ax: Axes3D):
        self.helper = helper
        self.ax = ax
        self.rings = np.asarray([74.5e3, 92e3, 117.580e3, 122.2e3, 136.78e3, 140.220e3])

    def _plot_sphere(self, c: np.ndarray, r: float, color: str):
        """
        Cool sphere plotter
        """
        from matplotlib.colors import to_rgba
        g_1, g_2 = np.mgrid[0:2 * spice.pi():50j, 0:spice.pi():25j]
        x = np.cos(g_1) * np.sin(g_2) * r + c[0]
        y = np.sin(g_1) * np.sin(g_2) * r + c[1]
        z = np.cos(g_2) * r + c[2]
        self.ax.plot_wireframe(
            x,
            y,
            z,
            alpha=WF_ALPHA,
            linewidth=0.5,
            colors=to_rgba(color, WF_ALPHA),
            zorder=1000
        )

    def _plot_rings(self):
        # Plotting wireframes is difficult
        xx, yy = np.mgrid[0:2 * spice.pi():100j, 0:0:100j]
        for r in self.rings:
            from matplotlib.colors import to_rgba
            color = SATURN_COLOR
            self.ax.plot_wireframe(
                np.sin(xx) * r / rs(),
                np.cos(xx) * r / rs(),
                yy,
                alpha=WF_ALPHA,
                linewidth=0.5,
                colors=to_rgba(color, WF_ALPHA),
                zorder=1000
            )

    def plot_target(self):
        t_pos = scale_to_rs(-self.helper.trps(SATURN_ID))
        t_r = np.average(scale_to_rs(spice.bodvcd(self.helper.target_id, 'RADII', 3)[1]))
        self._plot_sphere(t_pos, t_r, TARGET_COLOR)

    def plot_saturn(self):
        self._plot_rings()
        self._plot_sphere(np.zeros(3), 1, SATURN_COLOR)

    def plot_sun(self):
        sat = scale_to_rs(self.helper.trps(SATURN_ID))
        sp = scale_to_rs(self.helper.trps(SUN_ID))
        tp = -sat
        self.ax.plot(*np.column_stack((tp, tp + sp * 1 / np.linalg.norm(sp))), color=SUN_COLOR)
        self.ax.plot(*np.column_stack((tp, tp - sp * 1 / np.linalg.norm(sp))), color=TARGET_COLOR)
        if np.linalg.norm(sat) <= 1:
            self.ax.plot(*np.column_stack((tp, (0, 0, 0))), color=SATURN_COLOR)
        else:
            self.ax.plot(*np.column_stack((tp, tp + sat * 1 / np.linalg.norm(sat))), color=SATURN_COLOR)

    def plot_camera(self, closeup: bool = True, rings: bool = False):
        bore, bounds, up = get_camera_intersects(self.helper)
        cas = scale_to_rs(-self.helper.crps(SATURN_ID))
        target = scale_to_rs(-self.helper.trps(SATURN_ID))
        self.ax.scatter(cas[0], cas[1], cas[2], c=CASSINI_COLOR, zorder=10)
        self.ax.plot([cas[0], cas[0]], [cas[1], cas[1]], [0, cas[2]], c=CASSINI_COLOR, zorder=10)
        self.ax.plot(*np.column_stack((cas, bore)), color=CAMERA_COLOR, zorder=100)

        if rings:
            up[2] = 0
        self.ax.plot(*np.column_stack((bore, bore + up)), color=CAMERA_COLOR, zorder=100)

        for b in bounds:
            self.ax.plot(*b, color=CAMERA_COLOR, linestyle='--', zorder=100, alpha=0.65)
        if len(bounds) == 4:
            coord = [a[:, 1] for a in bounds]
            from itertools import combinations
            for c, rc in combinations(coord, 2):
                if c is not rc:
                    self.ax.plot(*np.column_stack((c, rc)), color=CAMERA_COLOR, linestyle='--', zorder=100)
        self.ax.set_box_aspect((1, 1, 1))
        if closeup:
            diff = 1.2 * np.max([np.linalg.norm(bore - b) for b in bounds[:, :, 1]])
            i = 0
            for f in [self.ax.set_xlim3d, self.ax.set_ylim3d, self.ax.set_zlim3d]:
                f((bore[i] - diff, bore[i] + diff))
                i += 1
        else:
            max_lim = np.amax([self.ax.get_xlim3d(), self.ax.get_ylim3d(), self.ax.get_zlim3d()], axis=0)
            diff = max_lim[1] - max_lim[0]
            i = 0
            for f in [self.ax.set_xlim3d, self.ax.set_ylim3d, self.ax.set_zlim3d]:
                f((target[i] - diff, target[i] + diff))
                i += 1

    def label(self):
        self.ax.set_xlabel(r"X ($R_s$)")
        self.ax.set_ylabel(r"Y ($R_s$)")
        self.ax.set_zlabel(r"Z ($R_s$)")
