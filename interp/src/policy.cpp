#include "interp/policy.h"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

namespace interp
{
using cbs::Api;
using cbs::Bitboard;
using cbs::ChampionInfo;
using cbs::EntityKind;
using cbs::Err;
using cbs::Vec2;
namespace state_bit = cbs::state_bit;

// Placeholder interpreter costs (fuel) until prices are measured against cambc:
// a flat cost per block evaluated, plus per-tile costs for whole-map scans.
constexpr std::int64_t kBlockCost = 10;
constexpr std::int64_t kScanDivisor = 16; // a full-map scan costs W*H/16

// Same order as policygen.blocks.TYPES: variable slot = type * kMaxVars + index.
static const char* const kTypes[] = { "Num", "Bool", "Tile", "TileSet", "Unit", "UnitList", "UnitPred",
									  "TilePred", "Stat", "Item", "Team", "Champ", "ChampList", "Bytes" };
constexpr int kNumTypes = sizeof kTypes / sizeof *kTypes;
constexpr int kMaxVars = 8;

#define INTERP_BLOCKS(X)                                                                                                    \
	X(ally, "ally()") X(enemy, "enemy()") X(stat_strength, "stat_strength()") X(stat_focus, "stat_focus()")                \
	X(stat_health, "stat_health()") X(add, "add(Num,Num)") X(sub, "sub(Num,Num)") X(mul, "mul(Num,Num)")                    \
	X(div, "div(Num,Num)") X(lt, "lt(Num,Num)") X(le, "le(Num,Num)") X(gt, "gt(Num,Num)") X(ge, "ge(Num,Num)")              \
	X(eq, "eq(Num,Num)") X(ne, "ne(Num,Num)") X(true_, "true()") X(false_, "false()") X(and_, "and(Bool,Bool)") X(or_, "or(Bool,Bool)") X(not_, "not(Bool)") X(floor_, "floor(Num)")     \
	X(is_draft, "is_draft()") X(unpicked_champions, "unpicked_champions()") X(random_champion, "random_champion(ChampList)") \
	X(pick, "pick(Champ)") X(write_draft, "write_draft(Bytes)") X(alive, "alive()") X(channeling, "channeling()")          \
	X(can_move, "can_move()") X(can_attack, "can_attack()") X(position, "position()") X(health, "health()")                \
	X(max_health, "max_health()") X(gems, "gems()") X(gold, "gold()") X(round_number, "round_number()")                    \
	X(fuel_remaining, "fuel_remaining()") X(altars, "altars()") X(walls, "walls()") X(holes, "holes()")                    \
	X(bushes, "bushes()") X(camp_spawn_tiles, "camp_spawn_tiles()") X(spawn_region, "spawn_region(Team)")                  \
	X(enemies_visible, "enemies_visible()") X(allies_visible, "allies_visible()") X(camps_visible, "camps_visible()")      \
	X(locked_altars, "locked_altars()") X(respawning_visible_spawns, "respawning_visible_spawns()")                        \
	X(read_shared, "read_shared(Num)") X(write_shared, "write_shared(Num,Num)") X(union_, "union(TileSet,TileSet)")        \
	X(minus, "minus(TileSet,TileSet)") X(contains, "contains(TileSet,Tile)") X(ring, "ring(TileSet,Num)")                  \
	X(closest, "closest(TileSet)") X(filter_tiles, "filter(TileSet,TilePred)") X(first_tile, "first(TileSet)")             \
	X(exists_tile, "exists(Tile)") X(count_tiles, "count(TileSet)") X(within, "within(Num,Tile)")                          \
	X(distance, "distance(Tile,Tile)") X(filter_units, "filter(UnitList,UnitPred)") X(first_unit, "first(UnitList)")       \
	X(exists_unit, "exists(Unit)") X(count_units, "count(UnitList)") X(unit_position, "unit_position(Unit)")               \
	X(unit_health, "unit_health(Unit)") X(in_attack_range, "in_attack_range()") X(random_int, "random_int(Num)")           \
	X(random_stat, "random_stat()") X(shard, "shard(Stat)") X(move_towards, "move_towards(Tile)")                          \
	X(attack, "attack(Unit)") X(cast_at_unit, "cast_at_unit(Num,Unit)") X(cast_at_tile, "cast_at_tile(Num,Tile)")          \
	X(cast_self, "cast_self(Num)") X(place_ward, "place_ward(Tile)") X(tribute, "tribute(Tile)") X(recall, "recall()")     \
	X(buy, "buy(Item,Num)") X(set_priority, "set_priority(Num)") X(champ_ryth, "champ_ryth()")                           \
	X(champ_vesper_vale, "champ_vesper_vale()") X(champ_vendetta, "champ_vendetta()")                                       \
	X(champ_cassi_issac, "champ_cassi_issac()") X(champ_stellar, "champ_stellar()") X(champ_prism, "champ_prism()")        \
	X(champ_marcella, "champ_marcella()") X(champ_willow, "champ_willow()") X(champ_ren, "champ_ren()")                    \
	X(champ_varg, "champ_varg()") X(champ_tavi, "champ_tavi()") X(available, "available(ChampList,Champ)")                 \
	X(i_am, "i_am(Champ)") X(ability_ready, "ability_ready(Num)")

enum class Op : std::uint16_t
{
#define X(id, key) id,
	INTERP_BLOCKS(X)
#undef X
		const_num,
	const_bytes,
	var,
};

struct BlockInfo
{
	Op op;
	const char* key;
	int arity;
};

static const std::vector<BlockInfo>& block_table()
{
	static const std::vector<BlockInfo> table = [] {
		std::vector<BlockInfo> t;
#define X(id, key) t.push_back({ Op::id, key, 0 });
		INTERP_BLOCKS(X)
#undef X
		for (auto& b : t)
		{
			const std::string k = b.key;
			const auto open = k.find('(');
			const std::string args = k.substr(open + 1, k.size() - open - 2);
			b.arity = args.empty() ? 0 : 1 + static_cast<int>(std::count(args.begin(), args.end(), ','));
		}
		return t;
	}();
	return table;
}

std::vector<std::string> supported_blocks()
{
	std::vector<std::string> out;
	for (auto& b : block_table()) out.push_back(b.key);
	return out;
}

// ---- program ---------------------------------------------------------------

struct Expr
{
	Op op = Op::const_num;
	int var = -1;
	double num = 0;
	std::string bytes;
	std::vector<Expr> args;
};

struct Step
{
	enum Kind { do_, if_, let_, keep_, end_turn } kind = do_;
	Expr expr; // effect call, condition, or bound value
	int var = -1;
	std::vector<Step> then, orelse;
};

struct Program
{
	std::vector<Step> steps;
};

namespace
{
struct Parser
{
	std::vector<std::string> toks;
	std::size_t pos = 0;
	int counts[kNumTypes] = {};
	std::unordered_map<std::string, const BlockInfo*> blocks;

