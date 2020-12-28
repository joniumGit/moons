# Ring moons of Saturn
######(And their shadows)

### General
Needs Cassini mission kernels in `kernels/` directory to function
> Not here since uncompressed 37Gb or compressed 16Gb

Use [PyCharm](https://www.jetbrains.com/pycharm/) or similar IDE for development
and handling of python virtual environment

Uses [NASA NAIF Spice](https://naif.jpl.nasa.gov/naif/) which is provided 
by [SpiceyPy](https://github.com/AndrewAnnex/SpiceyPy)

Needs to parse [VICAR2](https://www-mipl.jpl.nasa.gov/external/VICAR_file_fmt.pdf) file format
and [PDS LBL](https://pds.jpl.nasa.gov/datastandards/pds3/standards/sr/Chapter05.pdf) files

TODO List:
 - [ ] Basic VICAR2 file reading
     - [x] Extract and process labels
     - [x] Extract Image data
     - [ ] \(Optional) Explore possibility to use `asyncio`
 - [ ] Reliable way to parse VICAR files
     - [ ] Handle various data types
     - [ ] Handle different byteorders
     - [ ] Handle important SYSTEM labels
 - [ ] Reliably interpreting VICAR image data
     - [ ] Handle all image sizes
     - [ ] Fully support all `n1-4` dimension values properly
     - [ ] Handle all image modes in spec
     - [ ] Pixel data types
 - [ ] Parsing LBL files
     - [ ] Create a meaningful and visualizable data model
     - [ ] Combine with IMG files and their LABELs
 - [ ] Combining LBL files and VICAR files
     - [ ] \(Optional) Transform LABELS into JSON and find a better platform independent format for image
 - [ ] Image processing
     - [ ] Acknowledge embedded processing steps
     - [ ] Use embedded calibration data
     - [ ] Configurable image calibration and processing
     - [ ] \(Optional) Handle Binary labels and prefixes
 - [ ] UI to visualize and browse data
     - [ ] Proper display of image data
     - [ ] Visual processing
     - [ ] Display and connect image and label data
     - [ ] Display relevant SPICE data with image
 - [ ] Automatic handling of full data (LBL(s) + IMG(s))  

### Status

Currently only a single Proof-of-Concept read for a VICAR files is done.
Next is implementing a reliable reader for VICAR files and expanding it to handle the full VICAR spec.

Simple test read and image show is in [main](main.py) and reading in [reader](vicar_utils/reader.py)
all based on previous work from [SpiceExample](idl/SpiceExample.pro) 
