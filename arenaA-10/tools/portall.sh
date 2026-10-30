cd ~/a10w
for n in "$@"; do
  python3 tools/port.py runs/arenaA-10/arena/genomes/$n.genome ports/$n.genome >/dev/null 2>&1 || { echo "$n port failed"; continue; }
  echo -n "$n "; python3 tools/screen.py ports/$n.genome v33 --tag portall | cut -c1-40
done