	Parser()
	{
		for (auto& b : block_table()) blocks[b.key] = &b;
	}
	const std::string& take()
	{
		if (pos >= toks.size()) throw std::runtime_error("policy: unexpected end of input");
		return toks[pos++];
	}
	static int type_index(const std::string& name)
	{
		for (int i = 0; i < kNumTypes; ++i)
			if (name == kTypes[i]) return i;
		throw std::runtime_error("policy: unknown type " + name);
	}
	static std::vector<std::uint8_t> unhex(const std::string& s)
	{
		std::vector<std::uint8_t> out;
		if (s == "-") return out;
		for (std::size_t i = 0; i + 1 < s.size(); i += 2) out.push_back(static_cast<std::uint8_t>(std::stoi(s.substr(i, 2), nullptr, 16)));
		return out;
	}
	Expr expr()
	{
		const std::string tok = take();
		Expr e;
		if (tok == "CONST:Num")
		{
			e.op = Op::const_num;
			e.num = std::stod(take());
		}
		else if (tok == "CONST:Bytes")
		{
			e.op = Op::const_bytes;
			const auto b = unhex(take());
			e.bytes.assign(b.begin(), b.end());
		}
		else if (tok.rfind("VAR:", 0) == 0)
		{
			const auto c2 = tok.find(':', 4);
			e.op = Op::var;
			e.var = type_index(tok.substr(4, c2 - 4)) * kMaxVars + std::stoi(tok.substr(c2 + 1));
		}
		else
		{
			const auto it = blocks.find(tok);
			if (it == blocks.end()) throw std::runtime_error("policy: unknown block " + tok);
			e.op = it->second->op;
			for (int i = 0; i < it->second->arity; ++i) e.args.push_back(expr());
		}
		return e;
	}
	std::vector<Step> steps()
	{
		std::vector<Step> out;
		for (;;)
		{
			const std::string tok = take();
			if (tok == "END") return out;
			Step s;
			if (tok == "END_TURN") s.kind = Step::end_turn;
			else if (tok == "IF")
			{
				s.kind = Step::if_;
				s.expr = expr();
				s.then = steps();
				if (pos < toks.size() && toks[pos] == "ELSE")
				{
					++pos;
					s.orelse = steps();
				}
			}
			else if (tok.rfind("LET:", 0) == 0 || tok.rfind("KEEP:", 0) == 0)
			{
				const bool keep = tok[0] == 'K';
				const int t = type_index(tok.substr(keep ? 5 : 4));
				s.kind = keep ? Step::keep_ : Step::let_;
				s.expr = expr();
				if (counts[t] >= kMaxVars) throw std::runtime_error("policy: too many variables");
				s.var = t * kMaxVars + counts[t]++;
			}
			else
			{
				--pos;
				s.kind = Step::do_;
				s.expr = expr();
			}
			out.push_back(std::move(s));
		}
	}
};
} // namespace

std::shared_ptr<const Program> load_program(const std::string& text)
{
	Parser p;
	std::istringstream in(text);
	std::string line;
	if (!std::getline(in, line) || line != "policy v0") throw std::runtime_error("policy: missing 'policy v0' header");
	for (std::string tok; in >> tok;) p.toks.push_back(tok);
	auto prog = std::make_shared<Program>();
	prog->steps = p.steps();
	if (p.pos != p.toks.size()) throw std::runtime_error("policy: trailing tokens");
	return prog;
}

std::shared_ptr<const Program> load_program_file(const std::string& path)
{
	std::ifstream f(path);
	if (!f) throw std::runtime_error("policy: cannot open " + path);
	std::stringstream ss;
	ss << f.rdbuf();
	return load_program(ss.str());
}

// ---- values ----------------------------------------------------------------

namespace
{
struct Unit
{
	EntityKind kind = EntityKind::none;
	std::uint32_t h = 0;
};

constexpr Vec2 kNoTile{ -1, -1 };

struct Value
{
	double n = 0; // Num, Bool (0/1), Stat, Item, Team, Champ (-1 = none)
	Vec2 tile = kNoTile;
	Unit unit;
	std::shared_ptr<Bitboard> set;
	std::shared_ptr<std::vector<Unit>> units;
	std::shared_ptr<std::vector<int>> champs;
	std::string bytes;
	int pred = 0; // TilePred within: radius n, centre tile
};

Value num(double v)
{
	Value r;
	r.n = v;
	return r;
}
Value tile(Vec2 p)
{
	Value r;
	r.tile = p;
	return r;
}
Value set_of(const Bitboard& b)
{
	Value r;
	r.set = std::make_shared<Bitboard>(b);
	return r;
}
bool has_tile(Vec2 p) { return p.x >= 0; }

struct Rng
{
	std::uint64_t s;
	std::uint32_t next(std::uint32_t n)
	{
		s ^= s << 13, s ^= s >> 7, s ^= s << 17;
		return n ? static_cast<std::uint32_t>((s >> 11) % n) : 0;
	}
};

// One interpreter per bot instance; state (keep variables, rng) persists across turns.
struct Interp
{
	Api& api;
	const Program& prog;
	Rng rng;
	std::vector<Value> vars = std::vector<Value>(kNumTypes * kMaxVars);
	std::vector<char> kept = std::vector<char>(kNumTypes * kMaxVars, 0);
	std::vector<std::uint16_t> field;

