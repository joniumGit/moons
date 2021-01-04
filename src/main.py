from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import spiceypy as spice
from astropy.visualization import simple_norm

from vicar_utils import vicar_reader as vcr
from vicar_utils.vicar_reader import VicarData

BODY = 'ENCELADUS'
CASSINI = 'CASSINI'
SATURN = 'SATURN'
SUN = 'SUN'


def print_ver():
    """
    Prints the TOOLKIT version
    """
    print(spice.tkvrsn('TOOLKIT'))


META_KERNEL = 'kernels/mk/commons.tm'
TEST_KERNEL = 'kernels/mk/cas_2006_v26.tm'

if __name__ == '__main__':
    # Version
    print("_____SPICE_____")
    print_ver()

    # Testing kernel loading
    try:
        print("\n\nReading image")
        _img_path: str = '../test_image/N1533960372_1_CALIB.IMG'
        img: np.ndarray
        kv: Dict
        data: VicarData

        with open(_img_path, mode="rb") as f:
            data = vcr.read_image(f)

        print("\n\n--IMAGE DATA--")
        print(data.labels)
        print(data.properties)
        print(data.tasks)

        print("\n\nLoading kernels")
        spice.furnsh(META_KERNEL)
        print("Loaded: " + META_KERNEL)
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
        utc = data.properties['IDENTIFICATION']['IMAGE_MID_TIME']
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
        img: np.ndarray = data.data[0]
        plt.imshow(img, norm=simple_norm(img, 'sqrt'), cmap="gray")
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
