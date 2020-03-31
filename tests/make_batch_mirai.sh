#!/usr/bin/sh

prefix='all'
type='toi'
infp=$prefix'_'$type's' #e.g. all_tois
#start_date='2020-06-01 00:01'
#end_date='2020-11-30 23:59'
start_date='2020-03-31 00:01'
end_date='2020-04-30 23:59'
#lt1='23:59' #second half night only
lt2='23:59' #first half night only
site='tno'
outdir=$infp'_from_'$site
outfp=$outdir'.batch'
cat $infp.txt | while read toi; do echo mirai $type-$toi -v -s -o $outdir -site $site -dt1 $start_date -dt2 $end_date -lt2 $lt2; done > $outfp
echo "Check: cat $outfp"
echo "Run: cat $outfp | parallel 2>&1 | tee $outdir.log"
