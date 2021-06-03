"""
Finds and categorizes all calibrated images by the filter used into subdirectories

Args:
- Base path: Search start and subdirectory target
"""
if __name__ == '__main__':
    import sys
    from os import walk
    from pathlib import Path
    from typing import List, Dict

    from vicarutil.image import read_beg_labels

    base: Path = Path(sys.argv[1])

    CL1 = "CL1"
    CL2 = "CL2"

    clear: List[Path] = list()
    values: Dict[str, List[Path]] = dict()

    for d, _, files in walk(base, followlinks=False):
        p = Path(d)
        for f in files:
            if f.endswith("CALIB.IMG"):
                try:
                    fp = p.joinpath(f)
                    with open(fp, 'rb') as io:
                        labels = read_beg_labels(io)
                        filters: List[str] = [label.strip() for label in labels['INSTRUMENT']['FILTER_NAME']]
                        actual: str = "NA"
                        if CL1 in filters and CL2 in filters:
                            clear.append(fp)
                        else:
                            for filt in filters:
                                if filt != CL1 and filt != CL2:
                                    actual = filt
                                    break
                            if actual not in values:
                                values[actual] = [fp]
                            else:
                                values[actual].append(fp)
                except Exception as e:
                    print(e)

    clear_path = base.joinpath("CLEAR")
    clear_path.mkdir(exist_ok=True)
    for p in clear:
        np = Path(str(clear_path) + "/" + p.name)
        p.rename(np)
    for k, v in values.items():
        current_path = base.joinpath(k)
        current_path.mkdir(exist_ok=True)
        current_path = str(current_path)
        for p in v:
            np = Path(current_path + "/" + p.name)
            try:
                p.rename(np)
            except FileNotFoundError as e:
                print(e)
