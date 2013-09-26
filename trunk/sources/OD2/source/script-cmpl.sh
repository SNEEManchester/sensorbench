#!/bin/sh
#
# This script creates the necessary nodes
#

# For the D3 case, the script is run for every D3Node*.h file
cnt=`ls D3Node*.h | wc -l`;

#The target can be either mica2 or micaz
trg=micaz;

i=0;

while [ true ];
do
	cp "D3Node"$i".h" D3.h;
	SENSORBOARD=mts300 make $trg;
	cp build/$trg/main.exe mote"$i".elf;
	rm -rf build/;
	i=`expr $i + 1`;

	if [ $i -ge $cnt ] ;
	then
		break;
	fi
done	



