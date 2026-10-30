// Differential replay: runs a tracer script (oracle/tools/make_script.py) through the
// simulator. Each logged action is re-issued through cbs::Api; every observation line is
// regenerated with the tracer's exact formatting and compared with the engine's.
//
// Usage: replay MAP.map26a SCRIPT [--max-diffs N] [--quiet]
#include <cstdlib>
#include <cinttypes>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
#include <vector>
#include "cbs/coverage.h"
#include "cbs/api.h"

using namespace cbs;

namespace
{
struct Block
{
	std::string kind; // DRAFT or TURN
	int team = 0, round = 0, champ = -1;
	std::vector<std::string> lines; // "O ...", "A ...", "P ...", "L ..."
};

std::string fmt(const char* f, ...)
{
	char buf[4096];
	va_list ap;
	va_start(ap, f);
	vsnprintf(buf, sizeof buf, f, ap);
	va_end(ap);
	return buf;
}

// Mirrors oracle/bots/tracer observe(): returns the lines without the "@@" prefix.
struct Observer
{
	Api& api;
	const Map& m;
	std::vector<std::string> out;

	std::string board(const char* tag, const Bitboard& b)
	{
		std::string s = tag;
		int cur = 0, run = 0;
		for (int i = 0; i < m.W * m.H; ++i)
		{
			const int v = b.test(i % m.W, i / m.W);
			if (v == cur) ++run;
			else
			{
				s += fmt(" %d", run);
				cur = v;
				run = 1;
			}
		}
		s += fmt(" %d", run);
		return s;
	}

	std::string buffs_champ(std::uint32_t h)
	{
		BuffRecord raw[8];
		std::uint32_t n = 0;
		const Err rc = api.champion_buff_data(h, raw, 8, &n);
		if (rc != Err::success) return fmt(" buffs=E%d", static_cast<int>(rc));
		std::string s = " buffs=";
		for (std::uint32_t i = 0; i < n && i < 8; ++i)
		{
			if (raw[i].type == 0) s += fmt("S%d:%.9g;", raw[i].duration, static_cast<double>(raw[i].value));
			else s += fmt("%c%d;", raw[i].type == 1 ? 'T' : 'E', raw[i].duration);
		}
		return s;
	}

	std::string champion(const char* tag, std::uint32_t h, bool self)
	{
		ChampionInfo ci{};
		std::int32_t alive = 0;
		api.champion_is_alive(h, &alive);
		Err rc = api.champion(h, &ci);
		std::string s = fmt("%s %u alive=%d", tag, h, alive);
		if (rc != Err::success) return s + fmt(" E%d", static_cast<int>(rc));
		s += fmt(" t=%d ty=%d pos=%d,%d hp=%.9g mhp=%.9g str=%.9g foc=%.9g ms=%d ar=%d st=%x", ci.team, ci.type, ci.x, ci.y,
				 static_cast<double>(ci.health), static_cast<double>(ci.max_health), static_cast<double>(ci.strength),
				 static_cast<double>(ci.focus), ci.move_speed, ci.attack_range, ci.state);
		std::int32_t cd0 = 0, cd1 = 0;
		const int r0 = static_cast<int>(api.champion_cooldown(h, 0, &cd0)), r1 = static_cast<int>(api.champion_cooldown(h, 1, &cd1));
		s += fmt(" cd=%d,%d", r0 ? -1000 - r0 : cd0, r1 ? -1000 - r1 : cd1);
		s += buffs_champ(h);
		std::uint8_t restr = 0;
		if (api.champion_restrictions(h, &restr) == Err::success) s += fmt(" restr=%x", restr);
		std::uint32_t gems = 0;
		rc = api.champion_gems(h, &gems);
		s += fmt(" gems=%d", rc != Err::success ? -static_cast<int>(rc) : static_cast<int>(gems));
		std::int32_t chan = 0;
		rc = api.champion_channel_time(h, &chan);
		s += fmt(" chan=%d", rc != Err::success ? -static_cast<int>(rc) : chan);
		std::int32_t p0 = 0, p1 = 0;
		const int q0 = static_cast<int>(api.champion_priority(h, false, &p0)), q1 = static_cast<int>(api.champion_priority(h, true, &p1));
		s += fmt(" prio=%d,%d", q0 ? -1000 - q0 : p0, q1 ? -1000 - q1 : p1);
		std::uint32_t items[kNumItems] = {};
		if (api.champion_items(h, items) == Err::success)
		{
			s += " items=";
			for (int i = 0; i < kNumItems; ++i)
				if (items[i]) s += fmt("%d:%u;", i, items[i]);
		}
		if (self)
		{
			std::uint32_t gold = 0;
			api.champion_gold(h, &gold);
			std::uint32_t cons[4] = {};
			api.champion_consumables(h, cons);
			WardResources wr{};
			api.champion_wards(h, &wr);
			Vec2 wp[4];
			std::uint32_t nw = 0;
			api.champion_ward_positions(h, wp, 4, &nw);
			std::int32_t shop0 = 0, shop1 = 0, sell = 0;
			api.champion_can_shop(h, false, &shop0);
			api.champion_can_shop(h, true, &shop1);
			api.champion_can_sell(h, &sell);
			s += fmt(" gold=%u cons=%u,%u,%u,%u ward=%u,%d wpos=", gold, cons[0], cons[1], cons[2], cons[3], wr.charges, wr.cooldown);
			for (std::uint32_t i = 0; i < nw && i < 4; ++i) s += fmt("%d,%d;", wp[i].x, wp[i].y);
			s += fmt(" shop=%d,%d,%d", shop0, shop1, sell);
		}
		return s;
	}

