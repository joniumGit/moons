import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vicarui",
    version="0.0.1",
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
        "PySide2",
        "matplotlib",
        "vicarutil",
        "astropy",
        "numpy",
        "scikit-image",
        "scikit-learn"

    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)