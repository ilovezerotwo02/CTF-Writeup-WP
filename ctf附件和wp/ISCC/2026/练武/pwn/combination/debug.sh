#!/bin/bash
DIR=$(dirname "$0")
exec gdb -q \
  -ex "set exec-wrapper env LD_PRELOAD=''\ \"$DIR/debextract/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2\"\ --library-path\ \"$DIR/debextract/lib/x86_64-linux-gnu\"" \
  -ex "set sysroot" \
  -ex "set disable-randomization on" \
  -ex "checksec" \
  "$DIR/combination_final"
