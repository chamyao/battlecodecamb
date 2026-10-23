// Oracle bot: plays a seeded semi-random policy that exercises every action type and logs,
// as "@@" lines, a full observation at the start and end of each turn plus every raw action
// call with its return code. The simulator replays the logged actions and must reproduce the
// observations exactly (see oracle/README.md for the line format).
#include <cambc.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>
#include "config.h"

using namespace cambc;
using namespace cambc::detail;

namespace
{
std::uint64_t rng_state = 1;
std::uint32_t rnd()
{
	rng_state ^= rng_state << 13;
	rng_state ^= rng_state >> 7;
	rng_state ^= rng_state << 17;
	return static_cast<std::uint32_t>(rng_state >> 11);
}
bool chance(int pct) { return static_cast<int>(rnd() % 100) < pct; }
int rint(int lo, int hi) { return lo + static_cast<int>(rnd() % static_cast<std::uint32_t>(hi - lo + 1)); }

int W, H;
std::vector<std::uint8_t> blocked_static; // walls | holes | altars
std::vector<vec2> altars;
std::vector<std::uint32_t> all_camps;
std::vector<std::uint32_t> camp_group_of;
std::vector<vec2> camp_spawn;
std::uint32_t num_groups;
aabb spawn[2];
int me, my_team;

bool in_spawn(int team, vec2 p) { return p.x >= spawn[team].min_x && p.x < spawn[team].max_x && p.y >= spawn[team].min_y && p.y < spawn[team].max_y; }
bool in_bounds(vec2 p) { return p.x >= 0 && p.y >= 0 && p.x < W && p.y < H; }

void print_board(const char* tag, const std::uint64_t* raw)
{
	bitboard b;
	sdk_Bitboard_ImportRawBuffer(b.ptr(), reinterpret_cast<const std::uint8_t*>(raw), bitboard::raw_buffer_size());
	auto lin = b.export_linear_buffer();
	// Run-length encode the bit sequence (alternating runs starting with zeros).
	std::printf("@@%s", tag);
	int cur = 0, run = 0;
	for (int i = 0; i < W * H; ++i)
	{
		int v = lin[i / 8] >> (i % 8) & 1;
		if (v == cur) ++run;
		else { std::printf(" %d", run); cur = v; run = 1; }
	}
	std::printf(" %d\n", run);
}

void print_buffs_champ(std::uint32_t h)
{
	std::array<buff_data, 8> raw{};
	std::uint32_t n{};
	int rc = sdk_champion_buff_data(h, raw.data(), raw.size(), &n);
	if (rc) { std::printf(" buffs=E%d", rc); return; }
	std::printf(" buffs=");
	for (std::uint32_t i = 0; i < n; ++i)
	{
		if (raw[i].type == 0) std::printf("S%d:%.9g;", raw[i].data.shield.duration, raw[i].data.shield.value);
		else std::printf("%c%d;", raw[i].type == 1 ? 'T' : 'E', raw[i].data.stun.duration);
	}
}

void print_champion(const char* tag, std::uint32_t h, bool self)
{
	champion_info ci{};
	std::int32_t alive{};
	sdk_champion_is_alive(h, &alive);
	int rc = sdk_champion(h, &ci);
	std::printf("@@%s %u alive=%d", tag, h, alive);
	if (rc) { std::printf(" E%d\n", rc); return; }
	std::printf(" t=%d ty=%d pos=%d,%d hp=%.9g mhp=%.9g str=%.9g foc=%.9g ms=%d ar=%d st=%x", ci.team, ci.type, ci.x, ci.y, ci.health,
		ci.max_health, ci.strength, ci.focus, ci.move_speed, ci.attack_range, ci.state);
	std::int32_t cd0{}, cd1{};
	int r0 = sdk_champion_cooldown(h, 0, &cd0), r1 = sdk_champion_cooldown(h, 1, &cd1);
	std::printf(" cd=%d,%d", r0 ? -1000 - r0 : cd0, r1 ? -1000 - r1 : cd1);
	print_buffs_champ(h);
	std::uint8_t restr{};
	if (sdk_champion_restrictions(h, &restr) == 0) std::printf(" restr=%x", restr);
	std::uint32_t gems{};
	rc = sdk_champion_gems(h, &gems);
	std::printf(" gems=%d", rc ? -rc : static_cast<int>(gems));
	std::int32_t chan{};
	rc = sdk_champion_channel_time(h, &chan);
	std::printf(" chan=%d", rc ? -rc : chan);
	std::int32_t p0{}, p1{};
	int q0 = sdk_bc_champion_priority(h, 0, &p0), q1 = sdk_bc_champion_priority(h, 1, &p1);
	std::printf(" prio=%d,%d", q0 ? -1000 - q0 : p0, q1 ? -1000 - q1 : p1);
	std::array<std::uint32_t, 42> items{};
	if (sdk_champion_items(h, items.data()) == 0)
	{
		std::printf(" items=");
		for (int i = 0; i < 42; ++i)
			if (items[i]) std::printf("%d:%u;", i, items[i]);
	}
	if (self)
	{
		std::uint32_t gold{};
		sdk_champion_gold(h, &gold);
		std::array<std::uint32_t, 4> cons{};
		sdk_champion_consumables(h, cons.data());
		ward_resources wr{};
		sdk_champion_wards(h, &wr);
		std::array<position, 4> wp{};
		std::uint32_t nw{};
		sdk_champion_ward_positions(h, wp.data(), wp.size(), &nw);
		std::int32_t shop0{}, shop1{}, sell{};
		sdk_champion_can_shop(h, 0, &shop0);
		sdk_champion_can_shop(h, 1, &shop1);
		sdk_champion_can_sell(h, &sell);
		std::printf(" gold=%u cons=%u,%u,%u,%u ward=%u,%d wpos=", gold, cons[0], cons[1], cons[2], cons[3], wr.charges, wr.cooldown);
		for (std::uint32_t i = 0; i < nw; ++i) std::printf("%d,%d;", wp[i].x, wp[i].y);
		std::printf(" shop=%d,%d,%d", shop0, shop1, sell);
	}
	std::printf("\n");
}

void observe(char phase)
{
	std::uint32_t round{};
	sdk_bc_round_number(&round);
	std::printf("@@%c round=%u fuel=%lld\n", phase, round, static_cast<long long>(sdk_fuel_remaining()));
	print_champion("self", static_cast<std::uint32_t>(me), true);
	bitboard vis;
	sdk_vision(vis.ptr());
	print_board("vis", vis.ptr());
	std::array<std::uint32_t, 16> ids{};
	std::uint32_t n{};
	sdk_allies(ids.data(), ids.size(), &n);
	for (std::uint32_t i = 0; i < n; ++i)
		if (static_cast<int>(ids[i]) != me) print_champion("ally", ids[i], false);
	sdk_enemies(ids.data(), ids.size(), &n);
	for (std::uint32_t i = 0; i < n; ++i) print_champion("enemy", ids[i], false);
	for (auto c : all_camps)
	{
		detail::camp_state cs{};
		if (sdk_camp(c, &cs) != 0) continue;
		std::uint32_t st{};
		sdk_camp_state(c, &st);
		std::array<camp_buff_data, 4> b{};
		std::uint32_t nb{};
		sdk_camp_buffs(c, b.data(), b.size(), &nb);
		std::printf("@@camp %u st=%u pos=%d,%d hp=%.9g mhp=%.9g str=%.9g foc=%.9g cd=%d,%d buffs=", c, st, cs.x, cs.y, cs.health, cs.max_health,
			cs.strength, cs.focus, cs.cooldowns[0], cs.cooldowns[1]);
		for (std::uint32_t i = 0; i < nb; ++i) std::printf("%u:%.9g:%d;", b[i].type, b[i].magnitude, b[i].timer);
		std::printf("\n");
	}
	for (std::uint32_t g = 0; g < num_groups; ++g)
	{
		std::uint32_t st{};
		if (sdk_camp_group_state(g, &st) != 0 || st == 0) continue;
		std::int32_t cd{};
		int rc = sdk_camp_group_cooldown(g, &cd);
		std::printf("@@group %u st=%u cd=%d\n", g, st, rc ? -1000 - rc : cd);
	}
	{
		std::array<ward_info, 32> w{};
		std::uint32_t nw{};
		sdk_wards(w.data(), w.size(), &nw);
		std::printf("@@wards");
		for (std::uint32_t i = 0; i < nw && i < w.size(); ++i)
			std::printf(" %u:%d,%d:%d:%u:%u", w[i].team, w[i].x, w[i].y, w[i].timer, w[i].disabled, w[i].owner);
		std::printf("\n");
	}
	{
		std::array<teleport_info, 16> t{};
		std::uint32_t nt{};
		sdk_teleports(t.data(), t.size(), &nt);
		std::printf("@@tps");
		for (std::uint32_t i = 0; i < nt && i < t.size(); ++i)
			std::printf(" %u:%d:%u:%d,%d:%d:%u", t[i].champion, t[i].type, t[i].team, t[i].destination.x, t[i].destination.y, t[i].timer,
				t[i].channel_type);
		std::printf("\n");
	}
	{
		std::array<altar_lock_info, 16> l{};
		std::uint32_t nl{};
		sdk_altar_locks(l.data(), l.size(), &nl);
		std::printf("@@locks");
		for (std::uint32_t i = 0; i < nl && i < l.size(); ++i)
			std::printf(" %u:%u:%u:%d,%d:%u", l[i].kind, l[i].handle, l[i].team, l[i].x, l[i].y, l[i].hits_remaining);
		std::printf("\n");
	}
	std::array<std::uint8_t, 8> mem{};
	sdk_read_shared_memory(0, mem.data(), 8);
	std::uint32_t s0{}, s1{};
	sdk_bc_submitted_gems(0, &s0);
	sdk_bc_submitted_gems(1, &s1);
	std::printf("@@misc mem=");
	for (auto b : mem) std::printf("%02x", b);
	std::array<std::uint8_t, 16> dm{};
	int drc = sdk_read_draft_memory(0, dm.data(), 16);
	std::printf(" score=%u,%u dmem=%d:", s0, s1, drc);
	for (auto b : dm) std::printf("%02x", b);
	std::printf("\n");
}

// ---- action wrappers: each logs the raw call and its result ----
int act_move(vec2 p)
{
	std::int32_t ok{};
	int rc = sdk_move_to(p.x, p.y, &ok);
	std::printf("@@A move %d %d -> %d %d\n", p.x, p.y, rc, ok);
	return rc == 0 && ok;
}
int act_attack(std::uint32_t kind, std::uint32_t h)
{
	int rc = sdk_attack(kind, h);
	std::printf("@@A attack %u %u -> %d\n", kind, h, rc);
	return rc == 0;
}
int act_cast(std::uint32_t slot, std::uint32_t kind, std::uint32_t h, vec2 p)
{
	std::int32_t ok{};
	int rc = sdk_cast(slot, kind, h, p.x, p.y, &ok);
	std::printf("@@A cast %u %u %u %d %d -> %d %d\n", slot, kind, h, p.x, p.y, rc, ok);
	return rc == 0 && ok;
}
void act_buy(std::uint32_t item, std::uint32_t n) { std::printf("@@A buy %u %u -> %d\n", item, n, sdk_buy_item(item, n)); }
void act_buyc(std::uint32_t c) { std::printf("@@A buyc %u -> %d\n", c, sdk_buy_consumable(c)); }
void act_sell(std::uint32_t item) { std::printf("@@A sell %u -> %d\n", item, sdk_sell(item)); }
int act_use(std::uint32_t c, vec2 p)
{
	std::int32_t ok{};
	int rc = sdk_use_consumable(static_cast<std::int32_t>(c), p.x, p.y, &ok);
	std::printf("@@A use %u %d %d -> %d %d\n", c, p.x, p.y, rc, ok);
	return rc == 0 && ok;
}
void act_recall() { std::printf("@@A recall -> %d\n", sdk_recall()); }
void act_cancel() { std::printf("@@A cancel -> %d\n", sdk_cancel_channel()); }
int act_submit(vec2 p)
{
	int rc = sdk_submit_gems(p.x, p.y);
	std::printf("@@A submit %d %d -> %d\n", p.x, p.y, rc);
	return rc == 0;
}
int act_ward(vec2 p)
{
	std::int32_t ok{};
	int rc = sdk_place_ward(p.x, p.y, &ok);
	std::printf("@@A ward %d %d -> %d %d\n", p.x, p.y, rc, ok);
	return rc == 0 && ok;
}
void act_prio(int p) { std::printf("@@A prio %d -> %d\n", p, sdk_set_priority(p)); }
void act_wmem(int off, std::uint8_t v) { std::printf("@@A wmem %d %02x -> %d\n", off, v, sdk_write_shared_memory(off, &v, 1)); }

// ---- policy helpers ----
struct Unit
{
	std::uint32_t kind, handle;
	vec2 pos;
	float hp;
	int team;
	bool awake;
};

std::vector<Unit> visible_units(bool include_self)
{
	std::vector<Unit> out;
	std::array<std::uint32_t, 16> ids{};
	std::uint32_t n{};
	for (int side = 0; side < 2; ++side)
	{
		if (side == 0) sdk_allies(ids.data(), ids.size(), &n);
		else sdk_enemies(ids.data(), ids.size(), &n);
		for (std::uint32_t i = 0; i < n; ++i)
		{
			if (!include_self && static_cast<int>(ids[i]) == me) continue;
			champion_info ci{};
			if (sdk_champion(ids[i], &ci) != 0 || !(ci.state & 1)) continue;
			out.push_back({ 1, ids[i], { ci.x, ci.y }, ci.health, ci.team, false });
		}
	}
	for (auto c : all_camps)
	{
		detail::camp_state cs{};
		std::uint32_t st{};
		if (sdk_camp(c, &cs) != 0 || sdk_camp_state(c, &st) != 0 || st == 0) continue;
		out.push_back({ 2, c, { cs.x, cs.y }, cs.health, -1, st == 1 });
	}
	return out;
}

int cheb(vec2 a, vec2 b) { return std::max(std::abs(a.x - b.x), std::abs(a.y - b.y)); }

void step_towards(const champion_info& ci, const std::vector<vec2>& goals, const std::vector<Unit>& units)
{
	std::vector<std::uint8_t> blk = blocked_static;
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
			if (in_spawn(1 - my_team, { x, y })) blk[y * W + x] = 1;
	for (auto& u : units) blk[u.pos.y * W + u.pos.x] = 1;
	// BFS from goals.
	std::vector<int> dist(W * H, 1 << 30);
	std::vector<int> q;
	for (auto g : goals)
		if (in_bounds(g) && dist[g.y * W + g.x] != 0)
		{
			dist[g.y * W + g.x] = 0;
			q.push_back(g.y * W + g.x);
		}
	for (std::size_t i = 0; i < q.size(); ++i)
	{
		int cx = q[i] % W, cy = q[i] / W;
		for (int dy = -1; dy <= 1; ++dy)
			for (int dx = -1; dx <= 1; ++dx)
			{
				int nx = cx + dx, ny = cy + dy;
				if ((dx || dy) && nx >= 0 && ny >= 0 && nx < W && ny < H && dist[ny * W + nx] > dist[q[i]] + 1 &&
					(!blk[ny * W + nx] || (nx == ci.x && ny == ci.y)))
				{
					dist[ny * W + nx] = dist[q[i]] + 1;
					q.push_back(ny * W + nx);
				}
			}
	}
	vec2 best{ ci.x, ci.y };
	int bd = dist[ci.y * W + ci.x];
	for (int dy = -1; dy <= 1; ++dy)
		for (int dx = -1; dx <= 1; ++dx)
		{
			vec2 p{ ci.x + dx, ci.y + dy };
			if (in_bounds(p) && !blk[p.y * W + p.x] && dist[p.y * W + p.x] < bd)
			{
				bd = dist[p.y * W + p.x];
				best = p;
			}
		}
	if (best != vec2{ ci.x, ci.y }) act_move(best);
	else if (chance(30)) act_move({ ci.x + rint(-1, 1), ci.y + rint(-1, 1) });
}

void setup()
{
	metadata md{};
	sdk_bc_metadata(&md);
	W = md.width;
	H = md.height;
	me = sdk_my_champion();
	my_team = sdk_my_team();
	bitboard walls, holes, alt;
	sdk_bc_map_mask(0, walls.ptr());
	sdk_bc_map_mask(2, holes.ptr());
	sdk_bc_map_mask(3, alt.ptr());
	blocked_static.assign(W * H, 0);
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
		{
			if (walls.is_set({ x, y }) || holes.is_set({ x, y }) || alt.is_set({ x, y })) blocked_static[y * W + x] = 1;
			if (alt.is_set({ x, y })) altars.push_back({ x, y });
		}
	sdk_spawn_region(0, &spawn[0]);
	sdk_spawn_region(1, &spawn[1]);
	sdk_map_num_camp_groups(&num_groups);
	for (std::uint32_t g = 0; g < num_groups; ++g)
	{
		std::uint32_t n{};
		sdk_map_camp_group_num_camps(g, &n);
		std::vector<std::uint32_t> cs(n);
		sdk_map_camp_group_camps(g, cs.data(), n, &n);
		for (auto c : cs)
		{
			camp_info info{};
			sdk_map_camp_info(c, &info);
			if (c >= camp_spawn.size())
			{
				camp_spawn.resize(c + 1);
				camp_group_of.resize(c + 1);
			}
			camp_spawn[c] = { info.x, info.y };
			camp_group_of[c] = g;
			all_camps.push_back(c);
		}
	}
	std::sort(all_camps.begin(), all_camps.end());
}

void play_turn(std::uint32_t round)
{
	champion_info ci{};
	sdk_champion(static_cast<std::uint32_t>(me), &ci);
	const vec2 pos{ ci.x, ci.y };
	const bool alive = ci.state & 1;
	std::uint32_t gold{}, gems{};
	sdk_champion_gold(me, &gold);
	sdk_champion_gems(me, &gems);
	std::int32_t can_shop{};
	sdk_champion_can_shop(me, 0, &can_shop);
	std::array<std::uint32_t, 4> cons{};
	sdk_champion_consumables(me, cons.data());

	if (chance(5)) act_prio(rint(-3, 12));
	if (chance(8)) act_wmem(rint(0, 8), static_cast<std::uint8_t>(rnd()));

	// Shopping: random shards, consumables, occasional invalid purchases and Tavi sales.
	if (can_shop || chance(3))
	{
		if (gold >= 30 && chance(70))
		{
			const std::uint32_t item = static_cast<std::uint32_t>(rint(0, 6)) * 6 + static_cast<std::uint32_t>(rint(0, 2)) * 2;
			act_buy(item, static_cast<std::uint32_t>(rint(1, std::max(1, static_cast<int>(gold / 30)))));
		}
		if (chance(25)) act_buyc(chance(50) ? 0 : 2);
		if (chance(3)) act_buy(static_cast<std::uint32_t>(rint(0, 43)), static_cast<std::uint32_t>(rint(0, 2)));
		if (ci.type == 11 && chance(10)) act_sell(static_cast<std::uint32_t>(rint(0, 41)));
	}
	if (!alive) return;

	const bool channeling = ci.state & (2 | 4 | 4096);
	if (channeling)
	{
		if (chance(8)) act_cancel();
		if (chance(5)) act_move({ ci.x + rint(-1, 1), ci.y + rint(-1, 1) });
		return;
	}
	auto units = visible_units(true);
	std::vector<Unit> enemies, camps, allies;
	for (auto& u : units)
	{
		if (u.kind == 2) camps.push_back(u);
		else if (u.team != my_team) enemies.push_back(u);
		else if (static_cast<int>(u.handle) != me) allies.push_back(u);
	}

	// Ward placement (sometimes invalid).
	ward_resources wr{};
	sdk_champion_wards(me, &wr);
	if ((wr.charges > 0 && chance(15)) || chance(2)) act_ward({ ci.x + rint(-3, 3), ci.y + rint(-3, 3) });

	// Low health: recall.
	if (!in_spawn(my_team, pos) && ci.health < ci.max_health * 0.3f && chance(80))
	{
		act_recall();
		return;
	}
	if (chance(1)) act_recall();

	// Altar interactions.
	for (auto a : altars)
	{
		if (cheb(a, pos) <= 2 && cons[2] && chance(30)) act_use(2, a);
		if (cheb(a, pos) <= 1 && gems > 0 && chance(85))
		{
			if (act_submit(a)) return;
		}
	}
	std::array<altar_lock_info, 16> locks{};
	std::uint32_t nl{};
	sdk_altar_locks(locks.data(), locks.size(), &nl);
	for (std::uint32_t i = 0; i < nl; ++i)
		if (static_cast<int>(locks[i].team) != my_team && cheb({ locks[i].x, locks[i].y }, pos) <= ci.attack_range && chance(70))
			act_attack(locks[i].kind, locks[i].handle);

	// Teleport crystal.
	if (cons[0] && chance(6)) act_use(0, { ci.x + rint(-4, 4), ci.y + rint(-4, 4) });

	// Abilities.
	if (chance(45))
	{
		const std::uint32_t slot = static_cast<std::uint32_t>(rint(0, 1));
		ability_props props{};
		sdk_champion_ability_props(me, slot, &props);
		std::vector<Unit> cand;
		if (props.targets & 2) cand.insert(cand.end(), enemies.begin(), enemies.end());
		if (props.targets & 1) cand.insert(cand.end(), camps.begin(), camps.end());
		if (props.targets & 4) cand.insert(cand.end(), allies.begin(), allies.end());
		const int range = static_cast<int>(props.payload.damage.range);
		if (props.targets & 8)
			act_cast(slot, chance(80) ? 0 : 1, chance(80) ? 0 : static_cast<std::uint32_t>(me), chance(80) ? vec2{ -1, -1 } : pos);
		else if (!cand.empty() && chance(75))
		{
			auto& u = cand[rnd() % cand.size()];
			if (props.targets & 16 && chance(50)) act_cast(slot, 0, 0, u.pos);
			else act_cast(slot, u.kind, u.handle, { -1, -1 });
		}
		else if (props.targets & 16)
			act_cast(slot, 0, 0, { ci.x + rint(-range - 1, range + 1), ci.y + rint(-range - 1, range + 1) });
		else if (chance(20))
			act_cast(slot, 0, 0, { -1, -1 });
	}

	// Basic attack: enemies first, then camps (prefer awake, then lowest health).
	auto attack_best = [&]() -> bool
	{
		const Unit* best = nullptr;
		for (auto& u : enemies)
			if (cheb(u.pos, pos) <= ci.attack_range && (!best || u.hp < best->hp)) best = &u;
		if (!best)
			for (auto& u : camps)
				if (cheb(u.pos, pos) <= ci.attack_range && (!best || (u.awake && !best->awake) || (u.awake == best->awake && u.hp < best->hp)))
					best = &u;
		if (!best) return false;
		return act_attack(best->kind, best->handle);
	};
	sdk_champion(static_cast<std::uint32_t>(me), &ci);
	bool attacked = false;
	if (ci.state & 16) attacked = attack_best();
	if (chance(2)) act_attack(2, static_cast<std::uint32_t>(rint(0, static_cast<int>(all_camps.size()))));

	// Movement.
	sdk_champion(static_cast<std::uint32_t>(me), &ci);
	if (!(ci.state & 8)) return;
	std::vector<vec2> goals;
	if (gems >= 15 || (gems > 0 && chance(20)))
		for (auto a : altars)
			for (int dy = -1; dy <= 1; ++dy)
				for (int dx = -1; dx <= 1; ++dx)
					goals.push_back({ a.x + dx, a.y + dy });
	else if (!enemies.empty() && chance(15))
		for (auto& e : enemies) goals.push_back(e.pos);
	else
	{
		// Camp groups: go to their spawn tiles unless known to be respawning.
		for (std::uint32_t g = 0; g < num_groups; ++g)
		{
			std::uint32_t st{};
			if (sdk_camp_group_state(g, &st) == 0 && st == 3) continue;
			for (auto c : all_camps)
				if (camp_group_of[c] == g) goals.push_back(camp_spawn[c]);
		}
	}
	if (chance(7)) act_move({ ci.x + rint(-2, 2), ci.y + rint(-2, 2) });
	else if (!goals.empty()) step_towards(ci, goals, units);
	if (!attacked)
	{
		sdk_champion(static_cast<std::uint32_t>(me), &ci);
		units = visible_units(true);
		enemies.clear();
		camps.clear();
		for (auto& u : units)
		{
			if (u.kind == 2) camps.push_back(u);
			else if (u.team != my_team) enemies.push_back(u);
		}
		if (ci.state & 16) attack_best();
	}
}

void draft_turn()
{
	std::uint8_t rounds{};
	sdk_draft_num_rounds(&rounds);
	std::printf("@@draft rounds=%u", rounds);
	for (int t = 0; t < 2; ++t)
		for (std::uint32_t r = 0; r < rounds; ++r)
		{
			std::int32_t pick{};
			int rc = sdk_draft_get(t, r, &pick);
			std::printf(" %d:%u:%d", t, r, rc ? -rc : pick);
		}
	std::printf("\n");
	static std::array<int, 12> order = [] {
		std::array<int, 12> o{};
		for (int i = 0; i < 12; ++i) o[i] = i;
		for (int i = 11; i > 0; --i) std::swap(o[i], o[rnd() % (i + 1)]);
		return o;
	}();
	static int next = 0;
	while (next < 12)
	{
		const int pick = order[next++];
		const int rc = sdk_draft_champion(pick);
		std::printf("@@A pick %d -> %d\n", pick, rc);
		if (rc == 0) break;
	}
	if (TRACER_DRAFT_MEMORY)
	{
		std::array<std::uint8_t, 16> m{};
		for (auto& b : m) b = static_cast<std::uint8_t>(rnd());
		std::printf("@@A draftmem -> %d\n", sdk_bc_submit_draft_memory(m.data(), m.size()));
	}
}
} // namespace

int main()
{
	setup();
	if (is_draft())
	{
		rng_state = TRACER_SEED * 2654435761ull + static_cast<std::uint64_t>(my_team) * 97 + 1;
		for (;;)
		{
			draft_turn();
			end_turn();
		}
	}
	for (;;)
	{
		std::uint32_t round{};
		sdk_bc_round_number(&round);
		rng_state = (TRACER_SEED * 1000003ull + round) * 6364136223846793005ull + static_cast<std::uint64_t>(me) * 1442695040888963407ull + 7;
		std::printf("@@T %u %d\n", round, me);
		observe('O');
		play_turn(round);
		observe('P');
		end_turn();
	}
}
