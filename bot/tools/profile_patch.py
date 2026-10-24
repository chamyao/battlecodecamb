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
s = s.replace('#include "interp/policy.h"', '#include "interp/policy.h"\n#include <cambc.h>\n#include <cstdio>\n#if __has_include("prof2.h")\n#include "prof2.h"\n#endif', 1)
hook = r'''
	struct Prof { std::uint64_t n, tot, mx; }; // zeroed as statics
	static inline Prof prof[2][512]; // static: 32 KB would overflow the stack the interpreter lives on
	static inline std::int64_t turn_tot[2][512] = {};
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
			turn_tot[kind][static_cast<int>(op)] += excl;
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
s = re.sub(r'(\t\t\+\+turn_no;\n(?:.*\n)*?)(\t\trun\(prog\.steps\);)', lambda m: m.group(1) + '''		const std::int64_t t0 = cambc::detail::sdk_fuel_remaining();
		run(prog.steps);
		std::printf("@@T %d %llu %lld\\n", api.champ(), (unsigned long long)turn_no, (long long)(t0 - cambc::detail::sdk_fuel_remaining()));
		if (t0 - cambc::detail::sdk_fuel_remaining() > 50000)
		{
			std::printf("@@HEAVY %d %llu", api.champ(), (unsigned long long)turn_no);
#ifdef BOT_PROF2
			std::printf(" [fq=%lld host=%lld nbw=%lld ident=%lld df=%lld probe=%lld dfwrap=%lld box=%lld]", ::bot_prof[0], ::bot_prof[1], ::bot_prof[2], ::bot_prof[3], ::bot_prof[4], ::bot_prof[5], ::bot_prof[6], ::bot_prof[7]);
#endif
			for (int k = 0; k < 2; ++k)
				for (int i = 0; i < 512; ++i)
					if (turn_tot[k][i] > 400)
						std::printf(" %s%s=%lld", k ? "do:" : "", i < kNumBlocks ? kBlockTable[i].key : "?", (long long)turn_tot[k][i]);
			std::printf("\\n");
		}
		for (int k = 0; k < 2; ++k)
			for (int i = 0; i < 512; ++i) turn_tot[k][i] = 0;
#ifdef BOT_PROF2
		for (auto& v : ::bot_prof) v = 0;
#endif
		if (turn_no % 200 == 0) prof_dump();''', s, count=1)
assert s.count('eval_(') == 2 and 'exec_(' in s and '@@T' in s
open(p, 'w').write(s)
