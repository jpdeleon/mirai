# -*- coding: utf-8 -*-
import os
from os.path import join, exists
import datetime as dt

import numpy as np
import matplotlib.pyplot as pl
import pandas as pd
from astroquery.mast import Catalogs
from astropy.coordinates import SkyCoord, Distance
import astropy.units as u
from astroplan.plots import plot_altitude

from mirai.config import DATA_PATH


__all__ = [
    "SITES",
    "parse_target_coord",
    "get_tois",
    "get_ctois",
    "get_toi",
    "plot_full_transit",
    "plot_partial_transit",
    "get_ephem_from_nexsci"
]

# lat,lon, elev, local timezone
SITES = {
    "OAO": (34.5761, 133.5941, 343, "Asia/Tokyo"),  # Okayama
    "OT": (28.291, 343.5033, 2395, "UTC"),  # Teide
    "SBO": (
        -31.2733,
        149.0617,
        1145,
        "Australia/Brisbane",
    ),  # spring brook obs
    "AAO": (-31.2754, 149.067, 1164, "Australia/NSW"),  # aka siding spring obs
    "TRO": (-30.1692, -70.805, 2286, "America/Santiago"),  # cerro tololo obs
    "TNO": (18.59056, 98.48656, 2457, "Asia/Bangkok"),  # Thai national obs
    "SAAO": (
        -32.376006,
        20.810678,
        1798,
        "Africa/Johannesburg",
    ),  # South Africa astro obs
}

def get_ephem_from_nexsci(target):
    try:
        from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    except Exception:
        raise ModuleNotFoundError

    planet_properties = NasaExoplanetArchive.query_planet(target+' b', all_columns=True)

    t0 = planet_properties['pl_tranmid'][0]
    per = planet_properties['pl_orbper'].value[0] #has unit already
    dur = planet_properties['pl_trandur'][0]
    return (t0, per, dur)

def parse_target_coord(target):
    if len(target.split(",")) == 2:
        # coordinates
        if len(target.split(":")) == 6:
            coord = SkyCoord(target, unit=("hourangle", "degree"))
        else:
            coord = SkyCoord(target, unit=("deg", "degree"))
    else:
        # name or ID
        if target[:3] == "toi":
            toiid = float(target[3:])
            coord = get_coord_from_toiid(toiid)
        elif target[:4] == "ctoi":
            ctoiid = float(target[4:])
            coord = get_coord_from_ctoiid(ctoiid)
        elif target[:3] == "tic":
            ticid = float(target[3:])
            coord = get_coord_from_ticid(ticid)
        elif target[:4] == "epic":
            epicid = float(target[4:])
            coord = get_coord_from_toiid(epicid)
        elif target[:2] == "k2":
            k2id = float(target[2:])
            coord = SkyCoord.from_name("K2 " + str(k2id))
        elif target[:4] == "gaia":
            gaiaid = float(target[4:])
            coord = SkyCoord.from_name("Gaia DR2 " + str(gaiaid))
        else:
            coord = SkyCoord.from_name(target)
    return coord


def get_tois(
    clobber=True,
    outdir=DATA_PATH,
    verbose=False,
    remove_FP=True,
    remove_known_planets=False,
):
    """Download TOI list from TESS Alert/TOI Release.

    Parameters
    ----------
    clobber : bool
        re-download table and save as csv file
    outdir : str
        download directory location
    verbose : bool
        print texts

    Returns
    -------
    d : pandas.DataFrame
        TOI table as dataframe
    """
    dl_link = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
    fp = join(outdir, "TOIs.csv")
    if not exists(outdir):
        os.makedirs(outdir)

    if not exists(fp) or clobber:
        d = pd.read_csv(dl_link)  # , dtype={'RA': float, 'Dec': float})
        msg = "Downloading {}\n".format(dl_link)
    else:
        d = pd.read_csv(fp).drop_duplicates()
        msg = "Loaded: {}\n".format(fp)
    d.to_csv(fp, index=False)

    # remove False Positives
    if remove_FP:
        d = d[d["TFOPWG Disposition"] != "FP"]
        msg += "TOIs with TFPWG disposition==FP are removed.\n"
    if remove_known_planets:
        planet_keys = [
            "HD",
            "GJ",
            "LHS",
            "XO",
            "Pi Men" "WASP",
            "SWASP",
            "HAT",
            "HATS",
            "KELT",
            "TrES",
            "QATAR",
            "CoRoT",
            "K2",  # , "EPIC"
            "Kepler",  # "KOI"
        ]
        keys = []
        for key in planet_keys:
            idx = ~np.array(
                d["Comments"].str.contains(key).tolist(), dtype=bool
            )
            d = d[idx]
            if idx.sum() > 0:
                keys.append(key)
        msg += "{} planets are removed.\n".format(keys)
    msg += "Saved: {}\n".format(fp)
    if verbose:
        print(msg)
    return d.sort_values("TOI")


