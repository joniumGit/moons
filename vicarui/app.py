import cProfile as profile
import sys
from argparse import ArgumentParser
from pstats import Stats, SortKey
from typing import Optional

import matplotlib
from PySide2 import QtWidgets as qt

from vicarui.core.logging import info, debug
from vicarui.core.logging import invoke_safe
from vicarui.core.widget import AppWindow

pr: Optional[profile.Profile] = None


@invoke_safe
def get_parser() -> Optional[ArgumentParser]:
    parser = ArgumentParser(description="Moons - Vicar Image Processing And Analysis")
    parser.add_argument(
        '--verbose',
        help='Increase output verbosity',
        action='store_true'
    )
    return parser


def init() -> None:
    parser = get_parser()
    if parser is not None:
        args = parser.parse_args()
        if args.verbose:
            global pr
            pr = profile.Profile(builtins=False)
            pr.enable()
    debug("Setting Matplotlib backend")
    matplotlib.use("Qt5Agg")


def run():
    init()
    info("Starting application")
    app = qt.QApplication(sys.argv)
    apw = AppWindow()
    info("Setup done, starting...")
    apw.show()
    code: int = 1
    try:
        code = app.exec_()
    finally:
        global pr
        if pr is not None:
            debug("Incoming performance data...")
            res = Stats(pr).strip_dirs()
            res.sort_stats(SortKey.CUMULATIVE).print_stats(10)
            res.sort_stats(SortKey.TIME).print_stats(10)
            debug("Finished!")
        info("See you again!")
        sys.exit(code)


if __name__ == '__main__':
    run()
