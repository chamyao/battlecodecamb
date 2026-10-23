// Match runner: drives the draft and the rounds, running each bot instance (one draft bot
// per team, one per champion) on its own coroutine under the fuel rules.
#pragma once
#include <functional>
#include <memory>
#include <vector>
#include "cbs/api.h"

namespace cbs
{
// A bot body: ordinary code that loops forever, calling api.end_turn() to finish each turn.
// champ == -1 for the draft bot. Exceptions crash the instance (it is restarted next turn).
using BotBody = std::function<void(Api&)>;

class Player
{
public:
	virtual ~Player() = default;
	virtual BotBody make_bot(int team, int champ) = 0;
	// Inline players are called once per turn on the runner's own stack instead of running as
	// coroutines (used for Python policies, which cannot be suspended mid-call). For them a
	// fuel overrun cannot suspend: the overrunning call throws FuelExhausted, which ends the
	// turn (the call does not take effect) and the next turn starts with a fresh budget.
	virtual bool is_inline() const { return false; }
	virtual void inline_turn(Api& api) {}
};

// Adapter for policies written as one call per turn (no mid-turn suspension needed).
class TurnPlayer : public Player
{
public:
	virtual void draft_turn(Api& api) = 0;
	virtual void play_turn(Api& api) = 0;
	BotBody make_bot(int team, int champ) override;
};

struct MatchOptions
{
	FuelBudget fuel;
	const PriceTable* prices = &PriceTable::placeholder();
	bool unlimited_fuel = false;
	std::uint64_t seed = 1;	 // fills missed draft picks
	int max_rounds = 0;		 // 0 = settings().max_rounds
	std::size_t stack_size = 256 * 1024;
};

struct MatchStats
{
	std::uint64_t turns = 0, suspensions = 0, crashes = 0, truncations = 0;
	std::int64_t fuel_used[2] = {};
};

class Match
{
public:
	Match(std::shared_ptr<const Map> map, Player& a, Player& b, MatchOptions opt = {});
	~Match();
	GameResult run();
	Game game;
	MatchStats stats;

private:
	struct Instance;
	Player* players_[2];
	MatchOptions opt_;
	std::vector<std::unique_ptr<Instance>> draft_bots_, champ_bots_;
	void run_turn(Instance& inst);
	std::unique_ptr<Instance> make_instance(int team, int champ);
};
} // namespace cbs