	void observe(char phase)
	{
		std::uint32_t round = 0;
		api.round_number(&round);
		out.push_back(fmt("%c round=%u", phase, round));
		const std::uint32_t me = static_cast<std::uint32_t>(api.my_champion());
		out.push_back(champion("self", me, true));
		Bitboard vis;
		api.vision(vis);
		out.push_back(board("vis", vis));
		std::uint32_t ids[16], n = 0;
		api.allies(ids, 16, &n);
		for (std::uint32_t i = 0; i < n; ++i)
			if (ids[i] != me) out.push_back(champion("ally", ids[i], false));
		api.enemies(ids, 16, &n);
		for (std::uint32_t i = 0; i < n; ++i) out.push_back(champion("enemy", ids[i], false));
		for (std::uint32_t c = 0; c < m.camps.size(); ++c)
		{
			CampRecord cs{};
			if (api.camp(c, &cs) != Err::success) continue;
			std::uint32_t st = 0;
			api.camp_state(c, &st);
			CampBuffRecord b[4];
			std::uint32_t nb = 0;
			api.camp_buffs(c, b, 4, &nb);
			std::string s = fmt("camp %u st=%u pos=%d,%d hp=%.9g mhp=%.9g str=%.9g foc=%.9g cd=%d,%d buffs=", c, st, cs.x, cs.y,
								static_cast<double>(cs.health), static_cast<double>(cs.max_health), static_cast<double>(cs.strength),
								static_cast<double>(cs.focus), cs.cooldowns[0], cs.cooldowns[1]);
			for (std::uint32_t i = 0; i < nb && i < 4; ++i) s += fmt("%u:%.9g:%d;", b[i].type, static_cast<double>(b[i].magnitude), b[i].timer);
			out.push_back(s);
		}
		for (std::uint32_t g = 0; g < m.groups.size(); ++g)
		{
			std::uint32_t st = 0;
			if (api.camp_group_state(g, &st) != Err::success || st == 0) continue;
			std::int32_t cd = 0;
			const int rc = static_cast<int>(api.camp_group_cooldown(g, &cd));
			std::int32_t ct = 0, cs = 0;
			const int rc2 = static_cast<int>(api.camp_group_capture_state(g, &ct, &cs));
			out.push_back(fmt("group %u st=%u cd=%d cap=%d,%d", g, st, rc ? -1000 - rc : cd, rc2 ? -1000 - rc2 : ct, rc2 ? 0 : cs));
		}
		{
			WardRecord w[32];
			std::uint32_t nw = 0;
			api.wards(w, 32, &nw);
			std::string s = "wards";
			for (std::uint32_t i = 0; i < nw && i < 32; ++i) s += fmt(" %u:%d,%d:%d:%u:%u", w[i].team, w[i].x, w[i].y, w[i].timer, w[i].disabled, w[i].owner);
			out.push_back(s);
		}
		{
			TeleportRecord t[16];
			std::uint32_t nt = 0;
			api.teleports(t, 16, &nt);
			std::string s = "tps";
			for (std::uint32_t i = 0; i < nt && i < 16; ++i)
				s += fmt(" %u:%d:%u:%d,%d:%d:%u", t[i].champion, t[i].type, t[i].team, t[i].dx, t[i].dy, t[i].timer, t[i].channel_type);
			out.push_back(s);
		}
		{
			AltarLockRecord l[16];
			std::uint32_t nl = 0;
			api.altar_locks(l, 16, &nl);
			std::string s = "locks";
			for (std::uint32_t i = 0; i < nl && i < 16; ++i) s += fmt(" %u:%u:%u:%d,%d:%u", l[i].kind, l[i].handle, l[i].team, l[i].x, l[i].y, l[i].hits_remaining);
			out.push_back(s);
		}
		std::uint8_t mem[8] = {};
		api.read_shared_memory(0, mem, 8);
		std::uint32_t s0 = 0, s1 = 0;
		api.submitted_gems(0, &s0);
		api.submitted_gems(1, &s1);
		std::string s = "misc mem=";
		for (auto b : mem) s += fmt("%02x", b);
		std::uint8_t dm[16] = {};
		const int drc = static_cast<int>(api.read_draft_memory(0, dm, 16));
		s += fmt(" score=%u,%u dmem=%d:", s0, s1, drc);
		for (auto b : dm) s += fmt("%02x", b);
		out.push_back(s);
	}
};

// Strip volatile fields (fuel) so lines compare on game state only.
std::string normalise(std::string s)
{
	const auto p = s.find(" fuel=");
	if (p != std::string::npos) s.erase(p);
	// Traces recorded before the tracer printed capture state (engine 2.0.0): REPLAY_NO_CAP=1 drops it.
	static const bool no_cap = std::getenv("REPLAY_NO_CAP") != nullptr;
	if (no_cap)
		if (const auto q = s.find(" cap="); q != std::string::npos) s.erase(q);
	return s;
}

std::vector<int> ints(const std::string& s)
{
	std::vector<int> v;
	std::istringstream is(s);
	std::string w;
	while (is >> w)
	{
		char* end = nullptr;
		const long x = std::strtol(w.c_str(), &end, 10);
		if (*end == 0) v.push_back(static_cast<int>(x));
	}
	return v;
}

std::vector<std::uint8_t> hexbytes(const std::string& h)
{
	std::vector<std::uint8_t> v;
	for (std::size_t i = 0; i + 1 < h.size(); i += 2) v.push_back(static_cast<std::uint8_t>(std::stoi(h.substr(i, 2), nullptr, 16)));
	return v;
}

struct Replayer
{
	Game& g;
	int max_diffs;
	bool quiet;
	int diffs = 0, lines_ok = 0, actions_ok = 0;
	std::map<std::string, int> diff_kinds;
	std::string context;

