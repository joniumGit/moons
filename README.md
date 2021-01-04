# Ring moons of Saturn

### General

Needs Cassini mission kernels in `kernels/` directory to function
> Not here since uncompressed 37Gb or compressed 16Gb

Use [PyCharm](https://www.jetbrains.com/pycharm/) or similar IDE for development and handling of python virtual
environment

Uses [NASA NAIF Spice](https://naif.jpl.nasa.gov/naif/) which is provided
by [SpiceyPy](https://github.com/AndrewAnnex/SpiceyPy)

Needs to parse [VICAR2](https://www-mipl.jpl.nasa.gov/external/VICAR_file_fmt.pdf) file format
and [PDS LBL](https://pds.jpl.nasa.gov/datastandards/pds3/standards/sr/Chapter05.pdf) files

TODO List:

- [x] **Basic VICAR2 file reading**
    - [x] Extract and process labels
    - [x] Extract Image data
    - [ ] ~~(Optional) Explore possibility to use `asyncio`.~~
- [x] **Reliable way to parse VICAR files**
    - [x] Handle various data types
    - [x] Handle different byteorders
    - [x] Handle important SYSTEM labels
- [x] **Reliably interpreting VICAR image data**
    - [x] Handle all image sizes
    - [x] Fully support all `n1-4` dimension values properly
    - [ ] Handle all image modes in spec
    - [x] Pixel data types
- [ ] **Parsing LBL files**
    - [ ] Create a meaningful and visualizable data model
    - [ ] Combine with IMG files and their LABELs
- [ ] **Combining LBL files and VICAR files**
    - [ ] ~~(Optional) Transform LABELS into JSON and find a better platform independent format for image~~
- [ ] **Image processing**
    - [ ] ~~Acknowledge embedded processing steps~~ _**unlikely**_
    - [ ] ~~Use embedded calibration data~~ _**unlikely**_
    - [ ] Configurable image calibration and processing
    - [ ] ~~(Optional) Handle Binary labels and prefixes~~ _**missing documentation**_
- [ ] **UI to visualize and browse data**
    - [ ] Proper display of image data
    - [ ] Visual processing
    - [ ] Display and connect image and label data
    - [ ] Display relevant SPICE data with image
- [ ] **Automatic handling of full data (LBL(s) + IMG(s))**
- [ ] **Limb fitting and shadow extraction**
    - [ ] Recognize phase angle from image
    - [ ] Compare calculated and image phase angles
    - [ ] Image alignment correction

### Status

Currently only a single Proof-of-Concept read for a VICAR files is done. Next is implementing a reliable reader for
VICAR files and expanding it to handle the full VICAR spec.

**2021.01.04:**

New reader is implemented in hopes that it will better support all image types.  
Begun work on some ui and image display capabilities.  
Missing any actual tests for the code.  
Needs more test images to see if parsing is actually reliable.

### Notes

Simple test read and image show is in [main](src/main.py) and reading in [reader](src/vicar_utils/reader.py)
all based on previous work from [SpiceExample](idl/SpiceExample.pro) 
