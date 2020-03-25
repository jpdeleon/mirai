#!/usr/bin/env python
r"""
1. filter known transiting planets from nexsci and save name and ephem as .txt file
2. create a batch file to run mirai (see `make_batch_mirai_nexsci.sh`)
3. execute batch file using parallel

Source:
"""
from os import path
import argparse

# import numpy as np
import astropy.units as u
from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
from astropy.coordinates import SkyCoord
import pandas as pd

pd.options.display.float_format = "{:.2f}".format

from mirai.mirai import get_tois, get_between_limits, get_above_lower_limit, get_below_upper_limit

arg = argparse.ArgumentParser()
arg.add_argument(
    "-o", "--outdir", help="output directory", type=str, default="."
)
arg.add_argument(
    "-s",
    "--save",
    help="save visibility plots and transit predictions in a csv file",
    action="store_true",
    default=False,
)
args = arg.parse_args()

output_colums = ",".split(
    ","
)

# fetch transiting planets from nexsci
archive = NasaExoplanetArchive.get_confirmed_planets_table(cache=False)
# transit =
teff = observed_planets["st_teff"]  # stellar effective temperature
rstar = observed_planets["st_rad"]  # stellar radius
a = observed_planets["pl_orbsmax"]  # orbital semimajor axis
teq = (teff * np.sqrt(rstar / (2 * a))).decompose()

# ---define filters---#
# transit
# multisector = tois['Sectors'].apply(lambda x: True if len(x.split(',')) > 1 else False)
# site-specific
# star
# planet
# size
# orbit
# special

## combine filters by uncommenting lines
idx = (
    (Porb > 0)  # makes sure no Nan in period
    # & (Rp>0) #makes sure no Nan in radius
    # ---telescope---#
    # & north
    # & south
    # ---transit---#
    & deep
    & hi_snr
    # ---star---#
    # & nearby
    & bright
    # & cool
    # & dwarf
    # & hot
    # & giant
    # & sunlike
    # & nearby
    # & young
    # ---planet---#
    # & temperate
    # & tropical
    # & warm
    # & small
    # & subearth
    # & superearth
    # & earth
    # & subneptune
    # & neptune
    # & subsaturn
    # & saturn
    # & jupiter
    # & inflated
    # & large
    # ---orbit---#
    # & short
    # & medium
    # & long
    # ---special---#
    # & usp
    # & hotjup
    # & tropical & subneptune
    # & tropical & subsaturn
    # & tropical & jupiter
    # & reinflated
    # & radius_gap
)

# filename_header = "all"
# if args.save:
#     # just save list of toi
#     fp = path.join(args.outdir, filename_header + "_tois.txt")
#     tois.loc[idx, "TOI"].to_csv(fp, index=False, header=None)
#     print(f"Saved: {fp}")
# else:
#     print(tois.loc[idx, output_colums].to_string(index=False))
