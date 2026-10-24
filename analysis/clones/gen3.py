import sys,re
v21=open('/tmp/claude-0/fs/policies/tune-v21.policy').read()
h3=open('/tmp/claude-0/fs/policies/opp-hunter3.policy').read()
hunt=h3[h3.index('# engage u: hit it if in reach'):h3.index('# ---- draft ----')]
fb=open('fish_base.policy').read()
draft=fb[fb.index('# ---- draft ----'):fb.index('# ---- every turn ----')]
shop=fb[fb.index('    let shards_bought = floor( gold() / 30 )'):fb.index('    # heal on spawn')]
def make(name, items=True, engage=False, eng=8, lsin=1.5, lsout=0.0, hpg=0.8, bag=25):
    s=v21
    s=s[:s.index('# ---- draft ----')]+hunt+draft+s[s.index('# ---- every turn ----'):]
    if items:
        a=s.index('    let shards_bought = floor( gold() / 30 )'); b=s.index('    # heal on spawn')
        s=s[:a]+shop+s[b:]
    s=s.replace('let bag_ready = gems() >= 25', f'let bag_ready = gems() >= {bag}')
    anchor="let enemy = weakest( filter( foes, in_attack_range() ) )\n"
    assert anchor in s
    add=''
    if lsout>0:
        add+=f"if not at_spawn and enemies_within(6) > 0 and local_strength(6) < {lsout}:\n    let threat = nearest( foes )\n    if exists(threat):\n        move_away_from( unit_position(threat) )\n        end_turn()\n"
    s=s.replace(anchor, add+anchor)
    if engage:
        anchor2="# lock once (tune line): the champion holding the lock, bag empty"
        assert anchor2 in s
        e=f"# Fish engage: the closest visible enemy within {eng}, with local strength on our side and healthy\nlet prey = nearest( foes )\nif exists(prey) and distance( unit_position(prey), position() ) <= {eng} and local_strength(6) >= {lsin} and health() > {hpg} * max_health() and not contains( spawn_region(enemy()), unit_position(prey) ):\n    hunt(prey)\n"
        s=s.replace(anchor2, e+anchor2,1)
    s=f"# {name}: v21 + Fish draft{' + Fish items' if items else ''}{f' + engage(eng={eng} lsin={lsin} hpg={hpg})' if engage else ''}{f' + disengage(ls<{lsout})' if lsout else ''}, bag {bag} (analysis line)\n"+s
    open(name+'.policy','w').write(s)
args=dict(a.split('=') for a in sys.argv[2:])
conv=lambda v: v=='True' if v in('True','False') else (float(v) if '.' in v else int(v))
make(sys.argv[1], **{k:conv(v) for k,v in args.items()})
