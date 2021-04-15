import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="vicarutil",
    version="0.1.0",
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
        "numpy"
    ],
    extras_require={
        "spice": ["spiceypy", "matplotlib"]
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7",
    entry_points={
        'console_scripts': ['vicarutil = vicarutil.vicarutil:main']
    }
)
