# mirai
transit ephemeris calculator
* main referece: [astroplan](https://astroplan.readthedocs.io/en/latest/tutorials/periodic.html)
* see also: [NeXSci page](https://exoplanetarchive.ipac.caltech.edu/docs/transit_algorithms.html)

## installation
```shell
$ git clone https://github.com/jpdeleon/mirai.git
$ cd mirai && python setup.py install
$ python setup.py develop
```

## examples
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
* apply quick for observability e.g. dec cut
* add details e.g. airmass, local time in csv
* expand lists of sites: +LCO
* add Moon, local time, grid to see time gradations, and more airmass ticks in plot
* compare predictions against TTF or nexsci tool
* incorporate uncertainties
* query ephem from nexsci
* include partial transits
* add a function that reads an input file

## Notes on the algorithm
* Given ticid, first mirai checks if it is a toi or ctoi, else ephemeris is asked (check `get_t0_per_dur`)
* `EclipsingSystem.next_primary_eclipse_time` is used to compute the number of transit with `n_eclipses`=100 by default. `n_eclipses` can be erroneously set to a small number which does not reach the specified `obs_end` e.g. computing 100 eclipses may not be enough if the specified end date is say longer than 1 year from specified epoch. Perhaps, `n_eclipses` should be increased when specified end date is longer than a few months from the given epoch.
* `obs_end` argument is used to compare if the first observable primary transit happens before this date and discards all observable events after this date
