#!/bin/bash
# real_gate.sh CAND_BOT REF_BOT [JOBS]: ladder gate parts (b) and (c) in real cambc.
# Both bots must already be built under ~/ws/bots (genome/bot/sync.sh, bot/sync.sh).
# Plays all 40 maps x both sides (--release, as on the platform), then reports
# CAND's wins out of 80 (bar: >= 42) and per-bot safety: crashes (the bar), and for the record the first
# turns' max fuel and capped normal turns.
set -u
cand=$1; ref=$2; jobs=${3:-4}
repo=/home/user/battlecodecamb
out=${OUT:-$repo/genome/arenab/runs/$cand-vs-$ref}
mkdir -p "$out"; out=$(cd "$out" && pwd); rm -f "$out"/*.repl26a "$out"/manifest.txt
for m in "$repo"/maps/*.map26a; do
  cp -n "$m" ~/ws/maps/ 2>/dev/null
  n=$(basename "$m" .map26a)
  echo "$HOME/ws/bots/$cand $HOME/ws/bots/$ref $HOME/ws/maps/$n.map26a $out/A-$n.repl26a" >> "$out/manifest.txt"
  echo "$HOME/ws/bots/$ref $HOME/ws/bots/$cand $HOME/ws/maps/$n.map26a $out/B-$n.repl26a" >> "$out/manifest.txt"
done
(cd ~/ws && cambc run-batch --release --jobs "$jobs" --timeout 1800 "$out/manifest.txt") > "$out/batch.log" 2>&1
python3 "$repo/genome/arenab/gate_report.py" "$out" "$cand" "$ref" | tee "$out/report.txt"
