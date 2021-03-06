# -*- coding: utf-8 -*-
import os
from os.path import join, exists
import datetime as dt

import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as pl
import pandas as pd
from astroquery.mast import Catalogs
from astropy.coordinates import SkyCoord, Distance
import astropy.units as u
from astroplan.plots import plot_altitude

from mirai.config import DATA_PATH

TESS_TIME_OFFSET = 2457000.0  # TBJD = BJD - 2457000.0
K2_TIME_OFFSET = 2454833  # BKJD


__all__ = [
    "SITES",
    "parse_target_coord",
    "get_tois",
    "get_ctois",
    "get_toi",
    "plot_full_transit",
    "plot_partial_transit",
    "get_ephem_from_file",
    "get_ephem_from_nexsci",
    "get_t0_per_dur",
    "format_datetime",
    "parse_ing_egr",
    "parse_ing_egr_list",
    "parse_mid_list",
    "get_below_upper_limit",
    "get_above_lower_limit",
    "get_between_limits",
]
# TODO: EarthLocation().get_site_names(); pytz.all_timezones()
# subaru = EarthLocation().of_site("subaru")
# latlonh = subaru.geodetic;
# subaru.info.meta['timezone']
# TCS@OT, PROMPT-8/TRO @ CTIO, 188/Seimei@OAO
SITES = {
    # lat,lon, elev, local timezone
    "OAO": (34.5761, 133.5941, 343, "Asia/Tokyo"),  # Okayama
    "ALI": (32.3167, 80.0167, 5100, "Etc/GMT+8"),  # Ali Obs, Tibet, China
    "MCDO": (30.67, -104.02, 2070, "UCT"),  # Texas, Central Time
    "WISE": (30.5958, 34.76333, 875, "Asia/Jerusalem"),  # NRES@WISE
    "OT": (28.291, 343.5033, 2395, "UTC"),  # Teide
    "ALS": (24.1776, 54.6862, 100, "Etc/GMT+4"),  # Al Sadeem Obs
    "HLK": (20.7075, -156.2561, 3055, "Pacific/Honolulu"),  # Haleakala
    "TNO": (18.59056, 98.48656, 2457, "Asia/Bangkok"),  # Thai national obs
    "CTIO": (
        -30.1675,
        -70.8047,
        2198,
        "America/Santiago",
    ),  # Cerro Tololo, Chile
    "SBO": (
        -31.2733,
        149.0617,
        1145,
        "Australia/Brisbane",
    ),  # spring brook obs
    "SSO": (-31.2754, 149.067, 1164, "Australia/NSW"),
    "AAO": (-31.2754, 149.067, 1164, "Australia/NSW"),  # aka siding spring obs
    "SAAO": (
        -32.3760,
        20.8107,
        1798,
        "Africa/Johannesburg",
    ),  # South Africa astro obs
}


def parse_ing_egr(ing_egr):
    """get also mitransit from ing and egr"""
    errmsg = "must be a pair of astropy Time"
    assert len(ing_egr.datetime) == 2, errmsg
    ing, egr = ing_egr
    t14 = (egr - ing).value
    mid = ing + dt.timedelta(days=t14 / 2)
    return (ing, mid, egr)


def parse_ing_egr_list(ing_egr_list, details=None):
    """
    TODO: make sure tdb iso is precise

    output will be saved in csv
    """
    errmsg = "must be a pair of astropy Time"
    assert len(ing_egr_list[0]) == 2, errmsg
    t12 = ["ingress"]
    tmid = ["midtransit"]
    t34 = ["egress"]
    for ing, egr in ing_egr_list:
        t14 = (egr - ing).value
        mid = ing + dt.timedelta(days=t14 / 2)
        t12.append(ing.tdb.iso)
        tmid.append(mid.tdb.iso)
        t34.append(egr.tdb.iso)
    return np.c_[(t12, tmid, t34)]


def parse_mid_list(mid_list, transit_duration):
    """
    TODO: make sure tdb iso is precise

    output will be saved in csv
    """
    t12 = ["ingress"]
    tmid = ["midtransit"]
    t34 = ["egress"]
    for mid in mid_list:
        ing = mid - dt.timedelta(days=transit_duration / 2)
        egr = mid + dt.timedelta(days=transit_duration / 2)
        t12.append(ing.tdb.iso)
        tmid.append(mid.tdb.iso)
        t34.append(egr.tdb.iso)
    return np.c_[(t12, tmid, t34)]


