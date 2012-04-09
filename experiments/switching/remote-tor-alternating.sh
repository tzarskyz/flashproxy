#!/bin/bash

# Usage: ./remote-tor-alternating.sh [OUTPUT_FILENAME]
#
# Tests a Tor download over alternating flash proxies. If OUTPUT_FILENAME is
# supplied, appends the time measurement to that file.

. ../common.sh

PROFILE_1=flashexp1
PROFILE_2=flashexp2
PROXY_URL="http://127.0.0.1:8000/embed.html?facilitator=127.0.0.1:9002&ratelimit=off"
DATA_FILE_NAME="$FLASHPROXY_DIR/dump"
OUTPUT_FILENAME="$1"

# Declare an array.
declare -a PIDS_TO_KILL
stop() {
	browser_clear "$PROFILE_1"
	browser_clear "$PROFILE_2"
	if [ -n "${PIDS_TO_KILL[*]}" ]; then
		echo "Kill pids ${PIDS_TO_KILL[@]}."
		kill "${PIDS_TO_KILL[@]}"
	fi
	echo "Delete data file."
	rm -f "$DATA_FILE_NAME"
	exit
}
trap stop EXIT

echo "Start web server."
"$THTTPD" -D -d "$FLASHPROXY_DIR" -p 8000 &
PIDS_TO_KILL+=($!)

echo "Start facilitator."
"$FLASHPROXY_DIR"/facilitator.py -d --relay tor1.bamsoftware.com >/dev/null &
PIDS_TO_KILL+=($!)
visible_sleep 5

echo "Start connector."
"$FLASHPROXY_DIR"/connector.py >/dev/null &
PIDS_TO_KILL+=($!)
echo $'POST / HTTP/1.0\r\n\r\nclient=:9000' | socat - TCP-CONNECT:127.0.0.1:9002
visible_sleep 1

echo "Start Tor."
"$TOR" -f "$FLASHPROXY_DIR"/torrc &
PIDS_TO_KILL+=($!)

echo "Start browsers."
ensure_browser_started "$PROFILE_1"
ensure_browser_started "$PROFILE_2"

./proxy-loop.sh "$PROXY_URL" "$PROFILE_1" "$PROFILE_2" >/dev/null 2>&1  &
PIDS_TO_KILL+=($!)

# Let Tor bootstrap.
visible_sleep 15

repeat_download() {
	until torify wget http://torperf.torproject.org/.5mbfile --wait=0 --waitretry=0 -c -t 1000 -O "$DATA_FILE_NAME"; do
		echo "retrying"
	done
}

if [ -n "$OUTPUT_FILENAME" ]; then
	real_time repeat_download >> "$OUTPUT_FILENAME"
else
	real_time repeat_download
fi
