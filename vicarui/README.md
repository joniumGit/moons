# VicarUI

## UI Module for viewing Vicar Image files

This module gives functionality to display Vicar image files, do background reduction and analysis. This is designed to
analyze shadows in the Cassini probe images, but could be used for anything else too.

## usage

The viewer is very simple to use, load images and start analyzing. During image loading the program tries to find
the ``IDENTIFICATION`` property label from the image in order to group them by the sequence id, but it should work with
it absent too.

The UI should be quite self-explanatory for the features which include:

- background reduction
- normalization
- image geometry viewing
- label viewer
- image area inspection
- displaying mission data extracted from the kernels (image size, geometry, angles)
- overriding target selection and others
- polynomial fitting

### Background reduction

Background reduction is done with __LinearRegression__ models from __Scikit-learn__, and a background smoothing step is
optionally included with __RANSACRegressor__. The fitted polynomial degree is user configurable from the ui, and it is
implemented in the learning models with __PolynomialFeatures__. [Robust fitting by Scikit](
https://scikit-learn.org/stable/auto_examples/linear_model/plot_robust_fit.html
).

### Inspection

The area inspection view is an average of the first dimension selected in the viewers upper corner
``width``, the ``window`` controls selection width.

In this window you can fit 2 polynomials by clicking on parts of the plots. Forming a range by clicking twice will fit a
single __LinearRegressor__ on the smaller range, used as the shadow fit in my thesis, and a __LinearRegressor__
backed __RANSACRegressor__
on the other part to form a _background_ fit.

### commands

The new and _better_ viewer:

``
vicarui viewer --kernel-path "path to cassini mission kernels"
``

Additionally:

- ``--debug`` for more printing in console
- ``--mission`` for importing some other mission module than what is present here, or
  ``empty`` for nothing

#### Missions

These were made so that custom functionality could be added if this was used as a simple viewer for example. The
callsites can be checked from the ``analysis`` module.

#### Old

There's also a prototype made with Tkinter:

``
vicarui alt-viewer
``

This is just a viewer for the images and allows for different stretches from Astropy