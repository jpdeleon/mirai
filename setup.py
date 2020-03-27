# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from mirai import __version__, name

setup(
    name=name,
    version=__version__,
    description="Simple transit and ephemeris tool",
    author="Jerome de Leon",
    author_email="jpdeleon@astron.s.u-tokyo.ac.jp",
    license="MIT",
    packages=find_packages(),
    scripts=["scripts/mirai"],  # "scripts/toi"],
    install_requires=["astropy", "astroquery", "astroplan", "pytz", "pandas"],
)
