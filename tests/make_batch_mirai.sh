
#!/usr/bin/sh

name='toi'
fp='all_'$name's'
#start_date='2020-03-20 12:00'
end_date='2020-03-26 12:00'
lt2='23:59' #first half night only
site='tno'

cat $fp.txt | while read toi; do echo mirai $name-$toi -v -s -o $fp -site $site -s -lt2 $lt2 -dt2 $end_date; done > $fp.batch
echo "Check: cat $fp.batch"
echo "Run: cat $fp.batch | parallel"
