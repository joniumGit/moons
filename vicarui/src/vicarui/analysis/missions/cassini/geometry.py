from .config import *
from .helpers import ImageHelper
from ...kernels import load_kernels_for_image, release_kernels


def view_geometry(*_, image: ImageWrapper = None, **config):
    """
    Geometry viewer
    """
    if image is not None:
        image: VicarImage = image.get_raw()
        from PySide2.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QSizePolicy, QTextEdit
        from PySide2.QtCore import Qt
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
        from matplotlib.pyplot import Figure
        from mpl_toolkits.mplot3d import Axes3D
        from .entity import PlotPacket

        d = QDialog()
        d.setWindowState(Qt.WindowMaximized)
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

            pp = PlotPacket(helper, ax)
            pp.plot_saturn()
            pp.plot_target()
            pp.plot_sun()
            pp.plot_camera()
            pp.label()

            sat_cas_dist = np.linalg.norm(helper.pos_in_sat(SATURN_ID, CASSINI_ID))
            target_cas_dist = np.linalg.norm(helper.pos_in_sat(helper.target_id(), CASSINI_ID))
            sat_target_dist = np.linalg.norm(helper.pos_in_sat(SATURN_ID, helper.target_id()))

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

            sun_to_rings, shadow_in_image, shadow_to_bore = helper.shadow_angles

            ang_xy = f'{sun_to_rings:.5f} deg'
            ang_img = f'{shadow_in_image:.5f} deg'
            ang_bore = f'{shadow_to_bore:.5f} deg'

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
                - {lr('Angle to XY-plane:', ang_xy)}
                - {lr('Direction in image:', ang_img)}
                - {lr('Angle to Bore vector:', ang_bore)}
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
