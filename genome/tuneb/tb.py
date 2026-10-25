"""Tune-B harness: variants of the live genome by text edits, scored with genome_eval.

Runtime: genome/v0 568cbf5 (runtime identical through 67c2d5a) (built genome/build/genome_eval). Opponents: genome/tuneb/opp (stress genomes from
genome/intel), policies compiled into genome/build/tuneb/*.pol.
"""
import glob, hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL = os.path.join(ROOT, 'genome', 'build', 'genome_eval')
EVAL_ECON = os.path.join(ROOT, 'genome', 'build_econ', 'genome_eval')  # with the spent / held checkpoint fields
VAR = os.path.join(ROOT, 'genome', 'build', 'tuneb', 'var')
POL = os.path.join(ROOT, 'genome', 'build', 'tuneb')
MAPS = sorted(glob.glob(os.path.join(ROOT, 'maps', '*.map26a')))
# the reference (live / next-upload) genome; TB_BASE overrides. History: v28 a61188-mono, v29 v28-emblem,
# v30 A81582-ringheal, v31 A81582-rh-mono-all, v32 B1873, v33 B1873-bossbush (Oct 25 08:36Z).
BASE = os.environ.get('TB_BASE') or os.path.join(ROOT, 'genome', 'candidates', 'B1873-bossbush.genome')

CHAMPS = ['RYTH', 'VESPER_VALE', 'VENDETTA', 'CASSI', 'STELLAR', 'PRISM', 'MARCELLA', 'WILLOW', 'REN', 'VARG',
          'TAVI', 'HEART_OF_RUIN']

ANCHORS = {
    'farmer': 'genome/tuneb/opp/farmer.genome', 'deathball': 'genome/tuneb/opp/deathball.genome',
    'rushbank': 'genome/tuneb/opp/rushbank.genome', 'hunter': 'genome/tuneb/opp/hunter.genome',
    'hunter-carry': 'genome/tuneb/opp/hunter-carry.genome',
    'L1c': 'tune-v20-L1c.pol', 'gconv1': 'style-gconv1.pol', 'v7': 'v7.pol', 'L1': 'tune-v20-L1.pol',
    'rall2': 'rall2-ca4-lean-g.pol', 'metadraft': 'opp-tune5-metadraft.pol',
    'B792': 'genome/candidates/B792.genome', 'A61188': 'genome/candidates/A61188.genome',
    'v28': 'genome/candidates/a61188-mono.genome', 'v29': 'genome/candidates/v28-emblem.genome',
    'v30': 'genome/candidates/A81582-ringheal.genome', 'v31': 'genome/candidates/A81582-rh-mono-all.genome',
    'v32': 'genome/candidates/B1873.genome',
}

_so = {}


