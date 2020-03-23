#!/usr/bin/sh

echo "TEST0: Southern target not observable in OT"
mirai toi200.01 -v -n
echo

echo "TEST1: Observable in OT from June"
mirai toi1497.01 -v -n
echo

echo "TEST2: Use ephem of 2nd candidate in toi1726 using TIC"
mirai tic130181866.02 -site=AAO -v -n
echo

echo "TEST3: community TOI"
mirai ctoi25314899.01 -v -n
echo

echo "TEST4: specify ephem"
mirai wasp-127 -v -n -per=4.178062 -t0=2457248.74131 -dur=0.1795 #TODO: query ephem from nexsci
echo

echo "TEST5: change site"
mirai toi200.01 -site=SAAO -v -n #TODO: expand list +LCO
echo

echo "TEST6: find all transits between specified times"
mirai toi200.01 -site=SAAO -v -n -s -d1=2020-05-1 -d2=2020-06-1
echo

echo "TEST7: plot and figure+csv"
mirai tic130181866.02 -site=AAO -v -n -p -s
echo
