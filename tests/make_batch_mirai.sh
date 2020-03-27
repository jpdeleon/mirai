#!/usr/bin/sh

prefix='usp'
type='toi'
infp=$prefix'_'$type's' #e.g. all_tois
start_date='2020-06-1 00:01'
end_date='2020-11-30 23:59'
#lt1='23:59' #second half night only
#lt2='23:59' #first half night only
site='wise'
outdir=$infp'_from_'$site
outfp=$outdir'.batch'
cat $infp.txt | while read toi; do echo mirai $type-$toi -v -s -o $outdir -site $site -dt1 $start_date -dt2 $end_date; done > $outfp
echo "Check: cat $outfp"
echo "Run: cat $outfp | parallel"
