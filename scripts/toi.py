#!/usr/bin/env python

from os import path
import argparse

import astropy.units as u
from mirai import mirai as mr

arg = argparse.ArgumentParser()
arg.add_argument(
        "-o", "--outdir",
        help="output directory",
        type=str,
        default='../tests/'
    )
arg.add_argument(
        "-s",
        "--save",
        help="save visibility plots and transit predictions in a csv file",
        action="store_true",
        default=False,
    )
args = arg.parse_args()

output_colums = 'TOI,Period (days),Planet Radius (R_Earth)'.split(',')

#
tois = mr.get_tois(remove_FP=True, clobber=False, verbose=False)

##filters
#transit
deep = tois['Depth (ppm)']*1e6 > 1000 #1ppt
hi_snr = tois['Planet SNR'] > 10
#multisector = tois['Sectors'].apply(lambda x: True if len(x.split(',')) > 1 else False)
#star
bright = tois['TESS Mag'] < 10
nearby = tois['Stellar Distance (pc)'] < 100
cool = tois['Stellar Eff Temp (K)'] < 3500
dwarf = tois['Stellar Radius (R_Sun)'] < 0.6
giant = tois['Stellar Radius (R_Sun)'] > 1.6
hot = tois['Stellar Eff Temp (K)'] > 6500
young = tois['Stellar log(g) (cm/s^2)'] > 4.5
#planet
temperate = tois['Planet Equil Temp (K)'] > 800
tropical = (tois['Planet Equil Temp (K)'] > 500) & (tois['Planet Equil Temp (K)'] < 800)
#size
Rp = tois['Planet Radius (R_Earth)']
superearth = (Rp>=1.5) & (Rp<2.0)
subneptune = (Rp>=2.0) & (Rp<4.0)
radius_gap = (Rp>=3.8) & (Rp<=4.0)
subsaturn = (Rp>4.0) & (Rp<=11.0)
jupiter = Rp*u.Rearth.to(u.Rjup) > 1.0
#special
usp = tois['Period (days)']<=1
tropical = (tois['Period (days)']>=5) & (tois['Period (days)']<=10)
hotjup = (tois['Period (days)']<=2) & (Rp*u.Rearth.to(u.Rjup)>=1.0)

##combine filters
#idx = deep & bright & hi_snr & tropical & jupiter
idx = deep & bright & hi_snr & subneptune

if args.save:
    fp = path.join(args.outdir,'subneptune.txt')
    tois.loc[idx,'TOI'].to_csv(fp, index=False, header=None)
    print(f'Saved: {fp}')
else:
    print(tois.loc[idx,output_colums])
