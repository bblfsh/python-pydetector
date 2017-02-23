# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

description = long_descr = "Python command line application & package to guess the Python version of a file"

main_ns = {}
with open("pydetector/version.py") as ver_file:
    exec(ver_file.read(), main_ns)

version = main_ns['__version__']
setup(
    name = "pydetector",
    version = version,

    description = description,
    long_description = long_descr,
    license = "MIT",
    url = "https://github.com/juanjux/python-pydetector",
    download_url = "https://github.com/juanjux/python-pydetector/archive/%s.tar.gz" % version,
    author = "Juanjo Alvarez",
    author_email = "juanjo@juanjoalvarez.net",
    packages = find_packages(exclude=["tests"]),
    entry_points = {
        "console_scripts": [
            "pydetector = pydetector.cli:main"
        ]
    },
    install_requires = ["six"],
    extras_require = {},
    classifiers = [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Compilers",
        "Topic :: Software Development :: Disassemblers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5"
    ]
)
