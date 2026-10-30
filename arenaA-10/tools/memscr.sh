cd ~/a10w
for n in "$@"; do echo -n "$n "; python3 tools/screen.py $n v33 --tag member | cut -c1-30; done
