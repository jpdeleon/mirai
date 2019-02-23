#!/usr/bin/env python
"""
Transit and ephemeris calculator

Note: eclipse times are computed without any barycentric corrections
"""

from os.path import join, exists
import sys
import time
import datetime as dt
import numpy as np
import argparse
import subprocess
import matplotlib.pyplot as pl

from astroquery.exoplanet_orbit_database import ExoplanetOrbitDatabase
from astroplan import FixedTarget, Observer, EclipsingSystem
from astroplan.plots import plot_airmass
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as u
from astroplan import download_IERS_A

from astroplan import (PrimaryEclipseConstraint, MoonSeparationConstraint,
                       is_event_observable, is_always_observable, months_observable,
                       AtNightConstraint, AltitudeConstraint, LocalTimeConstraint,
                       AirmassConstraint)

import k2plr
client = k2plr.API()

#lat,lon, elev, local timezone
#to see all timezones: import pytz; print(pytz.all_timezones)
SITES = {'OAO': (34.5761, 133.5941, 343, "Asia/Tokyo"),
         'TCS': (28.291, 343.5033, 2395, "UTC"), 
         'SBO': (-31.2733, 149.0617, 1145, "Australia/Queensland"), #siding spring observatory
         'TRO': (-30.1692, -70.805, 2286, "America/Santiago"), #cerro tololo observatory
         'TNO': (111, 111, 0, "Asia/Thailand") #
        }

def get_ra_dec(epicnum,verbose=False):
    '''
    get ra, dec, and mag using `k2plr`
    '''
    if verbose:
        print('\nquerying RA and DEC...\n')
    epic = client.k2_star(int(epicnum))
    ra  = float(epic.k2_ra)
    dec = float(epic.k2_dec)
    #mag = float(epic.kp)
    return ra, dec