	void report(const std::string& what, const std::string& want, const std::string& got)
	{
		++diffs;
		const std::string kind = what + ":" + want.substr(0, want.find(' '));
		diff_kinds[kind]++;
		if (!quiet && diffs <= max_diffs)
			std::printf("DIFF %s [%s]\n  engine: %s\n  sim:    %s\n", what.c_str(), context.c_str(), want.c_str(), got.c_str());
	}

	void compare_obs(const std::vector<std::string>& want, const std::vector<std::string>& got, const char* phase)
	{
		std::size_t i = 0, j = 0;
		while (i < want.size() || j < got.size())
		{
			const std::string a = i < want.size() ? normalise(want[i]) : "<none>";
			const std::string b = j < got.size() ? normalise(got[j]) : "<none>";
			if (a == b)
			{
				++lines_ok;
				++i, ++j;
				continue;
			}
			// Resynchronise on line kinds (e.g. a camp line missing on one side).
			const std::string ka = a.substr(0, a.find(' ')), kb = b.substr(0, b.find(' '));
			if (ka == kb && ka != "camp" && ka != "group")
			{
				report(phase, a, b);
				++i, ++j;
			}
			else if (j < got.size() && (i >= want.size() || std::find_if(want.begin() + i, want.end(), [&](const std::string& w) { return normalise(w) == b; }) == want.end()))
			{
				report(std::string(phase) + "+extra", "<absent>", b);
				++j;
			}
			else
			{
				report(std::string(phase) + "+missing", a, "<absent>");
				++i;
			}
		}
	}

