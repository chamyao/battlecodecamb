// Plays a policy against an opponent and prints one JSON summary line.
// Usage: interp_eval --a A --b B [--games N] [--threads T] [--seed S] [--max-rounds R] MAP...
//        interp_eval --list-blocks
// A and B are a compiled policy file (.pol) or builtin:starter / builtin:idle.
// Game g uses map g % #maps; A plays team A on even games and team B on odd games.
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include "cbs/bots.h"
#include "interp/policy.h"

using namespace cbs;

struct Side
{
	std::string spec;
	std::shared_ptr<const interp::Program> prog;
	std::unique_ptr<Player> make(std::uint64_t seed) const
	{
		if (spec.rfind("builtin:", 0) == 0) return make_player(spec.substr(8), seed);
		return interp::make_policy_player(prog, seed);
	}
};

static Side load_side(const std::string& spec)
{
	Side s{ spec, nullptr };
	if (spec.rfind("builtin:", 0) != 0) s.prog = interp::load_program_file(spec);
	return s;
}

int main(int argc, char** argv)
{
	std::vector<std::string> maps;
	std::string a_spec = "builtin:starter", b_spec = "builtin:starter";
	int games = 10, threads = 1, max_rounds = 0;
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
	std::vector<std::shared_ptr<const Map>> loaded;
	for (auto& m : maps) loaded.push_back(load_map(m));

	std::atomic<int> next{ 0 }, a_wins{ 0 };
	std::atomic<long> a_gems{ 0 }, b_gems{ 0 }, rounds{ 0 }, a_susp{ 0 }, crashes{ 0 }, a_fuel{ 0 };
	std::mutex mu;
	std::vector<int> per_game(games, 0);
	const auto t0 = std::chrono::steady_clock::now();
	std::vector<std::thread> pool;
	for (int t = 0; t < threads; ++t)
		pool.emplace_back([&] {
			for (int g; (g = next++) < games;)
			{
				const bool swap = g % 2 == 1; // A plays team B
				const std::uint64_t gs = seed * 1000003ull + static_cast<std::uint64_t>(g);
				auto pa = a.make(2 * gs + 1), pb = b.make(2 * gs + 2);
				MatchOptions opt;
				opt.seed = gs;
				opt.max_rounds = max_rounds;
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
				std::lock_guard<std::mutex> lk(mu);
				per_game[g] = won;
			}
		});
	for (auto& th : pool) th.join();
	const double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
	std::printf("{\"games\": %d, \"a_wins\": %d, \"win_rate\": %.4f, \"a_gems\": %.2f, \"b_gems\": %.2f, \"avg_rounds\": %.1f, "
				"\"a_suspensions\": %.2f, \"crashes\": %.2f, \"a_fuel_per_game\": %.0f, \"seconds\": %.3f, \"results\": [",
				games, a_wins.load(), double(a_wins) / games, double(a_gems) / games, double(b_gems) / games, double(rounds) / games,
				double(a_susp) / games, double(crashes) / games, double(a_fuel) / games, s);
	for (int g = 0; g < games; ++g) std::printf("%s%d", g ? ", " : "", per_game[g]);
	std::printf("]}\n");
}
