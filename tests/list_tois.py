#!/usr/bin/env python
r"""
See https://arxiv.org/pdf/2003.11098.pdf to classify exoplanet systems

1. filter TOI and save TOI list as .txt file
2. create a batch file to run mirai (see `make_batch_mirai.sh`)
3. execute batch file using parallel

Source:
"""
from os import path
import argparse

import astropy.units as u
from astropy.coordinates import SkyCoord
import pandas as pd

pd.options.display.float_format = "{:.2f}".format

from mirai.mirai import (
    get_tois,
    get_between_limits,
    get_above_lower_limit,
    get_below_upper_limit,
)

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
args = arg.parse_args()

# fetch toi table from exofop tess
tois = get_tois(remove_FP=True, clobber=False, verbose=False)
output_colums = "TOI,Period (days),Planet Radius (R_Earth),Planet Radius (R_Earth) err".split(
    ","
)
sigma = args.sigma

tois = tois.drop_duplicates(
    subset=["Planet Radius (R_Earth)", "Planet Radius (R_Earth) err"],
    keep="first",
)
if args.frac_error:
    idx1 = (
        tois["Planet Radius (R_Earth) err"] / tois["Planet Radius (R_Earth)"]
    ) < args.frac_error
    idx2 = (
        tois["Period (days) err"] / tois["Period (days)"]
    ) < args.frac_error
    idx3 = (tois["Depth (mmag) err"] / tois["Depth (mmag)"]) < args.frac_error
    tois = tois[idx1 & idx2 & idx3]
Rp = tois["Planet Radius (R_Earth)"]
Rp_err = tois["Planet Radius (R_Earth) err"]
Porb = tois["Period (days)"]
Porb_err = tois["Period (days) err"]
Rstar = tois["Stellar Radius (R_Sun)"]
Rstar_err = tois["Stellar Radius (R_Sun) err"]
Teff = tois["Stellar Eff Temp (K)"]
Teff_err = tois["Stellar Eff Temp (K) err"]
Teq = tois["Planet Equil Temp (K)"]
depth = tois["Depth (mmag)"]
depth_err = tois["Depth (mmag) err"]
Tmag = tois["TESS Mag"]
Tmag_err = tois["TESS Mag"]
distance = tois["Stellar Distance (pc)"]
distance_err = tois["Stellar Distance (pc) err"]

# ---define filters---#
# transit
deep = get_above_lower_limit(5, depth, depth_err, sigma=sigma)  # 1ppt
hi_snr = get_above_lower_limit(10, tois["Planet SNR"], 1, sigma=sigma)
# multisector = tois['Sectors'].apply(lambda x: True if len(x.split(',')) > 1 else False)
# site-specific
coord = SkyCoord(ra=tois["RA"], dec=tois["Dec"], unit=("hourangle", "deg"))
north = coord.dec.deg > -20
south = coord.dec.deg < 20
# star
bright = get_below_upper_limit(11, Tmag, Tmag_err, sigma=sigma)
cool = get_below_upper_limit(3500, Teff, Teff_err, sigma=sigma)
hot = get_above_lower_limit(6500, Teff, Teff_err, sigma=sigma)
dwarf = get_below_upper_limit(0.6, Rstar, Rstar_err, sigma=sigma)
giant = get_above_lower_limit(1.6, Rstar, Rstar_err, sigma=sigma)
sunlike = get_between_limits(
    0.9, 1.1, Rstar, Rstar_err, sigma=sigma
) & get_between_limits(5500, 6000, Teff, Teff_err, sigma=sigma)
nearby = get_below_upper_limit(300, distance, distance_err, sigma=sigma)
# young = tois["Stellar log(g) (cm/s^2)"] > 4.5
# planet
temperate = get_between_limits(300, 500, Teff, Teff_err, sigma=sigma)
tropical = get_between_limits(500, 800, Teff, Teff_err, sigma=sigma)
warm = get_above_lower_limit(800, Teff, Teff_err, sigma=sigma)  # hot?
not_hot = get_below_upper_limit(1000, Teff, Teff_err, sigma=sigma)
# size
small = get_below_upper_limit(4, Rp, Rp_err, sigma=sigma)
subearth = get_below_upper_limit(1, Rp, Rp_err, sigma=sigma)
earth = get_between_limits(1, 1.5, Rp, Rp_err, sigma=sigma)
superearth = get_between_limits(1.5, 2, Rp, Rp_err, sigma=sigma)
subneptune = get_between_limits(2, 4, Rp, Rp_err, sigma=sigma)
neptune = get_between_limits(3.5, 4.5, Rp, Rp_err, sigma=sigma)
subsaturn = get_between_limits(5, 9, Rp, Rp_err, sigma=sigma)
saturn = get_between_limits(8.5, 9.5, Rp, Rp_err, sigma=sigma)
jupiter = get_between_limits(10.5, 11.5, Rp, Rp_err, sigma=sigma)
inflated = get_between_limits(12, 16, Rp, Rp_err, sigma=sigma)
large = get_above_lower_limit(16, Rp, Rp_err, sigma=sigma)
# orbit
short = get_below_upper_limit(3, Porb, Porb_err, sigma=sigma)
medium = get_between_limits(3, 10, Porb, Porb_err, sigma=sigma)
long = get_above_lower_limit(10, Porb, Porb_err, sigma=sigma)
# special
usp = get_below_upper_limit(1, Porb, Porb_err, sigma=sigma)
hotjup = short & get_above_lower_limit(11, Rp, Rp_err, sigma=sigma)
radius_gap = get_between_limits(1.8, 2, Rp, Rp_err, sigma=sigma)
reinflated = (
    get_above_lower_limit(
        11, Rp, Rp_err, sigma=sigma
    )  # See Lopez & Fortney 2015: arxiv.org/pdf/1510.00067.pdf
    & get_between_limits(10, 20, Porb, Porb_err, sigma=sigma)
    & get_between_limits(5, 10, Rstar, Rstar_err, sigma=sigma)
    & get_below_upper_limit(
        1, Rstar / Rstar_err, Rstar / Rstar_err, sigma=sigma
    )
)

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
    # & bright
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
    # & not_hot
    # & warm
    # & small
    # & subearth
    # & earth
    # & superearth
    # & subneptune
    # & neptune
    & subsaturn
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

filename_header = "subsaturn"
if args.save:
    # just save list of toi
    fp = path.join(args.outdir, filename_header + "_tois.txt")
    tois.loc[idx, "TOI"].to_csv(fp, index=False, header=None)
    print(f"Saved: {fp}")
else:
    print(tois.loc[idx, output_colums].to_string(index=False))
