// Plays a policy or a genome against an opponent and prints one JSON summary line (genome/: a copy of
// interp/tools/interp_eval.cpp that also loads compiled genomes, `genome:path.so`, from genome/build.py).
// Usage: genome_eval --a A --b B [--games N] [--threads T] [--seed S] [--max-rounds R] [--fuel-mult X]
//                    [--bot-seeds] [--details] [--block-hits] MAP...
// --bot-seeds: policies seeded per instance as the deploy bot is (reproduces cambc games);
// --details: one JSON line per game (map, side of A, winner, gems, end round) before the summary.
// --fuel-hash: with --details, record every game's per-turn fuel and add "fuel_hash" (FNV-1a over both teams' per-turn
//              fuel, in play order), "turns" and "fuel" (total per team) to each game line (exactness checks).
//              GENOME_TURN_FUEL_ALL=DIR also writes DIR/<game>.txt (both teams' per-turn fuel, one line each).
// --checkpoints N: every N rounds print {"game", "cp": [[round, tributed A, tributed B, carried A, carried B,
//                  gold earned A, gold earned B, kills A, kills B], ...]} for each game (teams A/B, not sides).
// --block-hits: add "block_hits": {block: executions} summed over both sides and all games (counters are
//               shared across threads without locking, so counts are approximate with --threads > 1).
//        genome_eval --list-blocks
// A and B are a compiled policy file (.pol), genome:path.so or builtin:starter / builtin:idle.
// Game g uses map g % #maps; A plays team A on even games and team B on odd games.
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <utility>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include "cbs/bots.h"
#include "interp/policy.h"
#include <dlfcn.h>
#include "genome_rt.h"

using namespace cbs;

struct Side
{
	std::string spec;
	std::shared_ptr<const interp::Program> prog;
	genome::MakeGenes genes = nullptr;
	std::unique_ptr<Player> make(std::uint64_t seed, bool bot_seeds) const
	{
		if (spec.rfind("builtin:", 0) == 0) return make_player(spec.substr(8), seed);
		if (genes) return std::make_unique<genome::GenomePlayer>(genes);
		return interp::make_policy_player(prog, seed, bot_seeds);
	}
};

static Side load_side(const std::string& spec)
{
	Side s{ spec, nullptr };
	if (spec.rfind("genome:", 0) == 0)
	{
		void* h = dlopen(spec.substr(7).c_str(), RTLD_NOW | RTLD_LOCAL);
		if (!h) throw std::runtime_error(std::string("dlopen: ") + dlerror());
		s.genes = reinterpret_cast<genome::MakeGenes>(dlsym(h, "genome_make"));
		if (!s.genes) throw std::runtime_error("no genome_make in " + spec);
		// a genome compiled against another runtime layout would crash: rebuild genome_eval after runtime changes
		if (auto sz = reinterpret_cast<unsigned long (*)()>(dlsym(h, "genome_ctx_size")); sz && sz() != sizeof(genome::Ctx))
			throw std::runtime_error(spec + " was compiled against another runtime (Ctx " + std::to_string(sz()) + " bytes, this genome_eval " +
									 std::to_string(sizeof(genome::Ctx)) + "): rebuild genome_eval");
	}
	else if (spec.rfind("builtin:", 0) != 0) s.prog = interp::load_program_file(spec);
	return s;
}

