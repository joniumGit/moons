import cProfile as profile
import sys
from argparse import ArgumentParser, Namespace
from pstats import Stats, SortKey
from typing import Optional

import matplotlib
from PySide2 import QtWidgets as qt

from .support import info, debug, invoke_safe
from .viewer import AppWindow

pr: Optional[profile.Profile] = None


@invoke_safe
def get_parser(parent=None) -> Optional[ArgumentParser]:
    parser: ArgumentParser
    if parent:
        parser = parent.add_parser(
            "viewer",
            help="Viewer and analyzer for Vicar image files",
            description="Viewer and analyzer for Vicar image files"

        )
    else:
        parser = ArgumentParser(prog='viewer', description="Moons - Vicar Image Processing And Analysis")
    parser.add_argument(
        '--verbose',
        help='Increase output verbosity',
        action='store_true'
    )
    parser.add_argument(
        "--kernel-path",
        metavar="PATH",
        dest="kernels",
        nargs=1,
        help="Kernel base path",
        type=str
    )
    parser.add_argument(
        "--mission",
        metavar="MISSION",
        dest="mission",
        nargs=1,
        help="Mission to analyze. "
             "I.E. Which mission to call set_info for (default: cassini). "
             "Imports from vicarui.analysis.missions",
        type=str,
        required=False
    )
    return parser


def init(ns: Namespace = None) -> None:
    args: Namespace
    if ns:
        args = ns
    else:
        parser = get_parser()
        if parser is not None:
            args, _ = parser.parse_known_args()
        else:
            return
    if args.verbose:
        global pr
        pr = profile.Profile(builtins=False)
        pr.enable()
    if args.kernels is not None:
        from . import analysis as anal
        info("Setting kernel path to: " + args.kernels.__repr__())
        anal.provide_kernels(args.kernels[0])
    if args.mission is not None:
        from . import analysis as anal
        info(f"Mission: {args.mission[0]}")
        anal.SELECTED = args.mission[0].strip()

    debug("Setting Matplotlib backend")
    matplotlib.use("Qt5Agg")


def run(no_init: bool = False):
    if not no_init:
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
