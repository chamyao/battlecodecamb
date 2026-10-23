"""Patch a copy of the deploy bot (bot/) into a fuel-profiling build.

Usage: python3 bot/profile_patch.py BOT_COPY_DIR [EVERY]   (run bot/sync.sh first; never patch bot/ itself)
Logs every 10th turn of each instance: "@@S id self exp dbits cexp cdbits occ" per interpreter block
(id < 256 eval, 256 + op exec) and per API call (id >= 1000, names in "@@APINAMES"); self
excludes children, API calls and the profiler's own cost ("@@OVH overhead inner"). "@@TURN total".
API records of distance_field / nearest_by_walk: exp = layers of the host search run (memo
miss), dbits = dest tiles queried (nearest_by_walk: 1 + tiles of its reachable mask), occ = misses.
"""
import re
import sys
src=sys.argv[1] + '/src'
every = sys.argv[2] if len(sys.argv) > 2 else '10'
open(f'{src}/sprof.h','w').write(f'#define SPROF_EVERY {every}\n' + r'''#pragma once
#include <cambc.h>
#include <cstdio>
namespace sprof
{
struct Frame { int op; long long f0, child, exp, dbits, excl, cexp, cdbits, occ; };
inline Frame stack[256];
inline int depth = 0;
inline bool logging = false;
struct Rec { int op; long long self, exp, dbits, cexp, cdbits, occ; };
inline Rec rec[8192];
inline int nrec = 0;
inline long long overhead = 0, inner = 0, last_incl = 0;
inline long long now() { return cambc::detail::sdk_fuel_remaining(); }
#ifndef SPROF_EVERY
#define SPROF_EVERY 10 // log every N-th turn of each champion instance
#endif
struct Scope
{
	Scope(int op) { stack[depth++] = { op, now(), 0, 0, 0, 0, 0, 0, 0 }; }
	~Scope()
	{
		const long long t = now();
		Frame& f = stack[--depth];
		const long long incl = f.f0 - t;
		last_incl = incl;
		// From the parent's view a child costs its inclusive time plus the profiler work outside
		// its own window (overhead - inner); its self excludes the window's fixed cost (inner).
		if (depth > 0)
		{
			stack[depth - 1].child += incl + (overhead - inner) + f.excl;
			stack[depth - 1].cexp += f.exp;
			stack[depth - 1].cdbits += f.dbits;
		}
		if (logging && nrec < 8192) rec[nrec++] = { f.op, incl - f.child - f.excl - inner, f.exp, f.dbits, f.cexp, f.cdbits, f.occ };
	}
};
inline void feat(long long exp, long long dbits) { if (depth > 0) stack[depth - 1].exp += exp, stack[depth - 1].dbits += dbits; }
inline void occ() { if (depth > 0) stack[depth - 1].occ++; }
inline void exclude(long long t0) { if (depth > 0) stack[depth - 1].excl += t0 - now(); }
} // namespace sprof
''')
# interpreter blocks
p=f'{src}/vendor_interp_policy.cpp';s=open(p).read()
s=s.replace('#include "interp/policy.h"','#include "interp/policy.h"\n#include "sprof.h"',1)
for a,tag in [("""		Charge charge{ *this, e.op, false };
		const auto& a = e.args;
		switch (e.op)""","static_cast<int>(e.op)"),("""		Charge charge{ *this, e.op, true };
		const auto& a = e.args;
		std::int32_t ok = 0;""","256 + static_cast<int>(e.op)")]:
    assert a in s
    s=s.replace(a, a.replace("		const auto& a = e.args;", f"		sprof::Scope sprof_scope_({tag});\n		const auto& a = e.args;"),1)
a="""		blocks_this_turn = 0;
		run(prog.steps);"""
assert a in s
s=s.replace(a,"""		blocks_this_turn = 0;
		if (turn_no == 1)
		{
			const long long t0 = sprof::now();
			{ sprof::Scope x(510); }
			sprof::overhead = t0 - sprof::now();
			sprof::inner = sprof::last_incl;
			sprof::nrec = 0;
			std::printf("@@OVH %lld inner %lld\\n", sprof::overhead, sprof::inner);
		}
		sprof::logging = api.champ() < 0 || turn_no % SPROF_EVERY == 0; // draft turns: always
		sprof::nrec = 0;
		const long long f0 = sprof::now();
		run(prog.steps);
		const long long total = f0 - sprof::now();
		if (sprof::logging)
		{
			std::printf("@@T %llu\\n", static_cast<unsigned long long>(turn_no));
			for (int i = 0; i < sprof::nrec; ++i) std::printf("@@S %d %lld %lld %lld %lld %lld %lld\\n", sprof::rec[i].op, sprof::rec[i].self, sprof::rec[i].exp, sprof::rec[i].dbits, sprof::rec[i].cexp, sprof::rec[i].cdbits, sprof::rec[i].occ);
			std::printf("@@TURN %lld\\n", total);
		}""")
a='''		if (cache_turn == turn_no && cache_epoch == epoch) return;
'''
assert a in s
s=s.replace(a, a+'		sprof::occ();\n')
open(p,'w').write(s)
# API calls
p=f'{src}/bot_api.cpp';s=open(p).read()
s=s.replace('#include "bot_api.h"','#include "bot_api.h"\n#include "sprof.h"',1)
lines=s.split('\n'); out=[]; names=[]; i=0
while i < len(lines):
    l=lines[i]
    m=re.match(r'^(Err|int|bool) Api::(\w+)\(', l)
    if m:
        nm=m.group(2); idx=1000+len(names); names.append(nm)
        # find opening brace of body
        j=i
        while '{' not in lines[j]: out.append(lines[j]); j+=1
        lb=lines[j]
        k=lb.index('{')
        out.append(lb[:k+1]+f' sprof::Scope sprof_api_({idx});'+lb[k+1:])
        i=j+1; continue
    out.append(l); i+=1
s='\n'.join(out)
# field_query (memo in cbs/field_memo.h): log host-search layers, misses and the dests queried;
# nearest_by_walk: also the tiles of its reachable mask
a="""	const FieldAnswer ans = memo->query(walls, roots, dests, max_distance, have_me, me, qr, W, H);
"""
assert a in s
s=s.replace(a,a+"""	{
		const long long t0 = sprof::now();
		if (ans.miss) sprof::occ();
		sprof::feat(ans.layers, dests ? dests->count(H) : 0);
		sprof::exclude(t0);
	}
""")
a="""		sdk_Bitboard_ReachableMask(walls.w, origin.x, origin.y, near.w, D);
"""
assert a in s
s=s.replace(a,a+"""		{
			const long long t0 = sprof::now();
			sprof::feat(0, near.count(H));
			sprof::exclude(t0);
		}
""")
open(p,'w').write(s)
p=f'{src}/main.cpp';s=open(p).read()
names_str=','.join(names)
s=s.replace("	for (;;)\n	{\n		try","	std::printf(\"@@APINAMES "+names_str+"\\n\");\n	for (;;)\n	{\n		try",1)
open(p,'w').write(s)
print(len(names),"api scopes")