def format_datetime(datetime, datefmt="%Y%b%d"):
    return datetime.date().strftime(datefmt)


def get_t0_per_dur(target, fp=None, **kwargs):
    """
    If TIC is given, the TOI table is searched first
    then CTOI table.
    """
    if fp is not None:
        errmsg = "only h5 from tql is supported"
        assert fp.split(".")[-1] == "h5", errmsg
        t0, per, dur = get_ephem_from_file(fp, verbose=True)
    elif target[:3] == "toi":
        if len(str(target).split(".")) == 2:
            toi = get_toi(target[3:], **kwargs)
        else:
            toi = get_toi(target[3:] + ".01", **kwargs)
        t0 = toi["Epoch (BJD)"].values[0]
        per = toi["Period (days)"].values[0]
        dur = toi["Duration (hours)"].values[0] / 24
    elif target[:4] == "ctoi":
        ctoiid = float(target[4:])
        if len(str(target).split(".")) == 2:
            ctoi = get_ctoi(target[4:], **kwargs)
        else:
            ctoi = get_ctoi(target[4:] + ".01", **kwargs)
        t0 = ctoi["Midpoint (BJD)"].values[0]
        per = ctoi["Period (days)"].values[0]
        dur = ctoi["Duration (hrs)"].values[0] / 24
    elif target[:3] == "tic":
        """check TIC if TOI or CTOI else ask ephem"""
        # get toiid from toi table
        tois = get_tois(**kwargs)
        if len(str(target[3:]).split(".")) == 2:
            # e.g. TICxxxxxx.02
            # if candidate number is .02, its index n=int(.02)-1 = 1
            n = int(str(target[3:]).split(".")[-1]) - 1
        else:
            # e.g. TICxxxxxx or TICxxxxxx.01
            # default n=0 for first candidate
            n = 0
        ticid = int(target[3:].split(".")[0])
        toi = tois[tois["TIC ID"].isin([ticid])]
        assert n <= len(toi), "n-th planet candidate not found in TOI table"
        if len(toi) > 0:
            print("Using ephemeris from TOI")
            toiid = toi["TOI"].values[n]
            print(f"TIC {ticid} == TOI {toiid}!")
            toi = get_toi(toiid, **kwargs)
            t0 = toi["Epoch (BJD)"].values[0]
            per = toi["Period (days)"].values[0]
            dur = toi["Duration (hours)"].values[0] / 24
        else:
            # check CTOI
            ctois = get_ctois(**kwargs)
            ctoi = ctois[ctois["TIC ID"].isin([ticid])]
            if len(ctoi) > 0:
                print("Using ephemeris from CTOI")
                ctoiid = ctoi["CTOI"].values[0]
                ctoi = get_ctoi(ctoiid, **kwargs)
                t0 = ctoi["Midpoint (BJD)"].values[0]
                per = ctoi["Period (days)"].values[0]
                dur = ctoi["Duration (hrs)"].values[0] / 24
                print(
                    f"TIC {ticid} is CTOI {ctoiid} with {len(ctoi)} candidates!"
                )
            else:
                raise ValueError("Provide t0,per,dur")
    elif target[:6] == "kepler":
        raise NotImplementedError("Provide t0,per,dur")
        # print('Using ephemeris from NExSci')
        # import k2plr
        # client = k2plr.API()
        # kepid = int(target[6:])
        # planet = client.planet(f"Kepler-{kepid}b")
        # import pdb; pdb.set_trace()
        # # planet.period

    elif target[:4] == "epic":
        raise NotImplementedError("Provide t0,per,dur")
        # print('Using ephemeris from NExSci')
        # import k2plr
        # client = k2plr.API()
        # epicid = int(target[4:])
        # import pdb; pdb.set_trace()

    # elif (target[:4] in ['wasp','epic','kelt']) | (target[:2]=='k2') | (target[:3]=='hat'):
    # print('Using ephemeris from NExSci')
    #    #TODO add more known planet names
    #    t0,per,dur = get_ephem_from_nexsci(target)
    else:
        raise ValueError("Provide t0,per,dur")
    assert (t0 is not None) & (not np.isnan(t0)) & (t0 != 0), "Error in t0"
    assert (per is not None) & (not np.isnan(per)) & (per != 0), "Error in per"
    assert (dur is not None) & (not np.isnan(dur)) & (dur != 0), "Error in dur"
    return (t0, per, dur)


