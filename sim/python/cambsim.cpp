// Python bindings: batched matches between built-in C++ policies (GIL released, threaded),
// and Python policies driven through the same bot Api (one call per turn, hidden information
// enforced). Api methods mirror the engine host imports: queries return (err, value) and
// actions return err or (err, ok); err 0 is success (see cbs::Err).
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <atomic>
#include <thread>
#include "cbs/bots.h"

namespace py = pybind11;
using namespace cbs;

namespace
{
py::array_t<bool> to_numpy(const Bitboard& b, int W, int H)
{
	py::array_t<bool> a({ H, W });
	auto m = a.mutable_unchecked<2>();
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x) m(y, x) = b.test(x, y);
	return a;
}
Bitboard from_numpy(const py::array_t<bool, py::array::c_style | py::array::forcecast>& a)
{
	Bitboard b;
	auto m = a.unchecked<2>();
	for (py::ssize_t y = 0; y < m.shape(0) && y < kMaxDim; ++y)
		for (py::ssize_t x = 0; x < m.shape(1) && x < kMaxDim; ++x)
			if (m(y, x)) b.set(static_cast<int>(x), static_cast<int>(y));
	return b;
}
int E(Err e) { return static_cast<int>(e); }
PyObject* g_fuel_exhausted = nullptr; // Python type for FuelExhausted

class PyPlayer : public Player
{
public:
	BotBody make_bot(int, int) override { throw std::logic_error("Python players run inline"); }
	bool is_inline() const override { return true; }
	void inline_turn(Api& api) override
	{
		py::gil_scoped_acquire gil;
		py::function f = py::get_override(static_cast<const Player*>(this), "turn");
		if (!f) throw std::logic_error("Player.turn not implemented");
		try
		{
			f(py::cast(&api, py::return_value_policy::reference));
		}
		catch (py::error_already_set& e)
		{
			// A fuel overrun raised inside a Python policy ends the turn like a C++ one.
			if (g_fuel_exhausted && e.matches(g_fuel_exhausted)) throw FuelExhausted{};
			throw;
		}
	}
};

py::dict result_dict(const Match& m)
{
	py::dict d;
	const Game& g = m.game;
	d["winner"] = g.result.winner;
	d["reason"] = g.result.reason;
	d["rounds"] = g.round;
	d["gems"] = py::make_tuple(g.teams[0].submitted, g.teams[1].submitted);
	d["earned_gold"] = py::make_tuple(g.teams[0].earned_gold_cents / 100.0, g.teams[1].earned_gold_cents / 100.0);
	d["kills"] = py::make_tuple(g.teams[0].kills, g.teams[1].kills);
	d["turns"] = m.stats.turns;
	d["suspensions"] = m.stats.suspensions;
	d["truncations"] = m.stats.truncations;
	d["crashes"] = m.stats.crashes;
	d["fuel_used"] = py::make_tuple(m.stats.fuel_used[0], m.stats.fuel_used[1]);
	py::list picks;
	for (const auto& c : g.champs) picks.append(py::make_tuple(c.team, static_cast<int>(c.type)));
	d["champions"] = picks;
	return d;
}

struct MatchSpec
{
	std::string a = "starter", b = "starter";
	std::uint64_t seed = 1;
	bool unlimited = false;
	int max_rounds = 0;
};
} // namespace