	const cbs::Map& m() const { return api.map(); }
	void scan_cost() { api.compute(static_cast<std::int64_t>(m().W) * m().H / kScanDivisor); }

	// false for the draft bot or when the champion record is unavailable
	bool me(ChampionInfo& ci)
	{
		if (api.champ() < 0) return false;
		return api.champion(static_cast<std::uint32_t>(api.my_champion()), &ci) == Err::success;
	}
	std::uint32_t self() { return static_cast<std::uint32_t>(api.my_champion()); }

	void turn()
	{
		run(prog.steps);
	}

	// Returns false when END_TURN was reached.
	bool run(const std::vector<Step>& steps)
	{
		for (const Step& s : steps)
		{
			switch (s.kind)
			{
			case Step::end_turn: return false;
			case Step::do_: exec(s.expr); break;
			case Step::let_: vars[s.var] = eval(s.expr); break;
			case Step::keep_:
				if (!kept[s.var])
				{
					vars[s.var] = eval(s.expr);
					kept[s.var] = 1;
				}
				break;
			case Step::if_:
				if (eval(s.expr).n != 0)
				{
					if (!run(s.then)) return false;
				}
				else if (!run(s.orelse)) return false;
				break;
			}
		}
		return true;
	}

	Bitboard blocked_tiles(Vec2 me)
	{
		Bitboard blocked = m().walls;
		blocked |= m().holes;
		blocked |= m().altars;
		blocked |= m().spawn_mask[1 - api.team()];
		Bitboard occ;
		api.ally_occupancy(occ);
		blocked |= occ;
		api.enemy_occupancy(occ);
		blocked |= occ;
		api.camp_occupancy(occ, 0);
		blocked |= occ;
		blocked.reset(me);
		return blocked;
	}