def get_ephem_from_file(fp, verbose=True):
    """read ephem from .h5 file from tql
    """
    try:
        import deepdish as dd
    except Exception:
        raise ModuleNotFoundError("pip install deepdish")

    if verbose:
        print("Loaded: ", fp)
    d = dd.io.load(fp)
    per = d["period"]
    t0 = d["T0"] + TESS_TIME_OFFSET
    dur = d["duration"]
    return t0, per, dur


def get_ephem_from_nexsci(target):
    try:
        from astroquery.nasa_exoplanet_archive import NasaExoplanetArchive
    except Exception:
        raise ModuleNotFoundError

    planet_properties = NasaExoplanetArchive.query_planet(
        target + " b", all_columns=True
    )

    t0 = planet_properties["pl_tranmid"][0]
    per = planet_properties["pl_orbper"].value[0]  # has unit already
    dur = planet_properties["pl_trandur"][0]
    return (t0, per, dur)


def parse_target_coord(target, **kwargs):
    """
    parse target string and query coordinates; e.g.
    toi.X, ctoi.X, tic.X, gaiaX, epicX, Simbad name
    """
    assert isinstance(target, str)
    if len(target.split(",")) == 2:
        # coordinates: ra, dec
        if len(target.split(":")) == 6:
            # e.g. 01:02:03.0, 04:05:06.0
            coord = SkyCoord(target, unit=("hourangle", "degree"))
        else:
            # e.g. 70.5, 80.5
            coord = SkyCoord(target, unit=("degree", "degree"))
    else:
        # name or ID
        if target[:3] == "toi":
            toiid = float(target[3:])
            coord = get_coord_from_toiid(toiid, **kwargs)
        elif target[:4] == "ctoi":
            ctoiid = float(target[4:])
            coord = get_coord_from_ctoiid(ctoiid, **kwargs)
        elif target[:3] == "tic":
            # TODO: requires int for astroquery.mast.Catalogs to work
            if len(target[3:].split(".")) == 2:
                ticid = int(target[3:].split(".")[1])
            else:
                ticid = int(target[3:])
            coord = get_coord_from_ticid(ticid)
        elif target[:4] == "epic":
            epicid = float(target[4:])
            coord = get_coord_from_epicid(epicid)
        elif target[:2] == "k2":
            k2id = float(target[2:])
            coord = SkyCoord.from_name("K2-" + str(k2id))
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
        msg = f"Downloading {dl_link}"
        d = pd.read_csv(dl_link)  # , dtype={'RA': float, 'Dec': float})
        d.to_csv(fp, index=False)
    else:
        d = pd.read_csv(fp)
        msg = f"Loaded: {fp}\n"
    assert len(d) > 1000, f"{fp} likely has been overwritten!"

    # remove False Positives
    if remove_FP:
        d = d[d["TFOPWG Disposition"] != "FP"]
        msg += "TOIs with TFOPWG disposition==FP are removed.\n"
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
        msg += f"{keys} planets are removed.\n"
    msg += f"Saved: {fp}\n"
    if verbose:
        print(msg)
    return d.sort_values("TOI", ascending=True)