if __name__ == '__main__':
    arg = argparse.ArgumentParser(description='set-up target and observation settings')
    arg.add_argument('name', help='target name', type=str)
    arg.add_argument('-ra', '--target_ra', help='target RA [deg]', type=float)
    arg.add_argument('-dec', '--target_dec', help='target Dec [deg]', type=float)
    arg.add_argument('t0', help='epoch of periastron passage [JD]', type=float)
    arg.add_argument('per', help='orbital period [d]', type=float)
    arg.add_argument('dur', help='transit duration [d]', type=float)
    
    arg.add_argument('-n', '--ntransit', help='number of next primary transit to compute (default=100)', 
                     type=int, default=100)
    arg.add_argument('-e', '--exclude_partial_transit', help='exclude partial transit (default=False)', 
                     action='store_true', default=False)
    #obs parameters
    arg.add_argument('start_date', help='start date of observation [UT] e.g. 2019-02-17', type=str)
    arg.add_argument('--start_time', help='start time of observation [UT] (default=19:00)', default='19:00', type=str)
    arg.add_argument('end_date', help='end date of observation [UT] e.g. 2019-03-17', type=str)
    arg.add_argument('--end_time', help='end time of observation [UT] (default=06:00)', default='06:00', type=str)
    
    arg.add_argument('-site', '--obs_site_name', help='observation site name (default TRO)', type=str, default='TRO')
    arg.add_argument('-tz', '--timezone', help='time zone', type=str, default='UTC')
    arg.add_argument('-lt', '--use_local_timezone', help='use local time zone', action='store_true', default=False)
    arg.add_argument('-lat', '--site_lat', help='custom site latitude [deg]', type=float, default=None)
    arg.add_argument('-lon', '--site_lon', help='custom site longitude [deg]', type=float, default=None)
    arg.add_argument('-elev', '--site_elev', help='custom site elevation [m]', type=float, default=None)
    #constraints
    arg.add_argument('-alt', '--alt_limit', help='target altitude limit [deg]', type=float, default=30)
    arg.add_argument('-sep', '--min_moon_sep', help='moon separation limit [deg]', type=float, default=10)
    #miscellaneous
    arg.add_argument('-p', '--plot_target', 
                     help='plot airmass and altitude of target on first observable date', 
                     action='store_true', default=False)
    arg.add_argument('-u', '--update_db', help='update IERS database', action='store_true', default=False)
    
    args      = arg.parse_args()    
    n_transits  = args.ntransit
    exclude_partial_transit = args.exclude_partial_transit
    plot_target= args.plot_target
    
    if args.update_db:
        download_IERS_A()
    
    #transit params
    targetname= args.name
    target_RA = args.target_ra
    target_Dec= args.target_dec
    epoch     = args.t0
    period    = args.per
    duration  = args.dur
    
    #set-up transit parameters
    primary_eclipse_time = Time(epoch, format='jd')
    orbital_period = period * u.day  
    transit_duration = duration * u.day
        
    #obs params
    obs_time1 = ' '.join((args.start_date, args.start_time))
    obs_time2   = ' '.join((args.end_date, args.end_time))
    obs_start = Time(obs_time1)
    obs_end   = Time(obs_time2)
    sitename  = args.obs_site_name
    timezone  = args.timezone
    use_local_timezone = args.use_local_timezone
    
    site_lat  = args.site_lat
    site_lon  = args.site_lon
    site_elev = args.site_elev
    
    #set-up obs constraints
    min_local_time = dt.time(19, 0)  # 7:00 pm local time 
    max_local_time = dt.time(7, 0)   # 6:00 am local time
    target_altitude_limit = args.alt_limit
    min_moon_sep   = args.min_moon_sep
    
    #see https://astroplan.readthedocs.io/en/latest/tutorials/constraints.html
    constraints = [AtNightConstraint.twilight_civil(),
               AltitudeConstraint(min=target_altitude_limit*u.deg),
               LocalTimeConstraint(min=min_local_time, max=max_local_time),
               MoonSeparationConstraint(min=min_moon_sep*u.deg)]

    if np.all([target_RA, target_Dec]):
        target_coord = SkyCoord(ra=target_RA*u.deg, dec=target_Dec*u.deg)
        targetloc = FixedTarget(target_coord, targetname)
    else:
        #query ra and dec given name
        targetloc = FixedTarget.from_name(targetname)

    #set-up observation parameters
    if sitename in list(SITES.keys()):
        #use any of the 5 default obs sites
        lat,lon,elev,local_timezone = SITES[sitename]
        if use_local_timezone:
            print('timezone: {}'.format(local_timezone))
            observatory_site = Observer(latitude=lat*u.deg, longitude=lon*u.deg,
                      elevation=elev*u.m, name=sitename, timezone=local_timezone)
        else:
            print('timezone: {}'.format(timezone))
            observatory_site = Observer(latitude=lat*u.deg, longitude=lon*u.deg,
                      elevation=elev*u.m, name=sitename, timezone=timezone)
    elif np.all([site_lat,site_lon,site_elev,timezone]):
        #use custom site location
        print('timezone: {}'.format(timezone))
        observatory_site = Observer(latitude=site_lat*u.deg, longitude=site_lon*u.deg,
                      elevation=site_elev*u.m, name=sitename, timezone=timezone)
    else: 
        #query known sites
        print('timezone: {}'.format(timezone))
        observatory_site = Observer.at_site(sitename, timezone=timezone)

    ###
    ephemeris = EclipsingSystem(primary_eclipse_time=primary_eclipse_time,
                                orbital_period=orbital_period, 
                                duration=transit_duration,
                                name=targetname+' b')
    
    if exclude_partial_transit:
        #FIXME: why next_primary_ingress_egress_time does not accept obs_end?
        ing_egr_times = ephemeris.next_primary_ingress_egress_time(obs_start, 
                                                                   n_eclipses=n_transits)
        idx1 = is_event_observable(constraints, 
                              observatory_site, 
                              targetloc,  
                              times_ingress_egress=ing_egr_times)[0]
        #check if computed time does not exceed the specified obs_end
        idx2 = [True if egr<obs_end else False for ing,egr in ing_egr_times[idx1]]
        partial_events = ing_egr_times[idx1][idx2].iso
        nobs = len(partial_events)
        
        if np.any(idx1):
            #in case any predicted transit is observable, 
            #take first date and compare to specified end of observation
            ing,egr=ing_egr_times[idx1][0]
            if egr > obs_end:
                print('{}: Next observable event from {} is on {}'
                      .format(targetname, sitename, time))
            else:
                print('{}: {} Observable full transits from {} between {} & {}\n{}'
                      .format(targetname, nobs, sitename, obs_time1, obs_time2, partial_events))
        else:
            print('{}: No observable full transit from {} between {} & {}'
                  .format(targetname, sitename, obs_time1, obs_time2))
    else:
        #FIXME: why next_primary_eclipse_time does not accept obs_end?
        midtransit_times = ephemeris.next_primary_eclipse_time(obs_start, 
                                                               n_eclipses=n_transits)
        idx1 = is_event_observable(constraints, 
                              observatory_site, 
                              targetloc, 
                              times=midtransit_times)[0]
        #check if computed time does not exceed the specified obs_end
        idx2 = [True if mid<obs_end else False for mid in midtransit_times[idx1]]
        full_events = midtransit_times[idx1][idx2].iso
        nobs = len(full_events)
        
        if np.any(idx1):
            time=midtransit_times[idx1][0]
            if time > obs_end:
                print('{}: Next observable event from {} is on {}'
                      .format(targetname, sitename, time))
            else:
                print('{}: {} Observable partial transits from {} between {} & {}\n{}'
                      .format(targetname, nobs, sitename, obs_time1, obs_time2, full_events))
        else:
            print('{}: No observable partial transit from {} between {} & {}'
                  .format(targetname, sitename, obs_time1, obs_time2))
    
#         if plot_target:
#             plot_airmass(targetloc, 
#                  observatory_site, 
#                  time, 
#                  brightness_shading=True, 
#                  altitude_yaxis=True)
#             pl.show()
