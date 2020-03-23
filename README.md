# mirai
transit ephemeris calculator
* main referece: [astroplan](https://astroplan.readthedocs.io/en/latest/tutorials/periodic.html)
* see also: [NeXSci page](https://exoplanetarchive.ipac.caltech.edu/docs/transit_algorithms.html)

## example
```shell
#find next transit @ OT(default)
$ mirai toi1497.01 -v -n
$ mirai tic130181866.02 -site AAO -v -n #toi1726 multi-planet
$ mirai ctoi25314899.01 -v -n #community TOI

#specify ephem
$ mirai wasp-127 -v -n -per 4.178062 -t0 2457248.74131 -dur 0.1795

#change site
$ mirai toi200.01 -site SAAO -v -n

# find all transits between specified times
$ mirai toi200.01 -site SAAO -v -n -s -dt1 2020-05-1 12:00 -dt2 2020-06-1 17:00

# add -p to plot and -s to save figure+csv
$ mirai tic130181866.02 -site AAO -v -n -p -s
```

## Issues/ TODO
* use twilight
* apply easy check for observability e.g. dec cut
* use pandas
* given tic, check toi then ctoi, else ephem
* add airmass, etc
* add Moon
* needs further tests (see tests/); compare with nexsci tool
* incorporate uncertainties
* expand lists of sites: +LCO
* query ephem from nexsci
* include partial transits
* a file with input values should be read by a function that maps transit ephemerides to a given target
* batch script should be used to compute transit times of one object observable from several (default) observatories

## Notes on the algorithm
* `next_primary_eclipse_time` method of `EclipsingSystem` class is used to compute the number of transit after a given epoch of periastron passage, where `n_eclipses`=100 by default. `n_eclipses` can be erroneously set to a small number which does not reach the specified `obs_end` e.g. computing 100 eclipses may not be enough if the specified end date is say longer than 1 year from specified epoch. Perhaps, `n_eclipses` should be increased when specified end date is longer than a few months from the given epoch.
* `obs_end` argument is used to compare if the first observable primary transit happens before this date and discards all observable events after this date
