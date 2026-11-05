#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
if [ -x ./lib/ld-linux-x86-64.so.2 ] && [ -f ./lib/libc.so.6 ]; then
    LIB_DIR=./lib
else
    LIB_DIR=.
fi
exec "$LIB_DIR/ld-linux-x86-64.so.2" --library-path "$LIB_DIR" ./uaf