def get_toi(toi, verbose=False, remove_FP=True, clobber=False):
    """Query TOI from TOI list

    Parameters
    ----------
    toi : float
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
    df = get_tois(verbose=False, remove_FP=remove_FP, clobber=clobber)

    if isinstance(toi, int):
        toi = float(str(toi) + ".01")
    else:
        planet = str(toi).split(".")[1]
        assert len(planet) == 2, "use pattern: TOI.01"
    idx = df["TOI"].isin([toi])
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
        print(f"{q[columns].T}\n")

    if q["TFOPWG Disposition"].isin(["FP"]).any():
        print("\nTFOPWG disposition is a False Positive!\n")

    return q.sort_values(by="TOI", ascending=True)


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


def get_ctoi(ctoi, verbose=False, remove_FP=False, clobber=False):
    """Query CTOI from CTOI list

    Parameters
    ----------
    ctoi : float
        CTOI id

    Returns
    -------
    q : pandas.DataFrame
        CTOI match else None
    """
    ctoi = float(ctoi)
    df = get_ctois(verbose=False, remove_FP=remove_FP, clobber=clobber)

    if isinstance(ctoi, int):
        ctoi = float(str(ctoi) + ".01")
    else:
        planet = str(ctoi).split(".")[1]
        assert len(planet) == 2, "use pattern: CTOI.01"
    idx = df["CTOI"].isin([ctoi])

    q = df.loc[idx]
    assert len(q) > 0, "CTOI not found!"

    q.index = q["CTOI"].values
    if verbose:
        print("Data from CTOI Release:\n")
        columns = [
            "Period (days)",
            "Midpoint (BJD)",
            "Duration (hours)",
            "Depth ppm",
            "Notes",
        ]
        print(f"{q[columns].T}\n")
    if (q["TFOPWG Disposition"].isin(["FP"]).any()) | (
        q["User Disposition"].isin(["FP"]).any()
    ):
        print("\nTFOPWG/User disposition is a False Positive!\n")

    return q.sort_values(by="CTOI", ascending=True)


def get_coord_from_toiid(toiid, **kwargs):
    toi = get_toi(toiid, **kwargs)
    coord = SkyCoord(
        ra=toi["RA"].values[0],
        dec=toi["Dec"].values[0],
        distance=toi["Stellar Distance (pc)"].values[0],
        unit=(u.hourangle, u.degree, u.pc),
    )
    return coord


def get_coord_from_ctoiid(ctoiid, **kwargs):
    ctoi = get_ctoi(ctoiid, **kwargs)
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


def get_coord_from_epicid(epicid):
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


def plot_full_transit(
    obs_date,
    target_coord,
    obs_site,
    name=None,
    ephem_label=None,
    night_only=True,
):
    """
    """
    fig, ax = pl.subplots(1, 1, figsize=(10, 6))
    # plot moon
    # mon_altitude = obs_site.moon_altaz(ing_egr).alt
    # ax.plot(ing_egr, moon_altitude, ls='--', label='Moon')

    # plot target
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
        name = f"ra, dec=({target_coord.to_string()})"

    if ephem_label is not None:
        name += f" @ {obs_site.name}, {ephem_label}"
    ax.set_title(name)
    if night_only:
        sunset = obs_site.sun_set_time(ing)
        sunrise = obs_site.sun_rise_time(egr)
        ax.set_xlim(sunset.datetime, sunrise.datetime)
    fig.tight_layout()
    return fig


def plot_partial_transit(
    midpoint,
    target_coord,
    obs_site,
    transit_duration=None,
    name=None,
    ephem_label=None,
    night_only=True,
):
    """
    transit_duration : float
        in days
    """
    fig, ax = pl.subplots(1, 1, figsize=(10, 6))
    if transit_duration is not None:
        ing = midpoint - dt.timedelta(days=transit_duration / 2)
        egr = midpoint + dt.timedelta(days=transit_duration / 2)
        sunset = obs_site.sun_set_time(ing)
        sunrise = obs_site.sun_rise_time(egr)
    else:
        sunset = obs_site.sun_set_time(midpoint)
        sunrise = obs_site.sun_rise_time(midpoint)
    _ = plot_altitude(
        targets=target_coord,
        observer=obs_site,
        time=midpoint.datetime,
        brightness_shading=True,
        airmass_yaxis=True,
        min_altitude=20,  # deg
        ax=ax,
    )

    ax.axhline(30, 0, 1, c="r", ls="--", label="limit")
    ax.axvline(midpoint.datetime, 0, 1, c="k", ls="-", label="mid")
    if transit_duration is not None:
        ax.axvline(ing.datetime, 0, 1, c="k", ls="--", label="ing/egr")
        ax.axvline(egr.datetime, 0, 1, c="k", ls="--", label="_nolegend_")
    if name is None:
        name = f"ra, dec=({target_coord.to_string()})"

    if ephem_label is not None:
        name += f" @ {obs_site.name}, {ephem_label}"
    ax.set_title(name)
    if night_only:
        ax.set_xlim(sunset.datetime, sunrise.datetime)
    fig.tight_layout()
    return fig


def get_above_lower_limit(lower, data_mu, data_sig, sigma=1):
    idx = norm.cdf(lower, loc=data_mu, scale=data_sig) < norm.cdf(sigma)
    return idx


def get_below_upper_limit(upper, data_mu, data_sig, sigma=1):
    idx = norm.cdf(upper, loc=data_mu, scale=data_sig) > norm.cdf(-sigma)
    return idx


def get_between_limits(lower, upper, data_mu, data_sig, sigma=1):
    """
    filter data between lower and upper limits
    """
    idx = get_above_lower_limit(
        lower, data_mu, data_sig, sigma=sigma
    ) & get_below_upper_limit(upper, data_mu, data_sig, sigma=sigma)
    return idx
