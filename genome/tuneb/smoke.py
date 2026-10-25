import sys; sys.path.insert(0,'.')
from genome.tuneb import tb
t = tb.with_draft(tb.base_text(), ['VENDETTA','VESPER_VALE','TAVI','RYTH','REN'])
p = tb.save(t)
print(p, tb.so_of(p), tb.so_of(tb.BASE))
print(tb.run(p, tb.BASE, bot_seeds=True)['wins'])
