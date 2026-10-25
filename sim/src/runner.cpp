#include "cbs/runner.h"

namespace cbs
{
BotBody TurnPlayer::make_bot(int team, int champ)
{
	return [this, champ](Api& api) {
		for (;;)
		{
			if (champ < 0) draft_turn(api);
			else play_turn(api);
			api.end_turn();
		}
	};
}

struct Match::Instance
{
	int team, champ;
	Api api;
	Coroutine coro;
	BotBody body;
	int turns = 0;
	bool needs_start = true;
	Instance(Game& g, int t, int c, const PriceTable* p, std::size_t stack) : team(t), champ(c), api(g, t, c, p), coro(stack) {}
};

Match::Match(std::shared_ptr<const Map> map, Player& a, Player& b, MatchOptions opt) : game(std::move(map)), players_{ &a, &b }, opt_(opt)
{
	game.draft.rounds = game.map().draft_rounds;
}

Match::~Match() = default;

std::unique_ptr<Match::Instance> Match::make_instance(int team, int champ)
{
	const PriceTable* prices = players_[team]->prices() ? players_[team]->prices() : opt_.prices;
	auto inst = std::make_unique<Instance>(game, team, champ, prices, opt_.stack_size);
	inst->api.unlimited = opt_.unlimited_fuel;
	if (players_[team]->is_inline()) return inst;
	inst->body = players_[team]->make_bot(team, champ);
	inst->api.attach(&inst->coro);
	return inst;
}

void Match::run_turn(Instance& inst)
{
	Player& player = *players_[inst.team];
	if (player.is_inline())
	{
		std::int64_t budget = opt_.fuel.per_turn;
		if (inst.turns == 0) budget *= inst.champ < 0 ? opt_.fuel.draft_first_turn_multiplier : opt_.fuel.play_first_turn_multiplier;
		inst.api.budget = budget;
		inst.api.spent = 0;
		try
		{
			player.inline_turn(inst.api);
		}
		catch (const FuelExhausted&)
		{
			++stats.truncations;
		}
		stats.fuel_used[inst.team] += inst.api.spent;
		if (opt_.record_turn_fuel && inst.champ >= 0) stats.turn_fuel[inst.team].push_back(inst.api.spent);
		++inst.turns;
		++stats.turns;
		return;
	}
	if (inst.needs_start || inst.coro.done())
	{
		// First turn, or the bot crashed/returned: (re)start a fresh body. RULE? restart policy
		if (!inst.needs_start && inst.coro.crashed()) ++stats.crashes;
		Instance* p = &inst;
		inst.coro.start([p] { p->body(p->api); });
		inst.needs_start = false;
	}
	std::int64_t budget = opt_.fuel.per_turn;
	if (inst.turns == 0) budget *= inst.champ < 0 ? opt_.fuel.draft_first_turn_multiplier : opt_.fuel.play_first_turn_multiplier;
	inst.api.budget = budget;
	inst.api.spent = 0;
	const auto susp = inst.api.suspensions;
	inst.coro.resume();
	stats.suspensions += inst.api.suspensions - susp;
	stats.fuel_used[inst.team] += inst.api.spent;
	if (opt_.record_turn_fuel && inst.champ >= 0) stats.turn_fuel[inst.team].push_back(inst.api.spent);
	++inst.turns;
	++stats.turns;
}

GameResult Match::run()
{
	// Every board of this match lies inside the map: board-wide ops need only its rows (bots run on
	// this thread's coroutines, so they see the same value).
	struct Rows
	{
		int saved = board_rows;
		~Rows() { board_rows = saved; }
	} rows_guard;
	board_rows = game.map().H;
	for (int t = 0; t < 2; ++t) draft_bots_.push_back(make_instance(t, -1));
	std::uint64_t rng = opt_.seed * 0x9E3779B97F4A7C15ull + 1;
	while (!game.draft.done)
	{
		for (int t = 0; t < 2; ++t) run_turn(*draft_bots_[t]);
		game.draft_end_round(rng);
	}
	draft_bots_.clear();
	game.start_play();
	for (const auto& ch : game.champs) champ_bots_.push_back(make_instance(ch.team, ch.id));
	const int max_rounds = opt_.max_rounds ? opt_.max_rounds : settings().max_rounds;
	std::vector<int> order;
	while (!game.over)
	{
		game.begin_round();
		game.turn_order(order);
		for (int c : order)
		{
			game.begin_turn(c);
			if (game.over) break;
			run_turn(*champ_bots_[c]);
			if (game.over) break;
			game.end_turn(c);
		}
		game.end_round();
		if (opt_.on_round) opt_.on_round(game);
		if (!game.over && game.round >= max_rounds)
		{
			game.over = true;
			game.result.reason = 2;
			game.result.rounds = game.round;
		}
	}
	champ_bots_.clear();
	return game.result;
}
} // namespace cbs