def so_of(path):
    if path not in _so:
        out = subprocess.run([sys.executable, '-m', 'genome.build', path], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout
        _so[path] = 'genome:' + out.strip().splitlines()[-1]
    return _so[path]


def side(spec):
    if spec in ANCHORS:
        spec = ANCHORS[spec]
    if spec.endswith('.pol'):
        return os.path.join(POL, spec)
    if spec.endswith('.genome'):
        return so_of(spec if os.path.isabs(spec) else os.path.join(ROOT, spec))
    return spec


def base_text():
    return open(BASE).read()


def draft_gene(order, desc='tune-B draft'):
    lines = ['@gene("d1", "draft preference (tune-B): %s, then anything")' % ', '.join(order),
             'def pick_value(c: Num) -> Num:']
    for i, c in enumerate(order):
        lines += ['    if c == %s:' % c, '        return %d' % (len(order) + 1 - i)]
    lines += ['    return 1', '']
    return '\n'.join(lines)


def with_draft(text, order):
    m = re.search(r'@gene\("d1".*?\n    return 1\n', text, re.S)
    assert m, 'draft gene not found'
    return text[:m.start()] + draft_gene(order) + text[m.end():]


def edit(text, pairs):
    for old, new in pairs:
        assert text.count(old) == 1, 'edit not unique: %r (%d)' % (old, text.count(old))
        text = text.replace(old, new)
    return text


def save(text, tag=None):
    os.makedirs(VAR, exist_ok=True)
    h = hashlib.sha1(text.encode()).hexdigest()[:12]
    p = os.path.join(VAR, '%s.genome' % h)
    if not os.path.exists(p):
        open(p, 'w').write(text)
    return p


def run(a, b, games=200, seed=1, bot_seeds=False, threads=4, maps=None):
    maps = maps or MAPS
    cmd = [EVAL, '--a', side(a), '--b', side(b), '--threads', str(threads)]
    if bot_seeds:
        cmd += ['--bot-seeds', '--games', str(2 * len(maps))]
    else:
        cmd += ['--games', str(games), '--seed', str(seed)]
    out = subprocess.run(cmd + maps, capture_output=True, text=True, check=True).stdout
    lines = [json.loads(l) for l in out.splitlines() if l.startswith('{')]
    s = lines[-1]
    r = s['results']
    wins = s['win_rate'] * len(r)  # results: 1 = side a won
    return dict(wins=wins, games=len(r), rate=wins / len(r), susp=s.get('a_suspensions'), crashes=s.get('crashes'),
                gems=s.get('a_gems'), bgems=s.get('b_gems'), results=r)


def precompile(paths, jobs=4):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(so_of, paths))


def econ(a, b, games=80, seed=1, bot_seeds=True, threads=4, maps=None):
    """Economy checkpoints from side a's view: earned gold at r250 / r500 and gold spent (item points) at r500,
    ours minus theirs, means over games; champion kills / deaths by r250; plus the win rate."""
    maps = maps or MAPS
    cmd = [EVAL_ECON, '--a', side(a), '--b', side(b), '--threads', str(threads), '--checkpoints', '250']
    cmd += ['--bot-seeds', '--games', str(2 * len(maps))] if bot_seeds else ['--games', str(games), '--seed', str(seed)]
    out = subprocess.run(cmd + maps, capture_output=True, text=True, check=True).stdout
    G = [json.loads(l) for l in out.splitlines() if l.startswith('{"game"')]
    acc = dict(gold250=0.0, gold500=0.0, items500=0.0, items500_us=0.0, deaths250=0.0, kills250=0.0, win=0.0)
    for g in G:
        us = 0 if g['a_side'] == 'A' else 1
        cp = {c[0]: c for c in g['cp']}
        last = g['cp'][-1]
        for r, key in ((250, 'gold250'), (500, 'gold500')):
            c = cp.get(r, last)
            acc[key] += (c[5 + us] - c[6 - us]) / 100
        c = cp.get(250, last)
        acc['deaths250'] += c[8 - us]  # their champion kills by r250 = our deaths to champions
        acc['kills250'] += c[7 + us]
        c = cp.get(500, last)
        acc['items500'] += c[9 + us] - c[10 - us]
        acc['items500_us'] += c[9 + us]
        acc['win'] += 1.0 if g['winner'] == us else 0.5 if g['winner'] not in (0, 1) else 0.0
    return {k: v / len(G) for k, v in acc.items()} | dict(games=len(G))


def sign_test(cand, base, maps=None, exclude=('01boss-battle',)):
    """Paired sign test on games where candidate and base results differ (game g = map (g/2) % #maps).
    Returns (cand-only wins, base-only wins, two-sided p)."""
    from math import comb
    maps = maps or MAPS
    up = dn = 0
    for g, (c, b) in enumerate(zip(cand, base)):
        if any(e in maps[(g // 2) % len(maps)] for e in exclude):
            continue
        if c > b: up += 1
        elif c < b: dn += 1
    n = up + dn
    k = min(up, dn)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
    return up, dn, p
