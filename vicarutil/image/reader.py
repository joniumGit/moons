"""
The one and only function to read a Vicar image file
"""
from pathlib import Path
from typing import Union, Optional

from .core.entity import VicarImage, BinaryPrefix
from .core.image import constraint_from_labels, read_image_internal, read_binary_prefix
from .core.label_processor import read_beg_labels, has_eol, read_eol_labels, read_binary_header
from .definitions.definitions import SystemLabel


def read_image(path: Union[str, Path]) -> VicarImage:
    """
    Reads all image and label data from a Vicar file
    :param path: File to read
    :return: VicarData object
    """
    with open(path, "rb") as f:
        beg_lbl = read_beg_labels(f)
        end_lbl = None
        if has_eol(beg_lbl):
            end_lbl = read_eol_labels(f, beg_lbl)
        img_constraints = constraint_from_labels(beg_lbl.system)
        img_offset = beg_lbl.vsl(SystemLabel.LBLSIZE) + img_constraints.nbh * img_constraints.recsize
        img = read_image_internal(f, img_offset, img_constraints)
        bpx: Optional[BinaryPrefix] = None
        bph: Optional[bytes] = None
        if img_constraints.nbb != 0:
            bpx = BinaryPrefix(read_binary_prefix(f, img_offset, img_constraints))
        if img_constraints.nbh != 0:
            bph = read_binary_header(f, beg_lbl)
        return VicarImage(
            name=str(path),
            labels=beg_lbl,
            eol_labels=end_lbl,
            data=img,
            binary_prefix=bpx,
            binary_header=bph
        )
