#!/usr/bin/env/sh
ifp="pathos-tic.txt"
ofp="pathos-tic.batch"
#awk -F"," '{print $1}' $ifp
cat $ifp | while read target; do echo mirai tic$target -dt1 2020-07-01 00:01 -dt2 2021-01-31 23:59 -v -s -fp targets.csv; done > $ofp
echo 'check: cat '$ofp
echo 'run: cat $ofp | parallel 2>&1 | tee '$ofp'.log'

