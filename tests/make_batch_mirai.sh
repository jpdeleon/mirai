#!/usr/bin/sh

name='ctoi'
fp='usp_'$name's'
#start_date='2020-03-20 12:00'
end_date='2020-03-28 12:00'
site='tno'


cat $fp.txt | while read toi; do echo mirai $name-$toi -v -s -o $fp -site $site -s -dt2 $end_date; done > $fp.batch
echo "Check: cat $fp.batch"
echo "Run: cat $fp.batch | parallel"