	// Executes one logged action line and returns the formatted result ("rc [ok]").
	std::string run_action(Api& api, const std::string& line)
	{
		std::istringstream is(line);
		std::string tag, name;
		is >> tag >> name;
		std::vector<std::string> args;
		for (std::string w; is >> w && w != "->";) args.push_back(w);
		auto I = [&](int k) { return std::stoi(args.at(k)); };
		std::int32_t ok = 0;
		Err rc;
		if (name == "move")
		{
			rc = api.move_to({ I(0), I(1) }, &ok);
			return fmt("%d %d", static_cast<int>(rc), ok);
		}
		if (name == "attack") return fmt("%d", static_cast<int>(api.attack(I(0), I(1))));
		if (name == "cast")
		{
			rc = api.cast(I(0), I(1), I(2), { I(3), I(4) }, &ok);
			return fmt("%d %d", static_cast<int>(rc), ok);
		}
		if (name == "buy") return fmt("%d", static_cast<int>(api.buy_item(I(0), I(1))));
		if (name == "buyc") return fmt("%d", static_cast<int>(api.buy_consumable(I(0))));
		if (name == "sell") return fmt("%d", static_cast<int>(api.sell(I(0))));
		if (name == "use")
		{
			rc = api.use_consumable(I(0), { I(1), I(2) }, &ok);
			return fmt("%d %d", static_cast<int>(rc), ok);
		}
		if (name == "recall") return fmt("%d", static_cast<int>(api.recall()));
		if (name == "cancel") return fmt("%d", static_cast<int>(api.cancel_channel()));
		if (name == "submit") return fmt("%d", static_cast<int>(api.submit_gems({ I(0), I(1) })));
		if (name == "ward")
		{
			rc = api.place_ward({ I(0), I(1) }, &ok);
			return fmt("%d %d", static_cast<int>(rc), ok);
		}
		if (name == "prio") return fmt("%d", static_cast<int>(api.set_priority(I(0))));
		if (name == "wmem")
		{
			const std::uint8_t v = static_cast<std::uint8_t>(std::stoi(args.at(1), nullptr, 16));
			return fmt("%d", static_cast<int>(api.write_shared_memory(I(0), &v, 1)));
		}
		if (name == "pick") return fmt("%d", static_cast<int>(api.draft_champion(I(0))));
		if (name == "draftmem")
		{
			auto b = hexbytes(args.at(0));
			return fmt("%d", static_cast<int>(api.submit_draft_memory(b.data(), static_cast<std::uint32_t>(b.size()))));
		}
		return "?";
	}

	void do_actions(Api& api, const Block& b)
	{
		for (const auto& l : b.lines)
		{
			if (l.rfind("A ", 0) != 0) continue;
			const std::string want = l.substr(l.find("-> ") + 3);
			const std::string got = run_action(api, l);
			if (got == want) ++actions_ok;
			else report("action", l.substr(2), got);
		}
	}

	static std::vector<std::string> phase_lines(const Block& b, char p)
	{
		std::vector<std::string> v;
		for (const auto& l : b.lines)
			if (l.size() > 2 && l[0] == p && l[1] == ' ') v.push_back(l.substr(2));
		return v;
	}

	void draft_block(const Block& b)
	{
		Api api(g, b.team, -1);
		context = fmt("draft team %d round %d", b.team, g.draft.round);
		// "draft rounds=N t:r:pick..."
		std::uint8_t rounds = 0;
		api.draft_num_rounds(&rounds);
		std::string s = fmt("draft rounds=%u", rounds);
		for (int t = 0; t < 2; ++t)
			for (int r = 0; r < rounds; ++r)
			{
				std::int32_t pick = 0;
				const Err rc = api.draft_get(t, static_cast<std::uint32_t>(r), &pick);
				s += fmt(" %d:%d:%d", t, r, rc != Err::success ? -static_cast<int>(rc) : pick);
			}
		const std::string want = b.lines.at(0).substr(2);
		if (want == s) ++lines_ok;
		else report("draft", want, s);
		do_actions(api, b);
	}