def get_ctois(clobber=True, outdir=DATA_PATH, verbose=False, remove_FP=True):
    """Download Community TOI list from exofop/TESS.

    Parameters
    ----------
    clobber : bool
        re-download table and save as csv file
    outdir : str
        download directory location
    verbose : bool
        print texts

    Returns
    -------
    d : pandas.DataFrame
        CTOI table as dataframe

    See interface: https://exofop.ipac.caltech.edu/tess/view_ctoi.php
    See also: https://exofop.ipac.caltech.edu/tess/ctoi_help.php
    """
    dl_link = "https://exofop.ipac.caltech.edu/tess/download_ctoi.php?sort=ctoi&output=csv"
    fp = join(outdir, "CTOIs.csv")
    if not exists(outdir):
        os.makedirs(outdir)

    if not exists(fp) or clobber:
        d = pd.read_csv(dl_link)  # , dtype={'RA': float, 'Dec': float})
        msg = "Downloading {}\n".format(dl_link)
    else:
        d = pd.read_csv(fp).drop_duplicates()
        msg = "Loaded: {}\n".format(fp)
    d.to_csv(fp, index=False)

    # remove False Positives
    if remove_FP:
        d = d[d["User Disposition"] != "FP"]
        msg += "CTOIs with user disposition==FP are removed.\n"
    msg += "Saved: {}\n".format(fp)
    if verbose:
        print(msg)
    return d.sort_values("CTOI")


def get_toi(
    toiid, clobber=True, outdir=DATA_PATH, add_FPP=False, verbose=True
):
    """Query TOI from TOI list

    Parameters
    ----------
    toiid : float
        TOI id
    clobber : bool
        re-download csv file
    outdir : str
        csv path
    verbose : bool
        print texts

    Returns
    -------
    q : pandas.DataFrame
        TOI match else None
    """

    df = get_tois(clobber=clobber, verbose=verbose, outdir=outdir)

    if isinstance(toiid, int):
        toi = float(str(toiid) + ".01")
    else:
        planet = str(toiid).split(".")[1]
        assert len(planet) == 2, "use pattern: TOI.01"
    idx = df["TOI"].isin([toiid])
    q = df.loc[idx]
    assert len(q) > 0, "TOI not found!"

    q.index = q["TOI"].values
    if verbose:
        print("Data from TOI Release:\n")
        columns = [
            "Period (days)",
            "Epoch (BJD)",
            "Duration (hours)",
            "Depth (ppm)",
            "Comments",
        ]
        print("{}\n".format(q[columns].T))

    if q["TFOPWG Disposition"].isin(["FP"]).any():
        print("\nTFOPWG disposition is a False Positive!\n")

    return q.sort_values(by="TOI", ascending=True)


def get_coord_from_toiid(toiid):
    toi = get_toi(toiid)
    coord = SkyCoord(
        ra=toi["RA"].values[0],
        dec=toi["Dec"].values[0],
        distance=toi["Stellar Distance (pc)"].values[0],
        unit=(u.hourangle, u.degree, u.pc),
    )
    return coord


def get_coord_from_ctoiid(ctoiid, clobber=True, verbose=True):
    ctois = get_ctois(clobber=clobber, verbose=verbose)
    ctoi = ctois[ctois["TIC ID"].isin([ctoiid])]
    coord = SkyCoord(
        ra=ctoi["RA"].values[0],
        dec=ctoi["Dec"].values[0],
        distance=ctoi["Stellar Distance (pc)"].values[0],
        unit=(u.degree, u.degree, u.pc),
    )
    return coord


def get_coord_from_ticid(ticid):
    df = Catalogs.query_criteria(catalog="Tic", ID=ticid).to_pandas()
    coord = SkyCoord(
        ra=df.iloc[0]["ra"],
        dec=df.iloc[0]["dec"],
        distance=Distance(parallax=df.iloc[0]["plx"] * u.mas).pc,
        unit=(u.degree, u.degree, u.pc),
    )
    return coord


def get_coord_from_epic(epicid):
    try:
        import k2plr

        client = k2plr.API()
    except Exception:
        raise ModuleNotFoundError(
            "pip install git+https://github.com/rodluger/k2plr.git"
        )
    epicid = int(epicid)
    star = client.k2_star(epicid)
    ra = float(star.k2_ra)
    dec = float(star.k2_dec)
    coord = SkyCoord(ra=ra, dec=dec, unit="deg")
    return coord


def get_coord_from_gaiaid(gaiaid):
    coord = SkyCoord.from_name("Gaia DR2 {}".format(gaiaid))
    return coord


def plot_full_transit(obs_date, target_coord, obs_site, name=None, ax=None):
    """
    """
    if ax is None:
        fig, ax = pl.subplots(1, 1, figsize=(10, 6))

    ing = obs_date[0]
    egr = obs_date[1]
    t14 = (obs_date[1] - obs_date[0]).value
    mid = ing + dt.timedelta(days=t14 / 2)

    _ = plot_altitude(
        targets=target_coord,
        observer=obs_site,
        time=mid.datetime,
        brightness_shading=True,
        airmass_yaxis=True,
        min_altitude=20,  # deg
        ax=ax,
    )

    ax.axhline(30, 0, 1, c="r", ls="--", label="limit")
    ax.axvline(ing.datetime, 0, 1, c="k", ls="--", label="ing/egr")
    ax.axvline(mid.datetime, 0, 1, c="k", ls="-", label="mid")
    ax.axvline(egr.datetime, 0, 1, c="k", ls="--", label="_nolegend_")
    if name is None:
        name = "ra,dec=({})".format(target_coord.to_string())
    ax.set_title("{} @ {}".format(name, obs_site.name))
    fig.tight_layout()
    # ax.legend()
    return fig


def plot_partial_transit():
    NotImplementedError
