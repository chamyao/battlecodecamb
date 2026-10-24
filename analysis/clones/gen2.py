import sys
base=open('fish_base.policy').read()
def make(name, ret=0.5, eng=8, lsin=1.2, lsout=0.7, bag=22, hpg=0.7):
    s=base.replace('if not at_spawn and health() < 0.3 * max_health():', f'if not at_spawn and health() < {ret} * max_health():')
    s=s.replace('let bag_ready = gems() >= 25', f'let bag_ready = gems() >= {bag}')
    old="if exists(prey) and distance( unit_position(prey), position() ) <= 3 and not contains( enemy_spawn, unit_position(prey) ):\n    hunt(prey)\n"
    new=old+f"if exists(prey) and distance( unit_position(prey), position() ) <= {eng} and local_strength(6) >= {lsin} and health() > {hpg} * max_health() and not contains( enemy_spawn, unit_position(prey) ):\n    hunt(prey)\n"
    assert old in s; s=s.replace(old,new)
    anchor="# in reach: hit the weakest enemy we can already attack (not on its own spawn)\n"
    assert anchor in s
    dis=f"# outmatched nearby: walk away (Fish disengages early and dies ~1 time a game)\nif not at_spawn and enemies_within(6) > 0 and local_strength(6) < {lsout}:\n    let threat = nearest( enemies_visible() )\n    if exists(threat):\n        move_away_from( unit_position(threat) )\n        end_turn()\n"
    s=s.replace(anchor, dis+anchor)
    s=s.replace('# fish-1:', f'# {name} (ret={ret} eng={eng} lsin={lsin} lsout={lsout} bag={bag} hpg={hpg}):',1)
    open(name+'.policy','w').write(s)
args=dict(a.split('=') for a in sys.argv[2:])
make(sys.argv[1], **{k:float(v) if '.' in v else int(v) for k,v in args.items()})