	void turn_block(const Block& b)
	{
		Api api(g, b.team, b.champ);
		context = fmt("round %d champ %d", b.round, b.champ);
		Observer o{ api, g.map(), {} };
		o.observe('O');
		compare_obs(phase_lines(b, 'O'), o.out, "O");
		do_actions(api, b);
		Observer p{ api, g.map(), {} };
		p.observe('P');
		compare_obs(phase_lines(b, 'P'), p.out, "P");
	}
};
} // namespace

int main(int argc, char** argv)
{
	if (argc < 3)
	{
		std::fprintf(stderr, "usage: replay MAP SCRIPT [--max-diffs N] [--quiet] [--rounds N]\n");
		return 2;
	}
	int max_diffs = 20, max_rounds = 1 << 30, watch_camp = -1, watch_from = 0, watch_to = 0, watch_group = -1, watch_champ = -1;
	bool quiet = false;
	for (int i = 3; i < argc; ++i)
	{
		if (!std::strcmp(argv[i], "--max-diffs")) max_diffs = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--quiet")) quiet = true;
		else if (!std::strcmp(argv[i], "--rounds")) max_rounds = std::atoi(argv[++i]);
		else if (!std::strcmp(argv[i], "--watch-group"))
		{
			watch_group = std::atoi(argv[++i]);
			watch_from = std::atoi(argv[++i]);
			watch_to = std::atoi(argv[++i]);
		}
		else if (!std::strcmp(argv[i], "--watch-champ"))
		{
			watch_champ = std::atoi(argv[++i]);
			watch_from = std::atoi(argv[++i]);
			watch_to = std::atoi(argv[++i]);
		}
		else if (!std::strcmp(argv[i], "--watch-camp"))
		{
			watch_camp = std::atoi(argv[++i]);
			watch_from = std::atoi(argv[++i]);
			watch_to = std::atoi(argv[++i]);
		}
	}
	auto map = load_map(argv[1]);
	std::ifstream f(argv[2]);
	std::vector<Block> blocks;
	std::string result_line;
	for (std::string line; std::getline(f, line);)
	{
		if (line.rfind("RESULT ", 0) == 0)
		{
			result_line = line;
			continue;
		}
		if (line.rfind("DRAFT ", 0) == 0)
		{
			Block b;
			b.kind = "DRAFT";
			b.team = std::stoi(line.substr(6));
			blocks.push_back(b);
		}
		else if (line.rfind("TURN ", 0) == 0)
		{
			Block b;
			b.kind = "TURN";
			std::sscanf(line.c_str(), "TURN %d %d %d", &b.team, &b.round, &b.champ);
			blocks.push_back(b);
		}
		else if (line == "END" || line.rfind("MAP ", 0) == 0)
			continue;
		else if (!blocks.empty())
			blocks.back().lines.push_back(line);
	}

	Game g(map);
	Replayer r{ g, max_diffs, quiet };
	std::size_t bi = 0;
	// Draft: blocks come in team-A, team-B pairs per draft round. The draft size is the
	// "rounds=" value the engine reported.
	for (; bi < blocks.size() && blocks[bi].kind == "DRAFT"; ++bi)
	{
		if (g.draft.round == 0 && bi == 0)
		{
			const auto& l = blocks[bi].lines.at(0);
			g.draft.rounds = std::atoi(l.c_str() + l.find("rounds=") + 7);
		}
		r.draft_block(blocks[bi]);
		if (blocks[bi].team == 1)
		{
			std::uint64_t rng = 1;
			g.draft_end_round(rng);
		}
	}
	g.start_play();
	int order_diffs = 0;
	std::vector<int> order;
	// After the last logged turn, finish that round without bots: the game may end at a turn
	// start (a tribute completing) or at the round limit.
	bool stop = false;
	while (!g.over && g.round < max_rounds && !stop)
	{
		g.begin_round();
		g.turn_order(order);
		if (watch_group >= 0 && g.round >= watch_from && g.round <= watch_to)
		{
			const Group& G = g.groups[watch_group];
			std::printf("WATCHG r%d group %d state=%d timer=%d capture=%d/%d camps:", g.round, watch_group, static_cast<int>(G.state), G.respawn_timer,
						G.capture_team, G.capture_timer);
			for (int h : g.map().groups[watch_group].camps)
				std::printf(" %d:%d@%d,%d(occ %d)", h, static_cast<int>(g.camps[h].life), g.camps[h].pos.x, g.camps[h].pos.y, g.champion_at(g.camps[h].pos));
			std::printf("\n");
		}
		if (watch_champ >= 0 && g.round >= watch_from && g.round <= watch_to)
		{
			const Champion& c = g.champs[watch_champ];
			std::printf("WATCHC r%d champ %d alive=%d pos=%d,%d hp=%.9g gold=%.9g gems=%u\n", g.round, watch_champ, c.alive ? 1 : 0, c.pos.x, c.pos.y,
						static_cast<double>(c.hp), c.gold(), static_cast<unsigned>(c.gems));
		}
		if (watch_camp >= 0 && g.round >= watch_from && g.round <= watch_to)
		{
			const Camp& k = g.camps[watch_camp];
			std::printf("WATCH r%d camp %d life=%d hp=%g sleep=%d buffs=", g.round, watch_camp, static_cast<int>(k.life), static_cast<double>(k.hp), k.sleep_timer);
			for (int i = 0; i < k.buffs.n; ++i) std::printf("%d:%d;", static_cast<int>(k.buffs.b[i].type), k.buffs.b[i].duration);
			std::printf(" champs:");
			for (auto& ch : g.champs)
				if (ch.alive) std::printf(" %d@%d,%d(d%d)", ch.id, ch.pos.x, ch.pos.y, chebyshev(ch.pos, k.pos));
			std::printf("\n");
		}
		for (int c : order)
		{
			if (bi >= blocks.size())
			{
				// No more logged turns: the engine must have ended the game at this turn start
				// (a completing tribute); otherwise this champion's turn would have been logged.
				g.begin_turn(c);
				if (!g.over) std::printf("NOTE: trace ended but the sim game continues at round %d champ %d\n", g.round, c);
				stop = true;
				break;
			}
			const Block& b = blocks[bi];
			if (b.round != g.round || b.champ != c)
			{
				if (order_diffs++ < 10)
					std::printf("ORDER mismatch: engine has round %d champ %d, sim expects round %d champ %d\n", b.round, b.champ, g.round, c);
			}
			const int who = (b.round == g.round) ? b.champ : c;
			g.begin_turn(who);
			r.turn_block(b);
			g.end_turn(who);
			++bi;
			if (g.over) break;
		}
		if (stop) break;
		g.end_round();
	}
	std::printf("replayed %zu/%zu blocks, %d rounds; lines ok=%d, actions ok=%d, diffs=%d, order mismatches=%d\n", bi, blocks.size(), g.round,
				r.lines_ok, r.actions_ok, r.diffs, order_diffs);
	std::printf("sim result: over=%d winner=%d reason=%d rounds=%d score=%u,%u\n", g.over, g.result.winner, g.result.reason, g.result.rounds,
				g.teams[0].submitted, g.teams[1].submitted);
	if (bi < blocks.size()) std::printf("WARNING: sim ended before the trace (%zu blocks left)\n", blocks.size() - bi);
	int result_diff = 0;
	if (!result_line.empty())
	{
		char outcome[32] = {};
		int rounds = 0;
		unsigned ga = 0, gb = 0;
		std::sscanf(result_line.c_str(), "RESULT %31s %d %u,%u", outcome, &rounds, &ga, &gb);
		const int want = std::string(outcome) == "teamA" ? 0 : 1;
		result_diff = !(g.over && g.result.winner == want && g.teams[0].submitted == ga && g.teams[1].submitted == gb);
		std::printf("engine result: %s rounds=%d score=%u,%u -> %s\n", outcome, rounds, ga, gb, result_diff ? "MISMATCH" : "match");
	}
	std::vector<std::pair<int, std::string>> kinds;
	for (auto& [k, v] : r.diff_kinds) kinds.push_back({ v, k });
	std::sort(kinds.rbegin(), kinds.rend());
	for (std::size_t i = 0; i < kinds.size() && i < 15; ++i) std::printf("  %6d %s\n", kinds[i].first, kinds[i].second.c_str());
#ifdef CBS_RULE_COVERAGE
	cbs::cov::dump(stdout);
#endif
	return (r.diffs || result_diff) ? 1 : 0;
}
