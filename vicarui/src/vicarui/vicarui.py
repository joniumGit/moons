import argparse


def new_ui_entry(ns: argparse.Namespace):
    from .app import run, init
    init(ns=ns)
    run(no_init=True)


def old_ui_entry(_: argparse.Namespace):
    from .viewer_old import ui
    ui.run()


def main():
    args = argparse.ArgumentParser(description="Moons - Vicar Image Processing And Analysis")
    subs = args.add_subparsers(title="Graphical utilities")

    from . import app
    p: argparse.ArgumentParser = app.get_parser(parent=subs)
    p.set_defaults(func=new_ui_entry)

    old_ui = subs.add_parser(
        "alt-viewer",
        help="Older alternative viewer",
        description="Older alternative viewer"
    )
    old_ui.set_defaults(func=old_ui_entry)

    ns, _ = args.parse_known_args()
    if hasattr(ns, 'func'):
        ns.func(ns)
    else:
        args.print_help()
