#!/usr/bin/env python
r"""
1. filter CTOI and save CTOI list as .txt file
2. create a batch file to run mirai (see `make_batch_mirai.sh`)
3. execute batch file using parallel

WATCH OUT: ctoi heading has inconsistent capitalization
err vs Err vs unit with no parentheses etc
"""
from os import path
import argparse

# import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord
import pandas as pd

pd.options.display.float_format = "{:.2f}".format

from mirai.mirai import (
    get_ctois,
    get_between_limits,
    get_above_lower_limit,
    get_below_upper_limit,
)

arg = argparse.ArgumentParser()
arg.add_argument(
    "-o", "--outdir", help="output directory", type=str, default="."
)
arg.add_argument(
    "-sig", "--sigma", help="strict=1 (default); conservative=3", default=1
)
arg.add_argument(
    "-f",
    "--frac_error",
    help="allowed fractional error in parameter",
    default=None,
    type=float,
)
arg.add_argument(
    "-s",
    "--save",
    help="save visibility plots and transit predictions in a csv file",
    action="store_true",
    default=False,
)
args = arg.parse_args()
sigma = args.sigma

output_colums = "CTOI,Period (days),Radius (R_Earth),Depth ppm".split(",")

# fetch toi table from exofop tess
ctois = get_ctois(remove_FP=True, clobber=False, verbose=False)
Rp = ctois["Radius (R_Earth)"]
Rp_err = ctois["Radius (R_Earth) Error"]
Porb = ctois["Period (days)"]
Porb_err = ctois["Period (days) Error"]
depth = ctois["Depth ppm"]
depth_err = ctois["Depth ppm Error"]
if args.frac_error:
    idx1 = (Rp_err / Rp) < args.frac_error
    idx2 = (Porb_err / Porb) < args.frac_error
    idx3 = (depth_err / depth) < args.frac_error
    ctois = ctois[idx1 & idx2 & idx3]

Rp = ctois["Radius (R_Earth)"]
Rp_err = ctois["Radius (R_Earth) Error"]
Porb = ctois["Period (days)"]
Porb_err = ctois["Period (days) Error"]
Rstar = ctois["Stellar Radius (R_Sun)"]
Rstar_err = ctois["Stellar Radius (R_Sun) err"]
teff = ctois["Stellar Eff Temp (K)"]
Teq = ctois["Equilibrium Temp (K)"]
depth = ctois["Depth ppm"]
depth_err = ctois["Depth ppm Error"]
Tmag = ctois["TESS Mag"]
Tmag_err = ctois["TESS Mag err"]
distance = ctois["Stellar Distance (pc)"]
# tois["Stellar log(g) (cm/s^2)"]

# ---define filters---#
# transit
deep = get_above_lower_limit(5, depth, depth_err, sigma=sigma)  # 1ppt
# site-specific
north = ctois["Dec"] > -30
south = ctois["Dec"] < 30
# star
bright = get_below_upper_limit(11, Tmag, Tmag_err, sigma=sigma)
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

filename_header = "all"
if args.save:
    # just save list of ctoi
    fp = path.join(args.outdir, filename_header + "_ctois.txt")
    ctois.loc[idx, "CTOI"].to_csv(fp, index=False, header=None)
    print(f"Saved: {fp}")
else:
    print(ctois.loc[idx, output_colums].to_string(index=False))