int main(int argc, char** argv)
{
	interp::state_trace = std::getenv("STATE_TRACE") != nullptr;
	if (const char* tr = std::getenv("STATE_TRACE_ROUNDS")) std::sscanf(tr, "%d-%d", &interp::state_trace_r0, &interp::state_trace_r1);
	if (const char* tt = std::getenv("STATE_TRACE_TILES")) interp::state_trace_tiles = std::atoi(tt);
	std::vector<std::string> maps;
	std::string a_spec = "builtin:starter", b_spec = "builtin:starter";
	int games = 10, threads = 1, max_rounds = 0, checkpoints = 0;
	double fuel_mult = 1.0; // exploration: scale every bot's per-turn fuel budget
	bool bot_seeds = false, details = false, fuel_hash = false;
	const char* turn_fuel_all = std::getenv("GENOME_TURN_FUEL_ALL");
	const char* turn_fuel_out = std::getenv("GENOME_TURN_FUEL"); // game 0: per-turn fuel of both teams, one line each
	std::uint64_t seed = 1;
	for (int i = 1; i < argc; ++i)
	{
		if (!std::strcmp(argv[i], "--list-blocks"))
		{
			for (auto& k : interp::supported_blocks()) std::printf("%s\n", k.c_str());
			return 0;
		}
		if (!std::strcmp(argv[i], "--a")) a_spec = argv[++i];
		else if (!std::strcmp(argv[i], "--b")) b_spec = argv[++i];
		else if (!std::strcmp(argv[i], "--games")) games = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--threads")) threads = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--seed")) seed = std::strtoull(argv[++i], nullptr, 10);
		else if (!std::strcmp(argv[i], "--max-rounds")) max_rounds = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--fuel-mult")) fuel_mult = std::atof(argv[++i]);
		else if (!std::strcmp(argv[i], "--bot-seeds")) bot_seeds = true;
		else if (!std::strcmp(argv[i], "--details")) details = true;
		else if (!std::strcmp(argv[i], "--fuel-hash")) fuel_hash = true;
		else if (!std::strcmp(argv[i], "--checkpoints")) checkpoints = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--block-hits")) cbs::memo_stats().enabled = true;
		else maps.push_back(argv[i]);
	}
	if (maps.empty())
	{
		std::fprintf(stderr, "no maps given\n");
		return 2;
	}
	Side a, b;
	try
	{
		a = load_side(a_spec);
		b = load_side(b_spec);
	}
	catch (const std::exception& e)
	{
		std::printf("{\"error\": \"%s\"}\n", e.what());
		return 1;
	}
	// Maps decode in parallel (vision windows are precomputed per tile: ~15 ms a map).
	std::vector<std::shared_ptr<const Map>> loaded(maps.size());
	{
		std::atomic<std::size_t> next_map{ 0 };
		std::string load_error;
		std::mutex load_mu;
		std::vector<std::thread> loaders;
		for (int t = 0; t < std::max(1, threads); ++t)
			loaders.emplace_back([&] {
				for (std::size_t i; (i = next_map++) < maps.size();)
					try
					{
						loaded[i] = load_map(maps[i]);
					}
					catch (const std::exception& e)
					{
						std::lock_guard<std::mutex> lk(load_mu);
						load_error = e.what();
					}
			});
		for (auto& th : loaders) th.join();
		if (!load_error.empty())
		{
			std::printf("{\"error\": \"%s\"}\n", load_error.c_str());
			return 1;
		}
	}
	// Play the biggest maps first so the threads finish together (each game's seed depends only on g).
	std::vector<int> order(games);
	for (int g = 0; g < games; ++g) order[g] = g;
	std::stable_sort(order.begin(), order.end(), [&](int x, int y) {
		const Map& mx = *loaded[(x / 2) % loaded.size()];
		const Map& my = *loaded[(y / 2) % loaded.size()];
		return mx.W * mx.H > my.W * my.H;
	});

	std::atomic<int> next{ 0 }, a_wins{ 0 };
	std::atomic<long> a_gems{ 0 }, b_gems{ 0 }, rounds{ 0 }, a_susp{ 0 }, crashes{ 0 }, a_fuel{ 0 };
	std::atomic<long> kills[2]{ 0, 0 }, deaths[2]{ 0, 0 }, dmg[2]{ 0, 0 }, lost[2]{ 0, 0 }, caps[2]{ 0, 0 }, capgems[2]{ 0, 0 }, tribs[2]{ 0, 0 }; // [0] = A, [1] = B
	std::mutex mu;
	std::vector<int> per_game(games, 0);
	const auto t0 = std::chrono::steady_clock::now();
	std::vector<std::thread> pool;
	for (int t = 0; t < threads; ++t)
		pool.emplace_back([&] {
			for (int gi; (gi = next++) < games;)
			{
				const int g = order[gi];
				const bool swap = g % 2 == 1; // A plays team B
				const std::uint64_t gs = seed * 1000003ull + static_cast<std::uint64_t>(g);
				auto pa = a.make(2 * gs + 1, bot_seeds), pb = b.make(2 * gs + 2, bot_seeds);
				MatchOptions opt;
				opt.seed = gs;
				opt.max_rounds = max_rounds;
				opt.record_turn_fuel = (turn_fuel_out && g == 0) || fuel_hash || turn_fuel_all;
				opt.fuel.per_turn = static_cast<std::int64_t>(static_cast<double>(opt.fuel.per_turn) * fuel_mult);
				std::string cp;
				if (checkpoints > 0)
					opt.on_round = [&](const Game& gm) {
						if (gm.round % checkpoints != 0 && !gm.over) return;
						long long carried[2] = {};
						for (const auto& c : gm.champs) carried[c.team] += c.gems;
						char buf[256];
						std::snprintf(buf, sizeof buf, "%s[%d, %u, %u, %lld, %lld, %lld, %lld, %d, %d]", cp.empty() ? "" : ", ", gm.round,
									  gm.teams[0].submitted, gm.teams[1].submitted, carried[0], carried[1],
									  static_cast<long long>(gm.teams[0].earned_gold_cents), static_cast<long long>(gm.teams[1].earned_gold_cents),
									  gm.teams[0].kills, gm.teams[1].kills);
						cp += buf;
					};
				Match match(loaded[(g / 2) % loaded.size()], swap ? *pb : *pa, swap ? *pa : *pb, opt);
				const GameResult r = match.run();
				const int at = swap ? 1 : 0;
				const bool won = r.winner == at;
				a_wins += won;
				a_gems += match.game.teams[at].submitted;
				b_gems += match.game.teams[1 - at].submitted;
				rounds += match.game.round;
				a_susp += static_cast<long>(match.stats.suspensions);
				crashes += static_cast<long>(match.stats.crashes);
				a_fuel += static_cast<long>(match.stats.fuel_used[at]);
				for (int k = 0; k < 2; ++k)
				{
					const TeamState& ts = match.game.teams[k == 0 ? at : 1 - at];
					kills[k] += ts.kills;
					deaths[k] += ts.deaths;
					dmg[k] += static_cast<long>(ts.champ_damage);
					lost[k] += static_cast<long>(ts.gems_lost_to_champs);
					caps[k] += ts.captures;
					capgems[k] += static_cast<long>(ts.gems_captured);
					tribs[k] += ts.tributes;
				}
				std::uint64_t fh = 1469598103934665603ull;
				for (int t = 0; t < 2; ++t)
				{
					for (auto v : match.stats.turn_fuel[t]) fh = (fh ^ static_cast<std::uint64_t>(v)) * 1099511628211ull;
					fh = (fh ^ 0xffffffffffffffffull) * 1099511628211ull;
				}
				if (turn_fuel_all)
					if (FILE* f = std::fopen((std::string(turn_fuel_all) + "/" + std::to_string(g) + ".txt").c_str(), "w"))
					{
						for (int t = 0; t < 2; ++t)
						{
							for (auto v : match.stats.turn_fuel[t]) std::fprintf(f, "%lld ", static_cast<long long>(v));
							std::fprintf(f, "\n");
						}
						std::fclose(f);
					}
				std::lock_guard<std::mutex> lk(mu);
				per_game[g] = won;
				if (checkpoints > 0)
					std::printf("{\"game\": %d, \"map\": \"%s\", \"a_side\": \"%s\", \"winner\": %d, \"reason\": %d, \"rounds\": %d, \"cp\": [%s]}\n", g,
								maps[(g / 2) % maps.size()].c_str(), swap ? "B" : "A", r.winner, r.reason, match.game.round, cp.c_str());
				if (turn_fuel_out && g == 0)
					if (FILE* f = std::fopen(turn_fuel_out, "w"))
					{
						for (int t = 0; t < 2; ++t)
						{
							for (auto v : match.stats.turn_fuel[t]) std::fprintf(f, "%lld ", static_cast<long long>(v));
							std::fprintf(f, "\n");
						}
						std::fclose(f);
					}
				if (details)
				{
					std::string draft;
					for (const auto& c : match.game.champs)
						draft += std::string(draft.empty() ? "" : ",") + std::to_string(c.team) + ":" + std::to_string(static_cast<int>(c.type));
					std::printf("{\"game\": %d, \"map\": \"%s\", \"a_side\": \"%s\", \"winner\": %d, \"gems\": [%lld, %lld], \"rounds\": %d, "
								"\"suspensions\": %llu, \"champs\": \"%s\", \"kills\": [%d, %d], \"deaths\": [%d, %d], \"champ_damage\": [%.0f, %.0f], "
								"\"gems_lost_to_champs\": [%u, %u], \"captures\": [%d, %d], \"gems_captured\": [%u, %u], \"tributes\": [%d, %d]}\n",
								g, maps[(g / 2) % maps.size()].c_str(), swap ? "B" : "A", r.winner, static_cast<long long>(match.game.teams[0].submitted),
								static_cast<long long>(match.game.teams[1].submitted), match.game.round,
								static_cast<unsigned long long>(match.stats.suspensions), draft.c_str(), match.game.teams[0].kills, match.game.teams[1].kills,
								match.game.teams[0].deaths, match.game.teams[1].deaths, match.game.teams[0].champ_damage, match.game.teams[1].champ_damage,
								match.game.teams[0].gems_lost_to_champs, match.game.teams[1].gems_lost_to_champs, match.game.teams[0].captures,
								match.game.teams[1].captures, match.game.teams[0].gems_captured, match.game.teams[1].gems_captured, match.game.teams[0].tributes,
								match.game.teams[1].tributes);
					if (fuel_hash)
						std::printf("{\"game\": %d, \"fuel_hash\": \"%016llx\", \"turns\": [%zu, %zu], \"fuel\": [%lld, %lld], \"crashes\": %llu}\n", g,
									static_cast<unsigned long long>(fh), match.stats.turn_fuel[0].size(), match.stats.turn_fuel[1].size(),
									static_cast<long long>(match.stats.fuel_used[0]), static_cast<long long>(match.stats.fuel_used[1]),
									static_cast<unsigned long long>(match.stats.crashes));
				}
			}
		});
	for (auto& th : pool) th.join();
	const double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
	std::printf("{\"games\": %d, \"a_wins\": %d, \"win_rate\": %.4f, \"a_gems\": %.2f, \"b_gems\": %.2f, \"avg_rounds\": %.1f, "
				"\"a_suspensions\": %.2f, \"crashes\": %.2f, \"a_fuel_per_game\": %.0f, \"kills\": [%.2f, %.2f], \"deaths\": [%.2f, %.2f], "
				"\"champ_damage\": [%.0f, %.0f], \"gems_lost_to_champs\": [%.1f, %.1f], \"captures\": [%.2f, %.2f], \"gems_captured\": [%.1f, %.1f], "
				"\"tributes\": [%.2f, %.2f], \"seconds\": %.3f, \"results\": [",
				games, a_wins.load(), double(a_wins) / games, double(a_gems) / games, double(b_gems) / games, double(rounds) / games,
				double(a_susp) / games, double(crashes) / games, double(a_fuel) / games, double(kills[0]) / games, double(kills[1]) / games,
				double(deaths[0]) / games, double(deaths[1]) / games, double(dmg[0]) / games, double(dmg[1]) / games, double(lost[0]) / games,
				double(lost[1]) / games, double(caps[0]) / games, double(caps[1]) / games, double(capgems[0]) / games,
				double(capgems[1]) / games, double(tribs[0]) / games, double(tribs[1]) / games, s);
	for (int g = 0; g < games; ++g) std::printf("%s%d", g ? ", " : "", per_game[g]);
	std::printf("]");
	if (cbs::memo_stats().enabled)
	{
		std::map<std::string, long long> hits; // evaluated and executed uses merged
		for (const auto& c : interp::charge_stats()) hits[c.key.rfind("exec:", 0) == 0 ? c.key.substr(5) : c.key] += c.count;
		std::printf(", \"block_hits\": {");
		bool first = true;
		for (const auto& [k, n] : hits) std::printf("%s\"%s\": %lld", std::exchange(first, false) ? "" : ", ", k.c_str(), n);
		std::printf("}");
		// fuel charged per engine call (cbs::Call order), summed over both sides and all games
		const auto& ms = cbs::memo_stats();
		std::printf(", \"call_fuel\": {");
		first = true;
		for (int c = 0; c < static_cast<int>(cbs::Call::count); ++c)
			if (ms.call_n[c]) std::printf("%s\"%d\": [%lld, %lld]", std::exchange(first, false) ? "" : ", ", c, ms.call_n[c], ms.call_fuel[c]);
		std::printf("}");
	}
	std::printf("}\n");
}
