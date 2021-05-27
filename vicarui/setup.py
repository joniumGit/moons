import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vicarui",
    version="0.0.2",
    author="joniumGit",
    author_email="52005121+joniumGit@users.noreply.github.com",
    description="Utilities for reading Vicar image files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joniumGit/moons",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "vicarutil",
        "PySide2",
        "matplotlib",
        "astropy",
        "numpy",
        "scikit-learn",
        "statsmodels"
    ],
    extras_require={
        "full": ["spiceypy"]
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7",
    entry_points={
        'console_scripts': ['vicarui = vicarui.vicarui:main']
    }
)
