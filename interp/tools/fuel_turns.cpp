// Per-turn fuel the simulator charges a policy, for comparison with real bot fuel.
// Usage: fuel_turns POLICY.pol MAP [--seed S] [--max-rounds R] [--side a|b]
// Plays the policy against builtin:starter with unlimited fuel (charges still counted) and
// prints one line per champion turn of the policy's team: "<turn index> <fuel>".
#include <cstdio>
#include <cstring>
#include <string>
#include "cbs/bots.h"
#include "interp/policy.h"

int main(int argc, char** argv)
{
	if (argc < 3)
	{
		std::fprintf(stderr, "usage: fuel_turns POLICY.pol MAP [--seed S] [--max-rounds R] [--side a|b]\n");
		return 2;
	}
	std::uint64_t seed = 1;
	int max_rounds = 0, side = 0;
	for (int i = 3; i < argc; ++i)
	{
		if (!std::strcmp(argv[i], "--seed")) seed = std::strtoull(argv[++i], nullptr, 10);
		else if (!std::strcmp(argv[i], "--max-rounds")) max_rounds = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--side")) side = argv[++i][0] == 'b';
	}
	auto prog = interp::load_program_file(argv[1]);
	auto pol = interp::make_policy_player(prog, seed);
	auto st = cbs::make_player("starter", seed + 1);
	cbs::MatchOptions o;
	o.seed = seed;
	o.unlimited_fuel = true;
	o.max_rounds = max_rounds;
	o.record_turn_fuel = true;
	cbs::Match m(cbs::load_map(argv[2]), side ? *st : *pol, side ? *pol : *st, o);
	const auto r = m.run();
	const auto& v = m.stats.turn_fuel[side];
	for (std::size_t i = 0; i < v.size(); ++i) std::printf("%zu %lld\n", i, static_cast<long long>(v[i]));
	std::fprintf(stderr, "winner %d rounds %d turns %zu\n", r.winner, m.game.round, v.size());
}
