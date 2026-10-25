import re, sys
G = '/root/z19/runs/arenaZ-19d/arena/genomes/'
def L(n): return open(G + n + '.genome').read()
def gene(src, gid):
    m = re.search(r"(@gene\(['\"]%s['\"].*?)(?=\n@gene|\Z)" % re.escape(gid), src, re.S)
    return m.group(1).rstrip() + "\n\n"
def gid_of(src, fname):
    return re.search(r"@gene\(['\"](\w+)['\"][^\n]*\n(?:@[^\n]*\n)*def %s\(" % fname, src).group(1)
def g(src, fname): return gene(src, gid_of(src, fname))
def has(src, fname): return re.search(r"\ndef %s\(" % fname, src) is not None
def w(n, s): open(f'/root/w/d/{n}.txt', 'w').write("```python\n" + s + "```\n")
THREAT = '''@gene("new", "how many awake camps and enemy champions could hit a tile", parents=["%s"])
def threat_at(t: Tile) -> Num:
    return count(is_awake(u) and dist(u.pos, t) <= u.attack_range for u in camps()) + count(dist(u.pos, t) <= u.attack_range + 1 for u in enemies())

'''
CONS = '''@gene("new", "which option kinds to list at all: skip wards, locks and cancels to save fuel", parents=["%s"])
def consider(kind: Num) -> Bool:
    return kind != WARD and kind != LOCK and kind != BUY_LOCK and kind != CANCEL

'''
BSTR = "100 + item_strength(o.item) if item_cost(o.item) >= 30 and item_strength(o.item) > 0 else 0"
def desc(s, add):
    m = re.search(r"@gene\((['\"])\w+\1, (['\"])(.*?)\2", s)
    if m and (len(m.group(3)) > 160 or add in m.group(3)):
        return s
    return re.sub(r"(@gene\((['\"])\w+\2, (['\"]))(.*?)\3", lambda m: m.group(1) + m.group(4) + ", " + add + m.group(3), s, count=1)
def retreat(s, R=0.25, R2=0.3, atk=0.3):
    s2 = re.sub(r"        return 90 if me\(\)\.health_frac < [0-9.]+ else 0\n", f"        return 90 if me().health_frac < {R} and threat_at(me().pos) == 0 else 0\n", s)
    mv = "    if o.kind == MOVE:\n        return 50 if progress(o.tile) > 0 else 0\n"
    assert mv in s2 and s2 != s
    s2 = s2.replace(mv, f"    if o.kind == MOVE:\n        if me().health_frac < {R2} and threat_at(me().pos) > 0:\n            return 95 if threat_at(o.tile) < threat_at(me().pos) else 0\n        return 50 if progress(o.tile) > 0 else 0\n")
    if atk:
        s3 = re.sub(r"        return 60 if (gems\(\) [<=]+ \d+) else 0\n", r"        return 60 if \1 and me().health_frac >= %s else 0\n" % atk, s2)
        assert s3 != s2; s2 = s3
    return desc(s2, "recall when safe, retreat from threats when hurt")
def draft(s, o=('VESPER_VALE','STELLAR','TAVI','CASSI','WILLOW')):
    body = "    if o.kind == PICK:\n" + "".join(f"        if o.champ == {c}:\n            return {10-i}\n" for i,c in enumerate(o)) + "        return 1\n"
    assert "    if o.kind == PICK:\n        return 1\n" in s
    return desc(s.replace("    if o.kind == PICK:\n        return 1\n", body), "draft a ranged team")
def wake(s):
    s2 = re.sub(r"        return 60 if (gems\(\) [<=]+ \d+)(?: and me\(\)\.health_frac >= [\d.]+)? else 0\n",
                r"        return 60 if (\1 or is_awake(o.unit)) and (is_awake(o.unit) or me().health_frac > 0.5) else 0\n", s)
    assert s2 != s, 'no camp attack line'
    return desc(s2, "finish awake camps, wake new ones only when healthy")
import json
def ed(seq, fname):
    u = json.load(open(f'/root/z19/queue/req-{seq}.json'))['user']
    m = re.search(r"## EDITABLE gene %s .*?\n```python\n(.*?)```" % fname, u, re.S)
    return m.group(1).rstrip() + "\n\n"
def later(s):
    s2 = s.replace("me().health_frac < 0.3 and threat_at(me().pos) == 0", "me().health_frac < 0.25 and threat_at(me().pos) == 0").replace("if me().health_frac < 0.35 and threat_at(me().pos) > 0:", "if me().health_frac < 0.3 and threat_at(me().pos) > 0:")
    return s2 if s2 == s else desc(s2, "later recall and retreat")
def focus(s):
    a = "        if o.unit.is_champion:\n            return 80\n"
    if a not in s: return s
    return desc(s.replace(a, "        if o.unit.is_champion:\n            return 80 + 5 * (1 - o.unit.health_frac) + (3 if unit_gems(o.unit) > 0 else 0)\n"), "focus hurt and gem-carrying champions")
