# mirai
transit ephemeris calculator
* main referece: [astroplan](https://astroplan.readthedocs.io/en/latest/tutorials/periodic.html)
* see also: [NeXSci page](https://exoplanetarchive.ipac.caltech.edu/docs/transit_algorithms.html)

## example
```python
./mirai.py TOI460 2458411.065871 0.52 0.9333 2019-01-01 2019-02-23 -ra=47.643478 -dec=-9.27681 -site OAO
```

## Notes on the algorithm
* `next_primary_eclipse_time` method of `EclipsingSystem` class is used to compute the number of transit after a given epoch of periastron passage, where `n_eclipses`=100 by default. `n_eclipses` can be erroneously set to a small number which does not reach the specified `obs_end` e.g. computing 100 eclipses after given epoch may not be enough if the specified `end_date` is say longer than 1 year from specified epoch. Perhaps, `n_eclipses` should be increased when specified end date is longer than a few months from the given epoch.
* `obs_end` argument is only used to compare if the first observable primary transit happens before this date. 

## Notes on things to improve
* a file with input values should be read by a function that maps transit ephemerides to a given target
* batch script should be used to compute transit times of one object observable from several (default) observatories 