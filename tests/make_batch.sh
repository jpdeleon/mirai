fp='subneptune'
cat $fp.txt | while read toi; do echo mirai TOI$toi -v -s -o $fp -site TNO -s -dt2 2020-03-28 12:00; done > $fp.batch
echo "cat $fp.batch | parallel "