PYBIND11_MODULE(cambsim, m)
{
	m.doc() = "Exact simulator of Cambridge Battlecode 2026a (cbs).";

	py::class_<Vec2>(m, "Vec2").def(py::init<int, int>()).def_readwrite("x", &Vec2::x).def_readwrite("y", &Vec2::y).def("__repr__", [](const Vec2& v) {
		return "Vec2(" + std::to_string(v.x) + ", " + std::to_string(v.y) + ")";
	});

	py::class_<Map, std::shared_ptr<Map>>(m, "Map")
		.def_readonly("name", &Map::name)
		.def_readonly("width", &Map::W)
		.def_readonly("height", &Map::H)
		.def_readonly("draft_rounds", &Map::draft_rounds)
		.def_property_readonly("walls", [](const Map& mp) { return to_numpy(mp.walls, mp.W, mp.H); })
		.def_property_readonly("bushes", [](const Map& mp) { return to_numpy(mp.bushes, mp.W, mp.H); })
		.def_property_readonly("holes", [](const Map& mp) { return to_numpy(mp.holes, mp.W, mp.H); })
		.def_property_readonly("altars", [](const Map& mp) { return to_numpy(mp.altars, mp.W, mp.H); })
		.def_property_readonly("num_camps", [](const Map& mp) { return mp.camps.size(); })
		.def_property_readonly("num_groups", [](const Map& mp) { return mp.groups.size(); })
		.def("vision", [](const Map& mp, int x, int y, int radius) {
			Bitboard b;
			mp.vision({ x, y }, radius, b);
			return to_numpy(b, mp.W, mp.H);
		});
	m.def("load_map", [](const std::string& path) { return std::const_pointer_cast<Map>(load_map(path)); });

	py::class_<ChampionInfo>(m, "ChampionInfo")
		.def_readonly("team", &ChampionInfo::team)
		.def_readonly("type", &ChampionInfo::type)
		.def_readonly("x", &ChampionInfo::x)
		.def_readonly("y", &ChampionInfo::y)
		.def_readonly("health", &ChampionInfo::health)
		.def_readonly("max_health", &ChampionInfo::max_health)
		.def_readonly("strength", &ChampionInfo::strength)
		.def_readonly("focus", &ChampionInfo::focus)
		.def_readonly("move_speed", &ChampionInfo::move_speed)
		.def_readonly("attack_range", &ChampionInfo::attack_range)
		.def_readonly("state", &ChampionInfo::state);
	py::class_<CampRecord>(m, "CampRecord")
		.def_readonly("x", &CampRecord::x)
		.def_readonly("y", &CampRecord::y)
		.def_readonly("health", &CampRecord::health)
		.def_readonly("max_health", &CampRecord::max_health)
		.def_readonly("strength", &CampRecord::strength)
		.def_readonly("focus", &CampRecord::focus)
		.def_property_readonly("cooldowns", [](const CampRecord& r) { return py::make_tuple(r.cooldowns[0], r.cooldowns[1]); });
	py::class_<BuffRecord>(m, "BuffRecord").def_readonly("type", &BuffRecord::type).def_readonly("duration", &BuffRecord::duration).def_readonly("value", &BuffRecord::value);
	py::class_<WardRecord>(m, "WardRecord")
		.def_readonly("team", &WardRecord::team)
		.def_readonly("x", &WardRecord::x)
		.def_readonly("y", &WardRecord::y)
		.def_readonly("owner", &WardRecord::owner);
	py::class_<TeleportRecord>(m, "TeleportRecord")
		.def_readonly("champion", &TeleportRecord::champion)
		.def_readonly("team", &TeleportRecord::team)
		.def_readonly("dx", &TeleportRecord::dx)
		.def_readonly("dy", &TeleportRecord::dy)
		.def_readonly("timer", &TeleportRecord::timer);
	py::class_<AltarLockRecord>(m, "AltarLockRecord")
		.def_readonly("handle", &AltarLockRecord::handle)
		.def_readonly("team", &AltarLockRecord::team)
		.def_readonly("x", &AltarLockRecord::x)
		.def_readonly("y", &AltarLockRecord::y)
		.def_readonly("hits_remaining", &AltarLockRecord::hits_remaining);
	py::class_<AbilityProps>(m, "AbilityProps")
		.def_readonly("kind", &AbilityProps::kind)
		.def_readonly("cooldown", &AbilityProps::cooldown)
		.def_readonly("targets", &AbilityProps::targets)
		.def_readonly("attributes", &AbilityProps::attributes)
		.def_readonly("range", &AbilityProps::range)
		.def_readonly("radius", &AbilityProps::radius)
		.def_readonly("modifier", &AbilityProps::modifier)
		.def_readonly("duration", &AbilityProps::duration);

	g_fuel_exhausted = py::register_exception<FuelExhausted>(m, "FuelExhausted").ptr();

	// The Api object passed to Player.turn is only valid during that call.
	py::class_<Api> api(m, "Api");
	api.def_property_readonly("team", &Api::team)
		.def_property_readonly("champ", &Api::champ)
		.def_property_readonly("map", [](Api& a) { return std::const_pointer_cast<Map>(a.game().map_ptr()); })
		.def_readwrite("spent", &Api::spent)
		.def_readonly("budget", &Api::budget)
		.def("compute", &Api::compute, "Charge fuel for the policy's own computation.")
		.def("fuel_remaining", &Api::fuel_remaining)
		.def("my_champion", &Api::my_champion)
		.def("my_team", &Api::my_team)
		// Diagnostics (differential replays): the full, unfogged game state.
		.def("truth", [](Api& a) {
			const Game& g = a.game();
			py::list champs, camps;
			for (const auto& c : g.champs)
				champs.append(py::make_tuple(c.id, c.team, static_cast<int>(c.type), c.alive, c.pos.x, c.pos.y, c.hp, c.max_hp, c.gold_int(), c.gems, c.kills,
											 c.strength, c.focus));
			for (const auto& c : g.camps) camps.append(py::make_tuple(c.pos.x, c.pos.y, c.hp, static_cast<int>(c.life)));
			return py::make_tuple(g.round, champs, camps, g.teams[0].submitted, g.teams[1].submitted);
		});
#define Q(name, T)                                                                                                                         \
	api.def(#name, [](Api& a, std::uint32_t h) {                                                                                           \
		T v{};                                                                                                                             \
		const Err e = a.name(h, &v);                                                                                                       \
		return py::make_tuple(E(e), v);                                                                                                    \
	})
	Q(champion, ChampionInfo);
	Q(champion_gems, std::uint32_t);
	Q(champion_gold, std::uint32_t);
	Q(champion_is_alive, std::int32_t);
	Q(champion_channel_time, std::int32_t);
	Q(champion_can_sell, std::int32_t);
	Q(camp, CampRecord);
	Q(camp_state, std::uint32_t);
	Q(camp_group_state, std::uint32_t);
	Q(camp_group_cooldown, std::int32_t);
	Q(submitted_gems, std::uint32_t);
