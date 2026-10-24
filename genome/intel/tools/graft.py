"""Graft the intel edits (commit = commit_goal + commit_bank + commit_live, mono, gemgroups, firstbank) onto an evolved genome as text patches.

Usage: python3 genome/intel/tools/graft.py BASE.genome OUT.genome EDIT[,EDIT...] [--name LABEL]
Each edit patches the base genome's own versions of the genes it touches (matched by gene ID, so evolved
bodies are kept); a patch whose anchor text is missing fails loudly rather than guessing.
"""
import re, sys


def gene_span(s, gid):
    m = re.search(r'''(?ms)^@gene\(["']%s["'].*?(?=^@gene\(|\Z)''' % re.escape(gid), s)
    if not m:
        raise SystemExit(f'gene {gid} not found')
    return m


def patch_gene(s, gid, old, new, note=None):
    m = gene_span(s, gid)
    g = m.group(0)
    if g.count(old) != 1:
        raise SystemExit(f'{gid}: anchor not found once: {old!r}')
    g = g.replace(old, new)
    if note:
        g = re.sub(r'''^(@gene\(["'][^"']+["'],\s*)(["'])(.*?)\2''', lambda x: f'{x.group(1)}{x.group(2)}{x.group(3)} ({note}){x.group(2)}', g, count=1)
        if 'parents=' not in g.split('\n', 1)[0]:
            g = g.replace(')\ndef ', f', parents=["{gid}"])\ndef ', 1)
    return s[:m.start()] + g + s[m.end():]


def add_keep(s, line):
    anchor = re.search(r'(?m)^OPEN: Bool = False.*$', s)
    return s[:anchor.end()] + '\n' + line + s[anchor.end():]


def add_gene_after(s, gid, text):
    m = gene_span(s, gid)
    return s[:m.end()].rstrip('\n') + '\n\n\n' + text.strip('\n') + '\n\n\n' + s[m.end():].lstrip('\n')


KEEPS_COMMIT = 'LAST_RULE: Num = 0      # last turn rule (intel: hysteresis)\nLAST_GOAL: Tile = None  # last turn walk goal\nBANKING: Bool = False   # last turn walked to an altar to bank'


def commit_keeps(s):
    if 'LAST_RULE: Num' in s:
        return s
    s = add_keep(s, KEEPS_COMMIT)
    return patch_gene(s, 'v2', '        FIELD = walk_field()\n', '''        FIELD = walk_field()
        if at(FIELD, here()) >= 100000000 and GOAL == LAST_GOAL:
            GOAL = rule_goal()
            OPEN = walk_open()
            FIELD = walk_field()
    LAST_RULE = RULE
    LAST_GOAL = GOAL
    BANKING = RULE == 11 or RULE == 12 or RULE == 13
''')


def commit_goal(s):
    s = commit_keeps(s)
    return patch_gene(s, 'v2', '    GOAL = rule_goal()\n', '''    GOAL = rule_goal()
    if RULE == LAST_RULE and (RULE == 11 or RULE == 12 or RULE == 18) and valid(LAST_GOAL) and LAST_GOAL != here() and not (LAST_GOAL in taken()):
        GOAL = LAST_GOAL
''', 'intel: a bank walk keeps the goal of last turn while the rule holds')


def commit_bank(s):
    s = commit_keeps(s)
    return patch_gene(s, 'r10', 'gems() > 0 and bag_ready()', 'gems() > 0 and (bag_ready() or BANKING)', 'intel: or last turn already walked to bank')


def commit_live(s):
    s = commit_keeps(s)
    return patch_gene(s, 'r18', 'dist(camp_goal(), here()) == 0 and exists(c)', '(dist(camp_goal(), here()) == 0 or LAST_RULE == 19) and exists(c)', 'intel: or already walking to a living camp')


def commit(s):
    return commit_live(commit_bank(commit_goal(s)))


FARMABLE = '''@gene("i1", "camp in reach worth hitting: not in a monolith's group (a hit wakes the group), unless the team goes for monoliths (intel GAPS #1)", parents=["s14"])
def farmable(c: Unit) -> Bool:
    if not in_reach(c):
        return False
    if not (camp_spawn(c) in MONO_GROUPS):
        return True
    return r_mono()'''


