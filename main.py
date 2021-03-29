import os
import sys
from typing import Dict, Optional, cast

import matplotlib.pyplot as plt
import spiceypy as spice
import statsmodels.api as sm
from astropy.visualization import *
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from skimage.exposure import exposure
from sklearn.preprocessing import PolynomialFeatures, normalize

from vicarutil import image as vcr

BODY = 'ENCELADUS'
CASSINI = 'CASSINI'
SATURN = 'SATURN'
SUN = 'SUN'


def print_ver():
    """
    Prints the TOOLKIT version
    """
    print(spice.tkvrsn('TOOLKIT'))


bp = sys.argv[1]
META_KERNEL = bp + '/kernels/mk/commons.tm'
TEST_KERNEL = bp + "/kernels/mk/"

if __name__ == '__main__':
    plt.switch_backend("TkAgg")
    # Version
    print("_____SPICE_____")
    print_ver()

    # Testing kernel loading
    try:
        print("\n\nReading image")
        _img_path: str = bp + '/test_image/N1533960372_1_CALIB.IMG'
        img: np.ndarray
        kv: Dict
        data: vcr.VicarImage
        labels: vcr.Labels

        data = vcr.read_image(_img_path)

        print("\n\n--IMAGE DATA--")
        labels = data.labels
        print(labels)
        print(labels.properties)
        print(labels.tasks)

        print("\n\nLoading kernels")
        spice.furnsh(META_KERNEL)
        print("Loaded: " + META_KERNEL)
        year = labels.property('IDENTIFICATION')['IMAGE_TIME'][0:4]
        for f in os.listdir(bp + "/kernels/mk"):
            if year in f:
                TEST_KERNEL += f
                spice.furnsh(TEST_KERNEL)
                print("Loaded: " + TEST_KERNEL)

        print("\n\nLoading body ids")
        # Get all body ids
        body_id: int = spice.bodn2c(BODY)
        cassini_id: int = spice.bodn2c(CASSINI)
        saturn_id: int = spice.bodn2c(SATURN)
        sun_id: int = spice.bodn2c(SUN)
        print("Body ids: " + [body_id, cassini_id, saturn_id, sun_id].__str__())

        J2K = 'J2000'
        ABCORR = 'NONE'
        utc = labels.property('IDENTIFICATION')['IMAGE_MID_TIME']
        time = spice.utc2et(utc.strip()[:-1])

        # positions
        cassini_pos: np.ndarray
        sun_pos: np.ndarray
        saturn_pos: np.ndarray

        # something
        lt_corr: float
        print("\n\nPosition vectors from %s:" % BODY)
        cassini_pos, lt_corr = spice.spkezp(cassini_id, time, J2K, ABCORR, body_id)
        print("Cassini pos: " + cassini_pos.__str__() + " with lt_corr: %f" % lt_corr)
        sun_pos, lt_corr = spice.spkezp(sun_id, time, J2K, ABCORR, body_id)
        print("Sun pos: " + sun_pos.__str__() + " with lt_corr: %f" % lt_corr)
        saturn_pos, lt_corr = spice.spkezp(saturn_id, time, J2K, ABCORR, body_id)
        print("Saturn pos: " + saturn_pos.__str__() + " with lt_corr: %f" % lt_corr)

        print("\n\nCalculating phase angle")
        pa = np.arccos(
            np.linalg.multi_dot((cassini_pos, sun_pos))
            / np.linalg.norm(cassini_pos)
            / np.linalg.norm(sun_pos)
        ) * 180 / np.pi
        print("Phase angle: " + str(pa))

        print("\n\nMaking position magic")
        INSTRUMENT = 'cassini_iss_nac'
        instrument_id: int = spice.bodn2c(INSTRUMENT)
        room = 10
        # hope defaults are ok
        shape, frame_name, bore, n_vec, boundaries = spice.getfov(instrument_id, room)
        print("FOV data:")
        print("    -" + shape)
        print("    -" + frame_name)
        print("    -" + bore.__str__())
        print("    -%d" % n_vec)
        print("Boundaries: ")
        print(boundaries)
        print()

        t_form = spice.pxform(J2K, frame_name, time)
        print("Translation matrix: ")
        print(t_form)
        print()

        t_sun: np.ndarray = spice.mxv(t_form, sun_pos)
        t_saturn: np.ndarray = spice.mxv(t_form, saturn_pos)
        t_sun = -t_sun / np.linalg.norm(t_sun)
        t_saturn = -t_saturn / np.linalg.norm(t_saturn)
        print("Translated vectors: ")
        print("    Sun: " + t_sun.__str__())
        print("    Saturn: " + t_saturn.__str__())

        print("\n\nPlotting")

        print("\n\nPlotting")
        img: np.ndarray = data.data[0][1:-1, 1:-1]
        img = img.astype("float64")
        pimg: np.ndarray = img.copy()

        arr: np.ndarray = np.arange(0, len(img), 1)

        noproc = 1
        if noproc:
            pf = PolynomialFeatures(3).fit_transform(arr.copy().reshape(-1, 1))
            params: Optional[np.ndarray] = None
            for idx, i in enumerate(pimg):
                res = sm.OLS(i, pf).fit()
                if params is not None:
                    params = (params + res.params) / 2
                else:
                    params = res.params
            for idx, i in enumerate(pimg):
                corr = -1 * np.polyval(params[::-1], arr)
                corr = corr - np.min(corr)
                pimg[idx] += corr
            pimg = pimg.transpose().copy()
            params: Optional[np.ndarray] = None
            for idx, i in enumerate(pimg):
                res = sm.OLS(i, pf).fit()
                if params is not None:
                    params = (params + res.params) / 2
                else:
                    params = res.params
            for idx, i in enumerate(pimg):
                corr = -1 * np.polyval(params[::-1], arr)
                corr = corr - np.min(corr)
                pimg[idx] += corr
            pimg = pimg.transpose().copy()
        pimg = normalize(pimg)
        # pimg = exposure.equalize_hist(pimg, nbins=1000)
        pl, ph = np.percentile(pimg, (4, 96))
        pimg = cast(np.ndarray, exposure.rescale_intensity(pimg, in_range=(pl, ph)))
        img = pimg

        for i in np.arange(490, 550, 1):
            x = arr[360:561]
            y = pimg[360:561, i:i + 1]
            pf = PolynomialFeatures(2).fit_transform(x.copy().reshape(-1, 1))
            res = sm.WLS(y, pf).fit()
            plt.scatter(x, y, s=4, c="b")
            plt.plot(x, np.polyval(res.params[::-1], x))
        plt.show()

        fig: Figure = plt.figure()

        X, Y = np.meshgrid(np.arange(0, 1022, 1), np.arange(0, 1022, 1))
        ax: Axes3D = fig.add_subplot(132, projection='3d')
        ax.plot_surface(X, Y, img)
        ax.invert_yaxis()
        ax1: Axes3D = fig.add_subplot(131, projection='3d')
        X, Y = np.meshgrid(np.arange(0, 1024, 1), np.arange(0, 1024, 1))
        ax1.plot_surface(X, Y, data.data[0])
        ax1.invert_yaxis()

        ax2 = fig.add_subplot(133)
        ax2.set_title("Background Subtracted")
        ax2.imshow(img, norm=ImageNormalize(interval=ZScaleInterval(), stretch=HistEqStretch(pimg)), cmap="gray")
        ax2.invert_yaxis()
        plt.tight_layout()
        plt.show()


        plt.imshow(img, cmap="gray")
        x = 630
        y = 550
        sun_coord = np.vstack([x, y]).ravel() + t_sun[:2] * 200
        saturn_coord = np.vstack([x, y]).ravel() + t_saturn[:2] * 200

        print(np.vstack([x, y]).ravel() + t_sun[:2] * 100)
        plt.plot((x, sun_coord[0]), (y, sun_coord[1]), label="Sun", color="r")
        plt.plot((x, saturn_coord[0]), (y, saturn_coord[1]), label="Saturn", color="y")
        plt.title("%s @ %s %s \nPA=%.5f DEG" % (BODY, J2K, utc, pa))
        plt.gca().invert_yaxis()
        plt.legend()
        plt.show()

    except Exception as e:
        print("Something failed")
        raise e
    finally:
        print("Unloading kernels")
        try:
            spice.unload(TEST_KERNEL)
        except Exception as e:
            print("Failed to unload %s" + TEST_KERNEL)
            raise e
        try:
            spice.unload(META_KERNEL)
        except Exception as e:
            print("Failed to unload %s" + META_KERNEL)
            raise e
        print("_____BYE_____")