#undef Q
	api.def("champion_restrictions", [](Api& a, std::uint32_t h) {
		   std::uint8_t v = 0;
		   const Err e = a.champion_restrictions(h, &v);
		   return py::make_tuple(E(e), v);
	   })
		.def("champion_cooldown", [](Api& a, std::uint32_t h, std::uint32_t slot) {
			std::int32_t v = 0;
			const Err e = a.champion_cooldown(h, slot, &v);
			return py::make_tuple(E(e), v);
		})
		.def("champion_ability_props", [](Api& a, std::uint32_t h, std::uint32_t slot) {
			AbilityProps v{};
			const Err e = a.champion_ability_props(h, slot, &v);
			return py::make_tuple(E(e), v);
		})
		.def("champion_items", [](Api& a, std::uint32_t h) {
			std::vector<std::uint32_t> v(kNumItems);
			const Err e = a.champion_items(h, v.data());
			return py::make_tuple(E(e), v);
		})
		.def("champion_consumables", [](Api& a, std::uint32_t h) {
			std::vector<std::uint32_t> v(kNumConsumables);
			const Err e = a.champion_consumables(h, v.data());
			return py::make_tuple(E(e), v);
		})
		.def("champion_buffs", [](Api& a, std::uint32_t h) {
			BuffRecord r[16];
			std::uint32_t n = 0;
			const Err e = a.champion_buff_data(h, r, 16, &n);
			return py::make_tuple(E(e), std::vector<BuffRecord>(r, r + std::min<std::uint32_t>(n, 16)));
		})
		.def("champion_priority", [](Api& a, std::uint32_t h, bool next) {
			std::int32_t v = 0;
			const Err e = a.champion_priority(h, next, &v);
			return py::make_tuple(E(e), v);
		})
		.def("champion_can_shop", [](Api& a, std::uint32_t h, bool consumables) {
			std::int32_t v = 0;
			const Err e = a.champion_can_shop(h, consumables, &v);
			return py::make_tuple(E(e), v);
		})
		.def("allies", [](Api& a) {
			std::uint32_t ids[16], n = 0;
			const Err e = a.allies(ids, 16, &n);
			return py::make_tuple(E(e), std::vector<std::uint32_t>(ids, ids + std::min<std::uint32_t>(n, 16)));
		})
		.def("enemies", [](Api& a) {
			std::uint32_t ids[16], n = 0;
			const Err e = a.enemies(ids, 16, &n);
			return py::make_tuple(E(e), std::vector<std::uint32_t>(ids, ids + std::min<std::uint32_t>(n, 16)));
		})
		.def("champion_at", [](Api& a, int x, int y) {
			std::uint32_t v = 0;
			const Err e = a.champion_at({ x, y }, &v);
			return py::make_tuple(E(e), v);
		})
		.def("camp_at", [](Api& a, int x, int y) {
			std::uint32_t v = 0;
			const Err e = a.camp_at({ x, y }, &v);
			return py::make_tuple(E(e), v);
		})
		.def("is_visible", [](Api& a, int x, int y) {
			std::int32_t v = 0;
			const Err e = a.is_visible({ x, y }, &v);
			return py::make_tuple(E(e), v != 0);
		})
		.def("vision", [](Api& a) {
			Bitboard b;
			const Err e = a.vision(b);
			return py::make_tuple(E(e), to_numpy(b, a.map().W, a.map().H));
		})
		.def("ally_occupancy", [](Api& a) {
			Bitboard b;
			const Err e = a.ally_occupancy(b);
			return py::make_tuple(E(e), to_numpy(b, a.map().W, a.map().H));
		})
		.def("enemy_occupancy", [](Api& a) {
			Bitboard b;
			const Err e = a.enemy_occupancy(b);
			return py::make_tuple(E(e), to_numpy(b, a.map().W, a.map().H));
		})
		.def(
			"camp_occupancy",
			[](Api& a, int which) {
				Bitboard b;
				const Err e = a.camp_occupancy(b, which);
				return py::make_tuple(E(e), to_numpy(b, a.map().W, a.map().H));
			},
			py::arg("which") = 0)
		.def("wards", [](Api& a) {
			WardRecord r[64];
			std::uint32_t n = 0;
			const Err e = a.wards(r, 64, &n);
			return py::make_tuple(E(e), std::vector<WardRecord>(r, r + std::min<std::uint32_t>(n, 64)));
		})
		.def("teleports", [](Api& a) {
			TeleportRecord r[16];
			std::uint32_t n = 0;
			const Err e = a.teleports(r, 16, &n);
			return py::make_tuple(E(e), std::vector<TeleportRecord>(r, r + std::min<std::uint32_t>(n, 16)));
		})
		.def("altar_locks", [](Api& a) {
			AltarLockRecord r[64];
			std::uint32_t n = 0;
			const Err e = a.altar_locks(r, 64, &n);
			return py::make_tuple(E(e), std::vector<AltarLockRecord>(r, r + std::min<std::uint32_t>(n, 64)));
		})
		.def("round_number", [](Api& a) {
			std::uint32_t v = 0;
			const Err e = a.round_number(&v);
			return py::make_tuple(E(e), v);
		})
		.def("read_shared_memory", [](Api& a, int off, std::uint32_t n) {
			std::string buf(n, '\0');
			const Err e = a.read_shared_memory(off, reinterpret_cast<std::uint8_t*>(buf.data()), n);
			return py::make_tuple(E(e), py::bytes(buf));
		})
		.def("write_shared_memory", [](Api& a, int off, const py::bytes& data) {
			const std::string s = data;
			return E(a.write_shared_memory(off, reinterpret_cast<const std::uint8_t*>(s.data()), static_cast<std::uint32_t>(s.size())));
		})
		.def("read_draft_memory", [](Api& a, int off, std::uint32_t n) {
			std::string buf(n, '\0');
			const Err e = a.read_draft_memory(off, reinterpret_cast<std::uint8_t*>(buf.data()), n);
			return py::make_tuple(E(e), py::bytes(buf));
		})
		.def("submit_draft_memory", [](Api& a, const py::bytes& data) {
			const std::string s = data;
			return E(a.submit_draft_memory(reinterpret_cast<const std::uint8_t*>(s.data()), static_cast<std::uint32_t>(s.size())));
		})
		// actions
		.def("move_to", [](Api& a, int x, int y) {
			std::int32_t ok = 0;
			const Err e = a.move_to({ x, y }, &ok);
			return py::make_tuple(E(e), ok != 0);
		})
		.def("attack", [](Api& a, std::uint32_t kind, std::uint32_t h) { return E(a.attack(kind, h)); })
		.def(
			"cast",
			[](Api& a, std::uint32_t slot, std::uint32_t kind, std::uint32_t h, int x, int y) {
				std::int32_t ok = 0;
				const Err e = a.cast(slot, kind, h, { x, y }, &ok);
				return py::make_tuple(E(e), ok != 0);
			},
			py::arg("slot"), py::arg("kind") = 0, py::arg("handle") = 0, py::arg("x") = -1, py::arg("y") = -1)
		.def("buy_item", [](Api& a, std::uint32_t item, std::uint32_t count) { return E(a.buy_item(item, count)); })
		.def("buy_consumable", [](Api& a, std::uint32_t t) { return E(a.buy_consumable(t)); })
		.def("sell", [](Api& a, std::uint32_t item) { return E(a.sell(item)); })
		.def("use_consumable", [](Api& a, int t, int x, int y) {
			std::int32_t ok = 0;
			const Err e = a.use_consumable(t, { x, y }, &ok);
			return py::make_tuple(E(e), ok != 0);
		})
		.def("recall", [](Api& a) { return E(a.recall()); })
		.def("cancel_channel", [](Api& a) { return E(a.cancel_channel()); })
		.def("submit_gems", [](Api& a, int x, int y) { return E(a.submit_gems({ x, y })); })
		.def("place_ward", [](Api& a, int x, int y) {
			std::int32_t ok = 0;
			const Err e = a.place_ward({ x, y }, &ok);
			return py::make_tuple(E(e), ok != 0);
		})
		.def("set_priority", [](Api& a, int p) { return E(a.set_priority(p)); })
		.def("resign", [](Api& a) { return E(a.resign()); })
		// draft
		.def("draft_num_rounds", [](Api& a) {
			std::uint8_t v = 0;
			const Err e = a.draft_num_rounds(&v);
			return py::make_tuple(E(e), v);
		})
		.def("draft_get", [](Api& a, int team, std::uint32_t round) {
			std::int32_t v = 0;
			const Err e = a.draft_get(team, round, &v);
			return py::make_tuple(E(e), v);
		})
		.def("draft_champion", [](Api& a, int choice) { return E(a.draft_champion(choice)); })
		// priced geometry
		.def("distance_field", [](Api& a, const py::array_t<bool, py::array::c_style | py::array::forcecast>& walls,
								  const py::array_t<bool, py::array::c_style | py::array::forcecast>& roots, int max_distance) {
			const int W = a.map().W, H = a.map().H;
			const Bitboard w = from_numpy(walls), r = from_numpy(roots);
			Bitboard visited;
			py::array_t<std::uint16_t> d({ H, W });
			a.distance_field(w, r, nullptr, max_distance, d.mutable_data(), visited);
			return d;
		});

	py::class_<Player, PyPlayer, std::shared_ptr<Player>>(m, "Player", "Subclass and implement turn(api); called once per turn (draft: api.champ == -1).")
		.def(py::init<>());
	m.def(
		"builtin_player", [](const std::string& name, std::uint64_t seed) { return std::shared_ptr<Player>(make_player(name, seed)); }, py::arg("name"),
		py::arg("seed") = 1, "Built-in C++ policy: 'starter' or 'idle'.");

	py::class_<Match>(m, "Match")
		.def(py::init([](std::shared_ptr<Map> map, std::shared_ptr<Player> a, std::shared_ptr<Player> b, std::uint64_t seed, bool unlimited,
						 int max_rounds, std::int64_t fuel) {
				 MatchOptions o;
				 o.seed = seed;
				 o.unlimited_fuel = unlimited;
				 o.max_rounds = max_rounds;
				 if (fuel > 0) o.fuel.per_turn = fuel;
				 return std::make_unique<Match>(map, *a, *b, o);
			 }),
			 py::arg("map"), py::arg("a"), py::arg("b"), py::arg("seed") = 1, py::arg("unlimited_fuel") = false, py::arg("max_rounds") = 0,
			 py::arg("fuel_per_turn") = 0, py::keep_alive<1, 3>(), py::keep_alive<1, 4>())
		.def("run",
			 [](Match& mt) {
				 {
					 py::gil_scoped_release nogil;
					 mt.run();
				 }
				 return result_dict(mt);
			 });

	m.def(
		"run_matches",
		[](const std::vector<std::string>& maps, const std::string& a, const std::string& b, int games, int threads, std::uint64_t seed,
		   bool unlimited, int max_rounds) {
			std::vector<std::shared_ptr<const Map>> loaded;
			for (const auto& p : maps) loaded.push_back(load_map(p));
			std::vector<py::dict> out;
			std::vector<std::unique_ptr<Match>> done(static_cast<std::size_t>(games));
			std::vector<std::unique_ptr<Player>> players(2 * static_cast<std::size_t>(games));
			{
				py::gil_scoped_release nogil;
				std::atomic<int> next{ 0 };
				std::vector<std::thread> pool;
				for (int t = 0; t < std::max(1, threads); ++t)
					pool.emplace_back([&] {
						for (int g; (g = next++) < games;)
						{
							const std::uint64_t s = seed + static_cast<std::uint64_t>(g);
							players[2 * g] = make_player(a, 2 * s + 1);
							players[2 * g + 1] = make_player(b, 2 * s + 2);
							MatchOptions o;
							o.seed = s;
							o.unlimited_fuel = unlimited;
							o.max_rounds = max_rounds;
							done[g] = std::make_unique<Match>(loaded[g % loaded.size()], *players[2 * g], *players[2 * g + 1], o);
							done[g]->run();
						}
					});
				for (auto& th : pool) th.join();
			}
			for (int g = 0; g < games; ++g)
			{
				py::dict d = result_dict(*done[g]);
				d["map"] = loaded[g % loaded.size()]->name;
				out.push_back(d);
			}
			return out;
		},
		py::arg("maps"), py::arg("a") = "starter", py::arg("b") = "starter", py::arg("games") = 1, py::arg("threads") = 1, py::arg("seed") = 1,
		py::arg("unlimited_fuel") = false, py::arg("max_rounds") = 0, "Play games between built-in policies on a thread pool (GIL released).");
}
