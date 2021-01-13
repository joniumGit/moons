from typing import BinaryIO

from .definitions.definitions import VSL
from .entity import VicarImage, BinaryPrefix
from .image import constraint_from_labels, read_img, read_binary_prefix
from .label import read_beg_labels, has_eol, read_eol_labels, read_binary_header


def read_image(f: BinaryIO) -> VicarImage:
    """
    Reads all iage and label data from a Vicar file
    :param f: File to read
    :return: VicarData object
    """
    beg_lbl = read_beg_labels(f)
    end_lbl = None
    if has_eol(beg_lbl):
        end_lbl = read_eol_labels(f, beg_lbl)
    img_constraints = constraint_from_labels(beg_lbl.system)
    img_offset = beg_lbl.vsl(VSL.LBLSIZE) + img_constraints.nbh * img_constraints.recsize
    img = read_img(f, img_offset, img_constraints)
    bpx = None
    bph = None
    if img_constraints.nbb != 0:
        bpx = read_binary_prefix(f, img_offset, img_constraints)
    if img_constraints.nbh != 0:
        bph = read_binary_header(f, beg_lbl)
    return VicarImage(
        labels=beg_lbl,
        eol_labels=end_lbl,
        data=img,
        binary_prefix=BinaryPrefix(bpx),
        binary_header=bph
    )
