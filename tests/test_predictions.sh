#!/usr/bin/sh

echo "TEST0: Southern target is not observable in OT (throws an error)"
cmd="mirai toi200.01 -v -n"
echo $cmd
$cmd
echo

echo "TEST1: Target is observable in OT from June"
cmd="mirai toi1497.01 -v -n"
echo $cmd
$cmd
echo

echo "TEST2: Use ephem of 2nd candidate in toi1726 using TIC"
cmd="mirai tic130181866.02 -site AAO -v -n"
echo $cmd
$cmd
echo

echo "TEST3: community TOI"
cmd="mirai ctoi25314899.01 -v -n"
echo $cmd
$cmd
echo

echo "TEST4: specify ephem"
cmd="mirai wasp-127 -v -n -per 4.178062 -t0 2457248.74131 -dur 0.1795" #TODO: query ephem from nexsci
echo $cmd
$cmd
echo

echo "TEST5: change site"
cmd="mirai toi200.01 -site SAAO -v -n" #TODO: expand list +LCO
echo $cmd
$cmd
echo

echo "TEST6: find all transits between specified times"
cmd="mirai toi200.01 -site SAAO -v -n -s -dt1 2020-05-1 12:00 -dt2 2020-06-1 17:00"
echo $cmd
$cmd
echo

echo "TEST7: plot and save figure+csv"
cmd="mirai tic130181866.02 -site AAO -v -n -p -s"
echo $cmd
$cmd
echo