def mono(s):
    s = add_gene_after(s, 's14', FARMABLE)
    s = patch_gene(s, 'r13', 'exists(reach_camp()) and in_reach(reach_camp())', 'exists(reach_camp()) and farmable(reach_camp())', 'intel: farmable camps only')
    g = gene_span(s, 'r14').group(0)
    if 'return exists(reach_camp()) and in_reach(reach_camp())' in g:
        s = patch_gene(s, 'r14', 'return exists(reach_camp()) and in_reach(reach_camp())', 'return exists(reach_camp()) and farmable(reach_camp())', 'intel: farmable camps only')
    else:
        s = patch_gene(s, 'r14', '    return True\n', '    return farmable(c)\n', 'intel: farmable camps only')
    g = gene_span(s, 's14').group(0)
    if '1 if in_reach(c) else 0' in g:
        s = patch_gene(s, 's14', '1 if in_reach(c) else 0', '1 if farmable(c) else 0', 'intel: farmable first')
    else:
        s = patch_gene(s, 's14', '(1000 if in_reach(c) else 0)', '(1000 if farmable(c) else 0)', 'intel: farmable first')
    g = gene_span(s, 'a0').group(0)
    if 'o.unit.is_camp and o.unit.pos == reach_camp().pos' in g:
        s = patch_gene(s, 'a0', 'o.unit.is_camp and o.unit.pos == reach_camp().pos', 'o.unit.is_camp and farmable(o.unit) and o.unit.pos == reach_camp().pos', 'intel: camp-walk attacks only on farmable camps')
    else:
        s = patch_gene(s, 'a0', 'return 90 if o.unit.pos == reach_camp().pos else 0', 'return 90 if o.unit.pos == reach_camp().pos and farmable(o.unit) else 0', 'intel: camp-walk attacks only on farmable camps')
    return s


GEMGROUPS = '''@gene("i5", "spawn tiles of every group whose reward has gems (intel GAPS #3)", parents=["m8"])
def gem_groups() -> Tiles:
    acc = camp_spawns() - camp_spawns()
    for g in range(num_groups()):
        if group_gems(g) > 0:
            acc = acc | group_tiles(g)
    return acc'''


def gemgroups(s):
    s = add_keep(s, 'GEM_BASE: Tiles = None  # CAMP_BASE tiles of groups that pay gems (intel; from round 3)\nGEM_MAPPED: Bool = False')
    s = patch_gene(s, 'v2', '        MAPPED = True\n', '''        MAPPED = True
    if not GEM_MAPPED and round() >= 3:
        GEM_BASE = CAMP_BASE & gem_groups()
        GEM_MAPPED = True
''', 'intel: gem-paying camp set at round 3')
    s = patch_gene(s, 'm11', '    return closest(CAMP_BASE - respawning())', '''    r = respawning()
    if size(GEM_BASE) > 0:
        t = closest(GEM_BASE - r)
        if valid(t):
            return t
    return closest(CAMP_BASE - r)''', 'intel: groups that pay gems first')
    return add_gene_after(s, 'm11', GEMGROUPS)


def firstbank(s):
    return patch_gene(s, 'r11', 'or hurt_below(0.3)\n', 'or hurt_below(0.3) or (g >= 8 and team_gems() == 0)\n', 'intel: 8+ while the team has banked nothing')


EDITS = dict(commit=commit, commit_goal=commit_goal, commit_bank=commit_bank, commit_live=commit_live, mono=mono, gemgroups=gemgroups, firstbank=firstbank)

if __name__ == '__main__':
    base, out, edits = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
    name = sys.argv[sys.argv.index('--name') + 1] if '--name' in sys.argv else None
    s = open(base).read()
    for e in edits:
        s = EDITS[e](s)
    if name:
        s = s.replace('"""', f'"""{name}: {base.split("/")[-1]} + intel edits {", ".join(edits)} (genome/intel/tools/graft.py).\n\n', 1)
    open(out, 'w').write(s)
