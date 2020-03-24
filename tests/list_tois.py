#!/usr/bin/env python
r"""
1. filter TOI and save TOI list as .txt file
2. create a batch file to run mirai (see `make_batch_mirai.sh`)
3. execute batch file using parallel

Source:
"""
from os import path
import argparse

# import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord
import pandas as pd

pd.options.display.float_format = "{:.2f}".format

from mirai import mirai as mr

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

output_colums = "TOI,Period (days),Planet Radius (R_Earth),Depth (ppm)".split(
    ","
)

# fetch toi table from exofop tess
tois = mr.get_tois(remove_FP=True, clobber=False, verbose=False)
Rp = tois["Planet Radius (R_Earth)"]
Porb = tois["Period (days)"]
Teq = tois["Planet Equil Temp (K)"]
Rstar = tois["Stellar Radius (R_Sun)"]
teff = tois["Stellar Eff Temp (K)"]

# ---define filters---#
# transit
deep = tois["Depth (ppm)"] > 1000  # 1ppt
hi_snr = tois["Planet SNR"] > 10
# multisector = tois['Sectors'].apply(lambda x: True if len(x.split(',')) > 1 else False)
# site-specific
coord = SkyCoord(ra=tois["RA"], dec=tois["Dec"], unit=("hourangle", "deg"))
north = coord.dec.deg > 20
south = coord.dec.deg < -20
# star
bright = tois["TESS Mag"] < 10
cool = teff < 3500
hot = teff > 6500
dwarf = Rstar < 0.6
giant = Rstar > 1.6
sunlike = (Rstar.round() == 1.0) & (teff > 5500) & (teff < 6000)  # +logg & feh
nearby = tois["Stellar Distance (pc)"] < 100
young = tois["Stellar log(g) (cm/s^2)"] > 4.5
# planet
hot = Teq > 1000
temperate = (Teq > 500) & (Teq < 1000)
# size
small = Rp < 4.0
subearth = Rp < 1.0
earthlike = (Rp >= 1.0) & (Rp < 1.5)
superearth = (Rp >= 1.5) & (Rp < 2.0)
subneptune = (Rp >= 2.0) & (Rp < 4.0)
subsaturn = (Rp > 4.0) & (Rp <= 11.0)
large = Rp * u.Rearth.to(u.Rjup) > 1.0
# orbit
short = Porb < 3
long = Porb > 10
tropical = (Porb >= 5) & (Porb <= 10)
# special
usp = Porb <= 1
hotjup = short & large
radius_gap = (Rp >= 3.8) & (Rp <= 4.0)

## combine filters by uncommenting lines
idx = (
    (Porb > 0)  # makes sure no Nan in period
    # & (Rp>0) #makes sure no Nan in radius
    # ---telescope---#
    & north
    # & south
    # ---transit---#
    & hi_snr
    & deep
    # ---star---#
    # & nearby
    & bright
    # & cool
    # & dwarf
    # & hot
    & giant
    # & sunlike
    # ---planet---#
    # & hot
    # & temperate
    # & small
    # & superearth
    # & earthlike
    # & superearth
    # & subneptune
    & subsaturn
    # & large
    # ---orbit---#
    # & short
    # & long
    # & tropical
    # ---special---#
    & usp
    # & hotjup
    # & tropical & subneptune
    # & tropical & subsaturn
    # & tropical & large
    # & radius_gap
)

filename_header = "name"
if args.save:
    # just save list of toi
    fp = path.join(args.outdir, filename_header + "_tois.txt")
    tois.loc[idx, "TOI"].to_csv(fp, index=False, header=None)
    print(f"Saved: {fp}")
else:
    print(tois.loc[idx, output_colums].to_string(index=False))
