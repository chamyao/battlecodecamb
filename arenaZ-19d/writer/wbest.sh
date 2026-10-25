#!/bin/bash
for s in "$@"; do b=$(cat ~/w/d/$s.best) && cp "$b" ~/w/d/$s.txt && python3 ~/w/val.py $s ~/w/d/$s.txt --write 2>&1 | tail -1; done
