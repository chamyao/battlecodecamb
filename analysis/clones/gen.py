import sys
base=open('fish_base.policy').read()
def make(name, ret=0.3, eng=3, ally=1, hpg=0.8, bag=25):
    s=base.replace('if not at_spawn and health() < 0.3 * max_health():', f'if not at_spawn and health() < {ret} * max_health():')
    s=s.replace('let bag_ready = gems() >= 25', f'let bag_ready = gems() >= {bag}')
    old="if exists(prey) and distance( unit_position(prey), position() ) <= 3 and not contains( enemy_spawn, unit_position(prey) ):\n    hunt(prey)\n"
    new=old+(f"if exists(prey) and distance( unit_position(prey), position() ) <= {eng} and allies_within(5) >= {ally} and health() > {hpg} * max_health() and not contains( enemy_spawn, unit_position(prey) ):\n    hunt(prey)\n" if eng>3 else '')
    assert old in s
    s=s.replace(old,new)
    s=s.replace('# fish-1:', f'# {name} (ret={ret} eng={eng} ally={ally} hpg={hpg} bag={bag}):',1)
    open(name+'.policy','w').write(s)
args=dict(a.split('=') for a in sys.argv[2:])
make(sys.argv[1], **{k:(float(v) if '.' in v else int(v)) for k,v in args.items()})
