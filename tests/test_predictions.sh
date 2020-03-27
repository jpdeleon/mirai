#!/usr/bin/sh
# List of exceptions:
# tic232650365 seems unobservable in north

southern="toi200.01"
tic2toi="tic154872375" #tic that is also a toi
tic2ctoi="tic364395234" #tic that is also a ctoi
usp="toi1729.01"
shortperiod="toi764.01" #4 d
mediumperiod="toi1141.01" #16 d
longperiod="toi1229.01" #30 d
shortduration="toi1681.01" #0.8 hr
mediumduration="toi1406.01" #4 hr
longduration="toi791.01" #12 h; only partial
multi="toi1749.02"


echo "TEST: Southern target is not observable in OT (throws an error)"
cmd="mirai $southern -v -n"
echo $cmd
$cmd
echo

echo "TEST: Southern target observable from SAAO"
cmd="mirai $southern -v -n -site SAAO"
echo $cmd
$cmd
echo


echo "TEST: Target is observable in OT from June"
cmd="mirai $multi -v -n"
echo $cmd
$cmd
echo

echo "TEST: Long duration target shows only partial transits"
cmd="mirai $longduration -site SAAO -v -n"
echo $cmd
$cmd
echo

echo "TEST: TIC using TOI ephemeris"
cmd="mirai $tic2toi -v -n"
echo $cmd
$cmd
echo

echo "TEST: TIC using community TOI (ctoi) ephemeris"
cmd="mirai $tic2ctoi -v -n -site AAO"
echo $cmd
$cmd
echo

echo "TEST: Specified ephemeris"
cmd="mirai wasp-127 -v -n -per 4.178062 -t0 2457248.74131 -dur 0.1795" #TODO: query ephem from nexsci
echo $cmd
$cmd
echo


echo "TEST: Find all transits between specified times"
cmd="mirai toi200.01 -site SAAO -v -n -dt1 2020-05-1 12:00 -dt2 2020-06-1 17:00"
echo $cmd
$cmd
echo

echo "TEST: First half night"
cmd="mirai $usp -v -n -lt2 23:59"
echo $cmd
$cmd
echo

echo "TEST: Second half night"
cmd="mirai $usp -v -n -lt1 00:01"
echo $cmd
$cmd
echo

echo "TEST: plot and save figure+csv"
cmd="mirai toi837.01 -site AAO -v -n -p -s"
echo $cmd
$cmd
echo
