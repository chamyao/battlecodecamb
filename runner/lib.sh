# Helpers for line scripts. Sourced by tick.sh; cwd is /root/bc.
REPO=https://github.com/chamyao/battlecodecamb
export HOME=/root PYTHONUNBUFFERED=1
set -a; . /root/.funsearch.env; set +a        # FUNSEARCH_API_KEY (never echo it)

log() { echo "[$(date -u +%H:%M:%S)] $LINE: $*"; echo "FSB|$LINE: $*" > /dev/ttyS0 2>/dev/null; }

# running <pattern>: is a python3 process whose command line contains <pattern> alive?
# (pgrep -f would match this shell's own command line; filter python3 processes only)
running() { pgrep -a -x python3 | grep -qF -- "$1"; }

# build <dir> [targets...]: Release build of interp_eval (and extra targets) once per checkout commit
build() {
  local d=$1; shift; local rev; rev=$(git -C "$d" rev-parse HEAD)
  [ -f "$d/interp/build/.built-$rev" ] && return 0
  cmake -S "$d/interp" -B "$d/interp/build" -DCMAKE_BUILD_TYPE=Release > /dev/null &&
    cmake --build "$d/interp/build" -j16 --target interp_eval "$@" > "$d/interp/build/build.log" 2>&1 &&
    touch "$d/interp/build/.built-$rev"
}

# push_state <branch> <dest dir in branch> <src dir> [commit message]
# Copies src into a clone of <branch> under <dest>, commits if anything changed, pushes.
push_state() {
  local br=$1 dst=$2 src=$3 msg=${4:-}
  local wt=/root/bc/state/${br//\//_}
  if [ ! -d "$wt/.git" ]; then
    git clone -q --single-branch --branch "$br" "$REPO" "$wt" 2>/dev/null ||
      { git init -q "$wt" && git -C "$wt" checkout -q --orphan "$br" && git -C "$wt" remote add origin "$REPO"; }
  fi
  git -C "$wt" fetch -q origin "$br" 2>/dev/null && git -C "$wt" reset -q --hard "origin/$br"
  mkdir -p "$wt/$dst"
  cp -a "$src/." "$wt/$dst/"
  git -C "$wt" add -A -f "$dst"
  git -C "$wt" diff --cached --quiet && return 0
  git -C "$wt" -c user.name="ec2-runner" -c user.email="ec2-runner@users.noreply.github.com" \
    commit -q -m "${msg:-$br: ec2 state $(date -u +%H:%M) UTC}"
  for i in 1 2 3; do git -C "$wt" push -q origin "HEAD:$br" && return 0; sleep $((i * 5));
    git -C "$wt" pull -q --rebase origin "$br"; done
  log "push to $br failed"
}

# clone_nopush <branch-or-commit> <dir>: working clone whose own pushes are disabled (the leagues' built-in
# `git push origin HEAD` must not reach funsearch/*; state goes out only through push_state)
clone_nopush() {
  rm -rf "$2" && git clone -q "$REPO" "$2" && git -C "$2" checkout -q "$1" &&
    git -C "$2" remote set-url --push origin DISABLED-by-ec2-runner
}