	// The starter bot's move_towards_closest: distance field from the goals, step downhill.
	void move_towards_goals(Bitboard goals, Vec2 me)
	{
		if (goals.test(me)) return;
		Bitboard blocked = blocked_tiles(me), camps;
		api.camp_occupancy(camps, 0);
		Bitboard taken = blocked;
		taken.andnot(camps);
		goals.andnot(taken);
		if (!goals.any(m().H)) return;
		Bitboard walls = blocked, dest, visited;
		walls.andnot(goals);
		dest.set(me);
		field.resize(static_cast<std::size_t>(m().W) * m().H);
		api.distance_field(walls, goals, &dest, cbs::kUnreachable, field.data(), visited);
		Vec2 best = me;
		std::uint16_t bd = field[m().idx(me)];
		for (int dy = -1; dy <= 1; ++dy)
			for (int dx = -1; dx <= 1; ++dx)
			{
				const Vec2 p{ me.x + dx, me.y + dy };
				if (!m().in_bounds(p) || blocked.test(p)) continue;
				if (field[m().idx(p)] < bd)
				{
					bd = field[m().idx(p)];
					best = p;
				}
			}
		if (best == me) return;
		std::int32_t ok = 0;
		api.move_to(best, &ok);
	}

	// Nearest tile of `set` by walking distance (same seeding rule as move_towards_goals).
	Vec2 closest(const Bitboard& set)
	{
		ChampionInfo ci{};
		if (!me(ci)) return kNoTile;
		const Vec2 pos{ ci.x, ci.y };
		if (set.test(pos)) return pos;
		Bitboard blocked = blocked_tiles(pos), camps;
		api.camp_occupancy(camps, 0);
		Bitboard cand = set, taken = blocked;
		taken.andnot(camps);
		cand.andnot(taken);
		if (!cand.any(m().H)) return kNoTile;
		Bitboard walls = blocked, root, visited;
		walls.andnot(cand);
		root.set(pos);
		field.resize(static_cast<std::size_t>(m().W) * m().H);
		api.distance_field(walls, root, &cand, cbs::kUnreachable, field.data(), visited);
		scan_cost();
		Vec2 best = kNoTile;
		std::uint16_t bd = cbs::kUnreachable;
		for (int y = 0; y < m().H; ++y)
			for (int x = 0; x < m().W; ++x)
				if (cand.test(x, y) && field[m().idx({ x, y })] < bd)
				{
					bd = field[m().idx({ x, y })];
					best = { x, y };
				}
		return best;
	}

	bool unit_info(const Unit& u, Vec2& pos, double& hp)
	{
		if (u.kind == EntityKind::champion)
		{
			ChampionInfo ci{};
			if (api.champion(u.h, &ci) != Err::success || !(ci.state & state_bit::alive)) return false;
			pos = { ci.x, ci.y };
			hp = ci.health;
			return true;
		}
		if (u.kind == EntityKind::camp)
		{
			cbs::CampRecord cr{};
			if (api.camp(u.h, &cr) != Err::success || cr.health <= 0) return false;
			pos = { cr.x, cr.y };
			hp = cr.health;
			return true;
		}
		return false;
	}

