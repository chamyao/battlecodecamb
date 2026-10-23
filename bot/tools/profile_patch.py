"""Instrument a vendored copy of interp/src/policy.cpp with per-block real-fuel accounting.

Usage: python3 bot/tools/profile_patch.py bot/src/vendor_interp_policy.cpp
Each eval/exec is bracketed with sdk_fuel_remaining(); exclusive fuel (children
subtracted) is summed per op and per step-op, and printed every 200 turns as
  @@P <turn> <op> <count> <total> <max>
plus @@T <turn> <fuel used this turn by the policy pass> lines.
Not for submission builds (bot/sync.sh restores the plain copy).
"""
import re, sys
p = sys.argv[1]
s = open(p).read()
s = s.replace('#include "interp/policy.h"', '#include "interp/policy.h"\n#include <cambc.h>\n#include <cstdio>', 1)
hook = r'''
	struct Prof { std::uint64_t n = 0, tot = 0, mx = 0; };
	Prof prof[2][512];
	std::int64_t prof_child = 0;
	template <class F>
	auto timed(int kind, Op op, F&& f)
	{
		const std::int64_t f0 = cambc::detail::sdk_fuel_remaining();
		const std::int64_t saved = prof_child;
		prof_child = 0;
		auto finish = [&]() {
			const std::int64_t used = f0 - cambc::detail::sdk_fuel_remaining();
			const std::int64_t excl = used - prof_child;
			Prof& q = prof[kind][static_cast<int>(op)];
			++q.n; q.tot += excl; if (excl > (std::int64_t)q.mx) q.mx = excl;
			prof_child = saved + used;
		};
		if constexpr (std::is_void_v<decltype(f())>) { f(); finish(); }
		else { auto r = f(); finish(); return r; }
	}
	void prof_dump()
	{
		for (int k = 0; k < 2; ++k)
			for (int i = 0; i < 512; ++i)
				if (prof[k][i].n)
					std::printf("@@P %d %llu %s%s %llu %llu %llu\n", api.champ(), (unsigned long long)turn_no, k ? "do:" : "",
								i < kNumBlocks ? kBlockTable[i].key : (i == (int)Op::var ? "var" : "const"),
								(unsigned long long)prof[k][i].n, (unsigned long long)prof[k][i].tot, (unsigned long long)prof[k][i].mx);
	}
	Value eval(const Expr& e) { return timed(0, e.op, [&]() { return eval_(e); }); }
	void exec(const Expr& e) { timed(1, e.op, [&]() { exec_(e); }); }
'''
s = s.replace('\tValue eval(const Expr& e)\n', hook + '\tValue eval_(const Expr& e)\n', 1)
s = s.replace('\tvoid exec(const Expr& e)\n', '\tvoid exec_(const Expr& e)\n', 1)
s = s.replace('''		++turn_no;
		run(prog.steps);''', '''		++turn_no;
		const std::int64_t t0 = cambc::detail::sdk_fuel_remaining();
		run(prog.steps);
		std::printf("@@T %d %llu %lld\\n", api.champ(), (unsigned long long)turn_no, (long long)(t0 - cambc::detail::sdk_fuel_remaining()));
		if (turn_no % 200 == 0) prof_dump();''', 1)
assert s.count('eval_(') == 2 and 'exec_(' in s and '@@T' in s
open(p, 'w').write(s)
