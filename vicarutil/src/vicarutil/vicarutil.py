import argparse


def reader(ns: argparse.Namespace):
    import textwrap
    from vicarutil.image import read_image

    def read(f: str):
        if f:
            f = f.strip()
            image = read_image(f)
            print(image.labels)
            if image.eol_labels:
                print(image.eol_labels)
            return True
        return False

    if ns.file:
        try:
            read(ns.file)
        except FileNotFoundError:
            import sys
            sys.exit(f"File not found: {ns.file}")
    else:
        print("Vicar Label Reader")
        print(
            textwrap.dedent(
                """
                Reads labels from Vicar files ang prints their contents in JSON

                Usage:
                    - Input filenames (paths)
                    - Input 'exit' or 'quit' or empty to quit
                """
            )
        )
        while True:
            file = input("Give file path: ")
            if not file:
                print("Exiting...")
                break
            file = file.strip()
            if file == 'exit' or file == 'quit':
                print("Exiting...")
                break
            print(file)
            if not read(file):
                break


def main():
    args = argparse.ArgumentParser()
    subs = args.add_subparsers(title="Command line utilities")
    lbl = subs.add_parser(
        "label-reader",
        help="VLR - Command line reader for labels embedded in Vicar files.",
        description="Reads labels from Vicar files ang prints their contents in JSON"
    )
    lbl.add_argument(
        "-f",
        metavar="FILE",
        action='store',
        dest='file',
        required=False,
        default=None,
        help="file to read and exit"
    )
    lbl.set_defaults(func=reader)
    ns, _ = args.parse_known_args()
    if hasattr(ns, 'func'):
        ns.func(ns)
    else:
        args.print_help()
