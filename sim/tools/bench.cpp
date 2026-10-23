// Plays full games between built-in players and reports throughput.
// Usage: bench MAP [MAP...] [--games N] [--threads T] [--a starter] [--b starter] [--unlimited]
#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <string>
#include <thread>
#include <vector>
#include "cbs/bots.h"

using namespace cbs;

int main(int argc, char** argv)
{
	std::vector<std::string> maps;
	int games = 10, threads = 1;
	std::string pa = "starter", pb = "starter";
	bool unlimited = false;
	for (int i = 1; i < argc; ++i)
	{
		if (!std::strcmp(argv[i], "--games")) games = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--threads")) threads = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--a")) pa = argv[++i];
		else if (!std::strcmp(argv[i], "--b")) pb = argv[++i];
		else if (!std::strcmp(argv[i], "--unlimited")) unlimited = true;
		else maps.push_back(argv[i]);
	}
	std::vector<std::shared_ptr<const Map>> loaded;
	for (auto& m : maps) loaded.push_back(load_map(m));
	std::atomic<int> next{ 0 }, wins_a{ 0 }, wins_b{ 0 };
	std::atomic<long> rounds{ 0 }, turns{ 0 }, susp{ 0 }, gems{ 0 };
	const auto t0 = std::chrono::steady_clock::now();
	std::vector<std::thread> pool;
	for (int t = 0; t < threads; ++t)
		pool.emplace_back([&] {
			for (int g; (g = next++) < games;)
			{
				auto a = make_player(pa, 2 * g + 1), b = make_player(pb, 2 * g + 2);
				MatchOptions opt;
				opt.seed = g;
				opt.unlimited_fuel = unlimited;
				Match match(loaded[g % loaded.size()], *a, *b, opt);
				const GameResult r = match.run();
				(r.winner == 0 ? wins_a : wins_b)++;
				rounds += match.game.round;
				turns += static_cast<long>(match.stats.turns);
				susp += static_cast<long>(match.stats.suspensions);
				gems += match.game.teams[0].submitted + match.game.teams[1].submitted;
			}
		});
	for (auto& th : pool) th.join();
	const double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
	std::printf("%d games in %.3f s: %.2f games/s (%d threads), %.0f rounds/s; avg rounds %.0f, turns/game %.0f, suspensions/game %.1f, gems/game %.0f; A wins %d, B wins %d\n",
				games, s, games / s, threads, rounds / s, double(rounds) / games, double(turns) / games, double(susp) / games, double(gems) / games,
				wins_a.load(), wins_b.load());
}
