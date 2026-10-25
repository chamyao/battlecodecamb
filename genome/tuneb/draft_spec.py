"""Draft screen orders around v28 (VENDETTA, VESPER_VALE, TAVI, RYTH, REN) plus the regression's picks."""
import itertools, json, sys
CUR = ['VENDETTA', 'VESPER_VALE', 'TAVI', 'RYTH', 'REN']
PREF = ['VESPER_VALE', 'MARCELLA', 'TAVI', 'VENDETTA', 'RYTH', 'REN', 'VARG', 'CASSI', 'PRISM']  # regression rank


def fill(head):
    tail = [c for c in CUR + PREF if c not in head]
    out = list(head)
    for c in tail:
        if c not in out:
            out.append(c)
    return out[:5]


orders = [CUR]
for p in itertools.permutations(CUR[:3]):
    orders.append(list(p) + CUR[3:])
for p in itertools.permutations(['VESPER_VALE', 'MARCELLA', 'TAVI', 'VENDETTA'], 3):
    orders.append(fill(p))
for i in range(4):
    o = list(CUR); o[i], o[i + 1] = o[i + 1], o[i]; orders.append(o)
for pos in (3, 4):
    for c in ['MARCELLA', 'VARG', 'CASSI', 'PRISM']:
        o = list(CUR); o[pos] = c; orders.append(o)
for pos in range(5):
    o = [c for c in CUR]; o.insert(pos, 'MARCELLA'); orders.append(o[:5])
orders.append(['VESPER_VALE', 'MARCELLA', 'TAVI', 'RYTH', 'VENDETTA'])
orders.append(['MARCELLA', 'PRISM', 'VESPER_VALE', 'VENDETTA', 'REN'])  # regression's top random order
seen, spec = set(), []
for o in orders:
    k = tuple(o)
    if k in seen:
        continue
    seen.add(k)
    spec.append(dict(tag='-'.join(c[:3] for c in o), order=o))
json.dump(spec, open(sys.argv[1], 'w'), indent=0)
print(len(spec))
