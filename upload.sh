#!/bin/bash

CHIP="esp32"
ROLE="server"

PORT="ttyUSB0"
EMIT="bytecode"
OPTF="-O3"

DO_FEECH=false
DO_FLASH=false
DO_REPL=false

IS_FIRST=true

while [ "$1" != "" ]; do

	PARAM=`echo $1 | awk -F= '{print $1}'`
	VALUE=`echo $1 | awk -F= '{print $2}'`

	case $PARAM in

		-p | --port)
			PORT=$VALUE
			;;

		-e | --emit)
			EMIT=$VALUE
			;;

		-d | --download)
			DO_FEECH=true
			;;

		-f | --flash)
			DO_FLASH=true
			;;

		-r | --repl)
			DO_REPL=true
			;;

		-s | --skip)
			ROLE="none"
			;;

		-g | --debug)
			OPTF="-O0"
			;;

	esac
	shift

done

if [ $DO_FEECH == true ]
then
	wget -qO- "https://code.jquery.com/jquery-1.11.1.min.js"                           | gzip --best > "arch/jquery.js.gz"
	wget -qO- "https://cdn.jsdelivr.net/npm/moment@2.30.1/moment.min.js"               | gzip --best > "arch/moment.js.gz"
	wget -qO- "https://cdn.jsdelivr.net/npm/moment@2.30.1/locale/pl.min.js"            | gzip --best > "arch/moment.pl.js.gz"
	wget -qO- "https://cdn.jsdelivr.net/npm/chart.js@2.9.4"                            | gzip --best > "arch/chart.js.gz"
	wget -qO- "https://cdn.jsdelivr.net/npm/hammerjs@2.0.8"                            | gzip --best > "arch/hammer.js.gz"
	wget -qO- "https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@0.7.7"                 | gzip --best > "arch/chart.zoom.js.gz"
	wget -qO- "https://cdn.jsdelivr.net/npm/codemirror@5.65.21/lib/codemirror.min.js"  | gzip --best > "arch/codemirror.js.gz"
	wget -qO- "https://cdn.jsdelivr.net/npm/codemirror@5.65.21/lib/codemirror.min.css" | gzip --best > "arch/codemirror.css.gz"
fi

if [ $DO_FLASH == true ]
then
	esptool --chip esp32 --port "/dev/$PORT" erase-flash
	sleep 1s
	esptool --chip esp32 --port "/dev/$PORT" --baud 460800 write-flash --flash-size=detect -z 0x1000 esp32.bin
fi

for f in lib/*.py
do
	mpy-cross "$OPTF" -march=xtensawin -X emit="$EMIT" "$f"
done

printf "{\n" > etc/etags.json

for f in obj/*.ico arch/*.gz http/*.html css/*.css src/*.js
do
	if [ $IS_FIRST == true ]; then IS_FIRST=false; else printf ',\n' >> etc/etags.json; fi
	printf '\t"%s": "%s"' $(basename "$f") $(cksum "$f" | awk '{print $1}') >> etc/etags.json
done

printf "\n}" >> etc/etags.json

if [ "$ROLE" == "server" ]
then
	mpfshell "$PORT" -s upload.mpf
fi

if [ $DO_REPL == true ]
then
	mpfshell "$PORT" -c repl
fi

rm -f lib/*.mpy
