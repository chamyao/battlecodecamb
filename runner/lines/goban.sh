# runner/lines/goban.sh: train Cham's Go network (goban-trainer, tools/ownnet) on this box, then stop.
# Idempotent (tick.sh runs it every 5 min): set up once, start training if it isn't running and isn't done,
# push the log and checkpoints to remote/goban. Public inputs only: the code and the starting checkpoint come from
# github.com/chamyao/goban-trainer (public), the game archives from u-go.net and homepages.cwi.nl. No secrets used.
# Done when step 80000 is logged: the script then only pushes the final state.
# Added by Cham's go-ahead (Nov 22 2026); disable by renaming to goban.sh.off.
unset FUNSEARCH_API_KEY   # lib.sh exports it; this line needs no secrets, keep it out of the Go processes
D=/root/bc/goban; mkdir -p "$D"; cd "$D" || exit 0
STEPS=80000

# 1. once: Python with CPU PyTorch, the code, the starting checkpoint
if [ ! -f .setup-done ]; then
  log "setup: python env"
  apt-get install -y -q python3-venv > /dev/null 2>&1
  python3 -m venv venv && venv/bin/python3 -m pip install -q numpy && \
    venv/bin/python3 -m pip install -q torch --index-url https://download.pytorch.org/whl/cpu || { log "setup: pip failed"; exit 0; }
  rm -rf code ck && git clone -q --depth 1 https://github.com/chamyao/goban-trainer code && \
    git clone -q --depth 1 --branch ownnet-checkpoints https://github.com/chamyao/goban-trainer ck || { log "setup: clone failed"; exit 0; }
  cp code/tools/ownnet/{prep.py,train.py,merge.py,export.py} . && mkdir -p run1 && cp ck/run1/full/latest.pt run1/start.pt
  touch .setup-done; log "setup done; starting from $(cat ck/run1/full/latest.txt)"
fi

# 2. once: the training data, rebuilt from the same archives and settings (row order may differ: prep.py's pool)
if [ ! -f mix.npz ]; then
  if running "prep.py" || running "merge.py"; then exit 0; fi
  log "data: downloading and extracting"
  mkdir -p raw cwi
  for f in 2014-19-13029- 2013-19-13783- 2012-19-13665- 2011-19-19099-; do
    [ -f raw/KGS-$f.tar.bz2 ] || curl -sSfL -o raw/KGS-$f.tar.bz2 https://dl.u-go.net/gamerecords/KGS-$f.tar.bz2
    tar xjf raw/KGS-$f.tar.bz2 -C raw
  done
  [ -f cwi.tgz ] || curl -sSfL -o cwi.tgz https://homepages.cwi.nl/~aeb/go/games/games.tgz
  tar xzf cwi.tgz -C cwi
  sed -i 's/Pool(4)/Pool(16)/' prep.py
  nohup sh -c "venv/bin/python3 prep.py kgs.npz raw 0.5 && venv/bin/python3 prep.py cwi.npz cwi 0.3 && venv/bin/python3 merge.py kgs.npz cwi.npz mix.npz.tmp.npz && mv mix.npz.tmp.npz mix.npz" > data.log 2>&1 &
  exit 0
fi

# 3. once: bfloat16 or float32, whichever trains faster on this CPU (AMD: no AMX, so not obvious)
if [ ! -f mode ]; then
  venv/bin/python3 - > bench.log 2>&1 <<'PY'
import time, torch, train
torch.set_num_threads(16)
net = train.Net(6, 64); opt = torch.optim.SGD(net.parameters(), lr=0.01, momentum=0.9)
x = torch.randn(256, 17, 19, 19); y = torch.randint(0, 362, (256,))
def rate(bf):
    m = net.to(memory_format=torch.channels_last) if bf else net
    xx = x.contiguous(memory_format=torch.channels_last) if bf else x
    t = time.time(); k = 0
    while time.time() - t < 30:
        with torch.autocast("cpu", dtype=torch.bfloat16, enabled=bf): p, _ = m(xx)
        l = torch.nn.functional.cross_entropy(p.float(), y); opt.zero_grad(); l.backward(); opt.step(); k += 1
    return k * 256 / (time.time() - t)
a, b = rate(False), rate(True); print(f"fp32 {a:.0f} bf16 {b:.0f} positions/s")
open("mode", "w").write("--bf16" if b > a else "")
PY
  log "bench: $(tail -1 bench.log); mode '$(cat mode)'"
fi

# 4. train (resume from the newest checkpoint here, else the start checkpoint)
last=$(grep -o "^step [0-9]*" run1.log 2>/dev/null | tail -1 | cut -d' ' -f2)
if [ "${last:-0}" -lt "$STEPS" ] && ! running "train.py mix.npz"; then
  ck=$(ls run1/m*.pt 2>/dev/null | tail -1); ck=${ck:-run1/start.pt}
  log "training: resume from $ck"
  nohup venv/bin/python3 train.py mix.npz run1 --blocks 6 --ch 64 --steps $STEPS --batch 256 --every 500 --threads 16 $(cat mode) --resume "$ck" >> run1.log 2>&1 &
fi

# 5. state to remote/goban: the logs, and the newest checkpoint (full, to resume from) plus every 2,500th exported
mkdir -p out; cp run1.log out/ 2>/dev/null; cp run1/log.jsonl out/ 2>/dev/null; cp bench.log data.log out/ 2>/dev/null
n=$(ls run1/m*.pt 2>/dev/null | tail -1)
if [ -n "$n" ]; then
  # the full checkpoint only at each 2,500th step (9 MB a commit; the box itself resumes from run1/)
  s=$(basename "$n" .pt); s=$((10#${s#m})); [ $((s % 2500)) -eq 0 ] && { cp "$n" out/latest.pt; basename "$n" > out/latest.txt; }
  for f in run1/m*.pt; do s=$(basename "$f" .pt); s=$((10#${s#m})); [ $((s % 2500)) -eq 0 ] || continue
    [ -f out/m$(printf %07d $s).bin ] || venv/bin/python3 export.py "$f" out/m$(printf %07d $s).bin > /dev/null 2>&1; done
fi
push_state remote/goban run1 out "goban: step $(grep -o '^step [0-9]*' run1.log 2>/dev/null | tail -1 | cut -d' ' -f2) $(date -u +%H:%M) UTC"
[ "${last:-0}" -ge "$STEPS" ] && log "done: step $last"; true