	Value champions(bool enemies)
	{
		std::uint32_t ids[16], n = 0;
		enemies ? api.enemies(ids, 16, &n) : api.allies(ids, 16, &n);
		Value r;
		r.units = std::make_shared<std::vector<Unit>>();
		for (std::uint32_t i = 0; i < n && i < 16; ++i)
		{
			if (!enemies && api.champ() >= 0 && ids[i] == self()) continue;
			ChampionInfo ci{};
			if (api.champion(ids[i], &ci) == Err::success && (ci.state & state_bit::alive))
				r.units->push_back({ EntityKind::champion, ids[i] });
		}
		return r;
	}

	Value eval(const Expr& e)
	{
		if (e.op == Op::const_num) return num(e.num);
		if (e.op == Op::var) return vars[e.var];
		if (e.op == Op::const_bytes)
		{
			Value r;
			r.bytes = e.bytes;
			return r;
		}
		api.compute(kBlockCost);
		const auto& a = e.args;
		switch (e.op)
		{
		case Op::ally: return num(api.team());
		case Op::enemy: return num(1 - api.team());
		case Op::stat_strength: return num(0);
		case Op::stat_focus: return num(1);
		case Op::stat_health: return num(2);
		case Op::add: return num(eval(a[0]).n + eval(a[1]).n);
		case Op::sub: return num(eval(a[0]).n - eval(a[1]).n);
		case Op::mul: return num(eval(a[0]).n * eval(a[1]).n);
		case Op::div:
		{
			const double x = eval(a[0]).n, y = eval(a[1]).n;
			return num(y == 0 ? 0 : x / y);
		}
		case Op::lt: return num(eval(a[0]).n < eval(a[1]).n);
		case Op::le: return num(eval(a[0]).n <= eval(a[1]).n);
		case Op::gt: return num(eval(a[0]).n > eval(a[1]).n);
		case Op::ge: return num(eval(a[0]).n >= eval(a[1]).n);
		case Op::eq: return num(eval(a[0]).n == eval(a[1]).n);
		case Op::ne: return num(eval(a[0]).n != eval(a[1]).n);
		case Op::true_: return num(1);
		case Op::false_: return num(0);
		case Op::and_: return num(eval(a[0]).n != 0 && eval(a[1]).n != 0);
		case Op::or_: return num(eval(a[0]).n != 0 || eval(a[1]).n != 0);
		case Op::not_: return num(eval(a[0]).n == 0);
		case Op::floor_: return num(std::floor(eval(a[0]).n));
		case Op::is_draft: return num(api.champ() < 0);
		case Op::unpicked_champions:
		{
			Value r;
			r.champs = std::make_shared<std::vector<int>>();
			for (int i = 0; i < 11; ++i)
			{
				bool used = false;
				std::int32_t pick = -1;
				for (std::uint32_t round = 0; round < 6; ++round)
					if (api.draft_get(api.team(), round, &pick) == Err::success && pick == i) used = true;
				if (!used) r.champs->push_back(i);
			}
			return r;
		}
		case Op::random_champion:
		{
			const Value l = eval(a[0]);
			if (!l.champs || l.champs->empty()) return num(-1);
			return num((*l.champs)[rng.next(static_cast<std::uint32_t>(l.champs->size()))]);
		}
		case Op::alive:
		case Op::channeling:
		case Op::can_move:
		case Op::can_attack:
		{
			ChampionInfo ci{};
			if (!me(ci)) return num(0);
			const std::uint32_t st = ci.state;
			if (e.op == Op::alive) return num((st & state_bit::alive) != 0);
			if (e.op == Op::channeling)
				return num((st & (state_bit::recalling | state_bit::submitting | state_bit::teleporting)) != 0);
			if (e.op == Op::can_move) return num((st & state_bit::can_move) != 0);
			return num((st & state_bit::can_attack) != 0);
		}
		case Op::position:
		{
			ChampionInfo ci{};
			return me(ci) ? tile({ ci.x, ci.y }) : tile(kNoTile);
		}
		case Op::health:
		case Op::max_health:
		{
			ChampionInfo ci{};
			if (!me(ci)) return num(0);
			return num(e.op == Op::health ? ci.health : ci.max_health);
		}
		case Op::gems:
		case Op::gold:
		{
			if (api.champ() < 0) return num(0);
			std::uint32_t v = 0;
			e.op == Op::gems ? api.champion_gems(self(), &v) : api.champion_gold(self(), &v);
			return num(v);
		}
		case Op::round_number:
		{
			std::uint32_t r = 0;
			api.round_number(&r);
			return num(r);
		}
		case Op::fuel_remaining: return num(static_cast<double>(api.fuel_remaining()));
		case Op::altars: api.charge(cbs::Call::map_mask); return set_of(m().altars);
		case Op::walls: api.charge(cbs::Call::map_mask); return set_of(m().walls);
		case Op::holes: api.charge(cbs::Call::map_mask); return set_of(m().holes);
		case Op::bushes: api.charge(cbs::Call::map_mask); return set_of(m().bushes);
		case Op::camp_spawn_tiles:
		{
			api.charge(cbs::Call::map_camp_query, static_cast<std::int64_t>(m().camps.size()));
			Bitboard b;
			for (auto& c : m().camps) b.set(c.pos);
			return set_of(b);
		}
		case Op::spawn_region:
		{
			api.charge(cbs::Call::spawn_region);
			const int t = static_cast<int>(eval(a[0]).n);
			return set_of(m().spawn_mask[t == 0 ? 0 : 1]);
		}
		case Op::enemies_visible: return champions(true);
		case Op::allies_visible: return champions(false);
		case Op::camps_visible:
		{
			Value r;
			r.units = std::make_shared<std::vector<Unit>>();
			for (std::uint32_t c = 0; c < m().camps.size(); ++c)
			{
				cbs::CampRecord cr{};
				if (api.camp(c, &cr) == Err::success && cr.health > 0) r.units->push_back({ EntityKind::camp, c });
			}
			return r;
		}
		case Op::locked_altars:
		{
			cbs::AltarLockRecord locks[16];
			std::uint32_t n = 0;
			api.altar_locks(locks, 16, &n);
			Bitboard b;
			for (std::uint32_t i = 0; i < n && i < 16; ++i) b.set(locks[i].x, locks[i].y);
			return set_of(b);
		}
		case Op::respawning_visible_spawns:
		{
			Bitboard b;
			for (std::size_t g = 0; g < m().groups.size(); ++g)
			{
				std::uint32_t gs = 0;
				if (api.camp_group_state(static_cast<std::uint32_t>(g), &gs) != Err::success) continue;
				if (gs != static_cast<std::uint32_t>(cbs::GroupState::respawning)) continue;
				for (int c : m().groups[g].camps) b.set(m().camps[c].pos);
			}
			return set_of(b);
		}
		case Op::read_shared:
		{
			const int off = std::clamp(static_cast<int>(eval(a[0]).n), 0, 7);
			std::uint8_t v = 0;
			api.read_shared_memory(off, &v, 1);
			return num(v);
		}
		case Op::union_:
		case Op::minus:
		{
			const Value x = eval(a[0]), y = eval(a[1]);
			Bitboard b = *x.set;
			if (e.op == Op::union_) b |= *y.set;
			else b.andnot(*y.set);
			return set_of(b);
		}
		case Op::contains:
		{
			const Value s = eval(a[0]), t = eval(a[1]);
			return num(has_tile(t.tile) && s.set->test(t.tile));
		}
		case Op::ring:
		{
			const Value s = eval(a[0]);
			const float r = static_cast<float>(std::clamp(eval(a[1]).n, 0.0, 10.0));
			scan_cost();
			Bitboard b;
			for (int y = 0; y < m().H; ++y)
				for (int x = 0; x < m().W; ++x)
					if (s.set->test(x, y)) cbs::draw_chebyshev(b, m().W, m().H, { x, y }, r);
			return set_of(b);
		}
		case Op::closest: return tile(closest(*eval(a[0]).set));
		case Op::filter_tiles:
		{
			const Value s = eval(a[0]), p = eval(a[1]);
			scan_cost();
			Bitboard b;
			if (has_tile(p.tile))
				for (int y = 0; y < m().H; ++y)
					for (int x = 0; x < m().W; ++x)
						if (s.set->test(x, y) && cbs::chebyshev({ x, y }, p.tile) <= p.n) b.set(x, y);
			return set_of(b);
		}
		case Op::first_tile:
		{
			const Value s = eval(a[0]);
			scan_cost();
			for (int y = 0; y < m().H; ++y)
				for (int x = 0; x < m().W; ++x)
					if (s.set->test(x, y)) return tile({ x, y });
			return tile(kNoTile);
		}
		case Op::exists_tile: return num(has_tile(eval(a[0]).tile));
		case Op::count_tiles:
		{
			scan_cost();
			return num(eval(a[0]).set->count(m().H));
		}
		case Op::within:
		{
			Value r = tile(eval(a[1]).tile);
			r.n = eval(a[0]).n;
			return r;
		}
		case Op::distance:
		{
			const Vec2 p = eval(a[0]).tile, q = eval(a[1]).tile;
			return num(has_tile(p) && has_tile(q) ? cbs::chebyshev(p, q) : 1e9);
		}
		case Op::filter_units:
		{
			const Value l = eval(a[0]);
			eval(a[1]); // in_attack_range is the only UnitPred so far
			Value r;
			r.units = std::make_shared<std::vector<Unit>>();
			ChampionInfo ci{};
			if (!me(ci)) return r;
			const Vec2 mp{ ci.x, ci.y };
			for (const Unit& u : *l.units)
			{
				Vec2 pos;
				double hp;
				if (unit_info(u, pos, hp) && cbs::chebyshev(mp, pos) <= ci.attack_range) r.units->push_back(u);
			}
			return r;
		}
		case Op::first_unit:
		{
			const Value l = eval(a[0]);
			Value r;
			if (!l.units->empty()) r.unit = l.units->front();
			return r;
		}
		case Op::exists_unit: return num(eval(a[0]).unit.kind != EntityKind::none);
		case Op::count_units: return num(static_cast<double>(eval(a[0]).units->size()));
		case Op::unit_position:
		case Op::unit_health:
		{
			Vec2 pos = kNoTile;
			double hp = 0;
			const bool ok = unit_info(eval(a[0]).unit, pos, hp);
			if (e.op == Op::unit_position) return tile(ok ? pos : kNoTile);
			return num(ok ? hp : 0);
		}
		case Op::in_attack_range: return Value{};
		case Op::random_int:
		{
			const double n = std::floor(eval(a[0]).n);
			return num(n >= 1 ? rng.next(static_cast<std::uint32_t>(std::min(n, 1e9))) : 0);
		}
		case Op::random_stat: return num(rng.next(3));
		case Op::champ_ryth:
		case Op::champ_vesper_vale:
		case Op::champ_vendetta:
		case Op::champ_cassi_issac:
		case Op::champ_stellar:
		case Op::champ_prism:
		case Op::champ_marcella:
		case Op::champ_willow:
		case Op::champ_ren:
		case Op::champ_varg:
		case Op::champ_tavi: return num(static_cast<int>(e.op) - static_cast<int>(Op::champ_ryth));
		case Op::available:
		{
			const Value l = eval(a[0]);
			const int c = static_cast<int>(eval(a[1]).n);
			return num(l.champs && std::find(l.champs->begin(), l.champs->end(), c) != l.champs->end());
		}
		case Op::i_am:
		{
			const int c = static_cast<int>(eval(a[0]).n);
			ChampionInfo ci{};
			if (!me(ci)) return num(0);
			// ChampionType order: ryth, vesper_vale, vendetta, cassi, issac, stellar, ... (Issac shares Cassi's pick)
			const int pick = ci.type <= 3 ? ci.type : ci.type - 1;
			return num(pick == c);
		}
		case Op::ability_ready:
		{
			const int slot = std::clamp(static_cast<int>(eval(a[0]).n), 0, 1);
			ChampionInfo ci{};
			if (!me(ci) || !(ci.state & state_bit::can_cast)) return num(0);
			std::int32_t cd = 1;
			api.champion_cooldown(self(), static_cast<std::uint32_t>(slot), &cd);
			return num(cd <= 0);
		}
		case Op::shard: return num(6 + 2 * std::clamp(static_cast<int>(eval(a[0]).n), 0, 2)); // power shard
		default: break;
		}
		exec(e); // an effect used as a value (cannot happen in well-typed policies)
		return Value{};
	}

