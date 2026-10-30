cd ~/a10w
for f in "$@"; do echo -n "$(basename $f) "; python3 tools/screen.py $f v33 --tag exp | cut -c1-30; done
