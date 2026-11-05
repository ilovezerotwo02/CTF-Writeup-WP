#!/bin/bash
DIR=$(dirname "$0")
exec "$DIR/debextract/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2" --library-path "$DIR/debextract/lib/x86_64-linux-gnu" "$DIR/combination_final" "$@"