	void exec(const Expr& e)
	{
		api.compute(kBlockCost);
		const auto& a = e.args;
		std::int32_t ok = 0;
		switch (e.op)
		{
		case Op::pick:
		{
			const int c = static_cast<int>(eval(a[0]).n);
			if (c >= 0) api.draft_champion(c);
			break;
		}
		case Op::write_draft:
		{
			const Value b = eval(a[0]);
			api.submit_draft_memory(reinterpret_cast<const std::uint8_t*>(b.bytes.data()), static_cast<std::uint32_t>(b.bytes.size()));
			break;
		}
		case Op::write_shared:
		{
			const int off = std::clamp(static_cast<int>(eval(a[0]).n), 0, 7);
			const std::uint8_t v = static_cast<std::uint8_t>(std::clamp(std::lround(eval(a[1]).n), 0l, 255l));
			api.write_shared_memory(off, &v, 1);
			break;
		}
		case Op::move_towards:
		{
			const Vec2 t = eval(a[0]).tile;
			ChampionInfo ci{};
			if (!has_tile(t) || !me(ci)) break;
			Bitboard goals;
			goals.set(t);
			move_towards_goals(goals, { ci.x, ci.y });
			break;
		}
		case Op::attack:
		{
			const Unit u = eval(a[0]).unit;
			if (u.kind != EntityKind::none) api.attack(static_cast<std::uint32_t>(u.kind), u.h);
			break;
		}
		case Op::cast_at_unit:
		{
			const int slot = static_cast<int>(eval(a[0]).n);
			const Unit u = eval(a[1]).unit;
			Vec2 pos = kNoTile;
			double hp;
			if (u.kind != EntityKind::none && unit_info(u, pos, hp))
				api.cast(static_cast<std::uint32_t>(std::clamp(slot, 0, 1)), static_cast<std::uint32_t>(u.kind), u.h, pos, &ok);
			break;
		}
		case Op::cast_at_tile:
		{
			const int slot = static_cast<int>(eval(a[0]).n);
			const Vec2 t = eval(a[1]).tile;
			if (has_tile(t)) api.cast(static_cast<std::uint32_t>(std::clamp(slot, 0, 1)), 0, 0, t, &ok);
			break;
		}
		case Op::cast_self:
		{
			const int slot = static_cast<int>(eval(a[0]).n);
			ChampionInfo ci{};
			if (me(ci))
				api.cast(static_cast<std::uint32_t>(std::clamp(slot, 0, 1)), static_cast<std::uint32_t>(EntityKind::champion), self(),
						 { ci.x, ci.y }, &ok);
			break;
		}
		case Op::place_ward:
		{
			const Vec2 t = eval(a[0]).tile;
			if (has_tile(t)) api.place_ward(t, &ok);
			break;
		}
		case Op::tribute:
		{
			const Vec2 t = eval(a[0]).tile;
			if (has_tile(t)) api.submit_gems(t);
			break;
		}
		case Op::recall: api.recall(); break;
		case Op::buy:
		{
			const int item = static_cast<int>(eval(a[0]).n);
			const double n = std::floor(eval(a[1]).n);
			if (n >= 1) api.buy_item(static_cast<std::uint32_t>(item), static_cast<std::uint32_t>(std::min(n, 1000.0)));
			break;
		}
		case Op::set_priority: api.set_priority(static_cast<std::int32_t>(std::clamp(eval(a[0]).n, -1e6, 1e6))); break;
		default: eval(e); break; // a pure block used as a step: evaluate for its cost only
		}
	}
};

class PolicyPlayer : public cbs::Player
{
public:
	PolicyPlayer(std::shared_ptr<const Program> p, std::uint64_t seed) : prog_(std::move(p)), seed_(seed) {}
	cbs::BotBody make_bot(int team, int champ) override
	{
		const std::uint64_t s = (seed_ * 0x9E3779B97F4A7C15ull) ^ (static_cast<std::uint64_t>(team) << 32) ^
								static_cast<std::uint64_t>(champ + 7) * 0xBF58476D1CE4E5B9ull;
		auto prog = prog_;
		return [prog, s](Api& api) {
			Interp in{ api, *prog, Rng{ s | 1 } };
			for (;;)
			{
				in.turn();
				api.end_turn();
			}
		};
	}

private:
	std::shared_ptr<const Program> prog_;
	std::uint64_t seed_;
};
} // namespace

std::unique_ptr<cbs::Player> make_policy_player(std::shared_ptr<const Program> program, std::uint64_t seed)
{
	return std::make_unique<PolicyPlayer>(std::move(program), seed);
}
} // namespace interp
