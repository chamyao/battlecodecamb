#include "interp/policy.h"
#include "interp/program.h"
#include <algorithm>
#include <exception>
#include <string_view>
#include <charconv>
#include <array>
#include <cctype>
#include <cstdlib>
#include <cmath>
#include <fstream>
#include <functional>
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


// Same order as policygen.blocks.TYPES: variable slot = type * kMaxVars + index.
static const char* const kTypes[] = { "Num", "Bool", "Tile", "TileSet", "Unit", "UnitList", "UnitPred",
									  "TilePred", "Stat", "Item", "Team", "Champ", "ChampList", "Bytes", "Family" };
constexpr int kNumTypes = sizeof kTypes / sizeof *kTypes;
constexpr int kMaxVars = 16;
static_assert(kNumTypes * kMaxVars <= 256, "variable codes must fit one 256-code band");

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
	X(champ_varg, "champ_varg()") X(champ_tavi, "champ_tavi()") X(champ_heart_of_ruin, "champ_heart_of_ruin()") X(available, "available(ChampList,Champ)")                 \
	X(i_am, "i_am(Champ)") X(ability_ready, "ability_ready(Num)") X(family_monster, "family_monster()")                  \
	X(family_power, "family_power()") X(family_durability, "family_durability()") X(family_treasure, "family_treasure()") \
	X(family_jungle, "family_jungle()") X(family_home, "family_home()") X(family_bruiser, "family_bruiser()")              \
	X(shard_of, "shard_of(Family,Stat)") X(buy_altar_lock, "buy_altar_lock()") X(buy_teleport, "buy_teleport()")          \
	X(has_altar_lock, "has_altar_lock()") X(has_teleport, "has_teleport()") X(place_altar_lock, "place_altar_lock(Tile)") \
	X(teleport_to, "teleport_to(Tile)") X(i_am_ranged, "i_am_ranged()") X(slot_is_dash, "slot_is_dash(Num)")             \
	X(slot_is_damage, "slot_is_damage(Num)") X(slot_is_aoe, "slot_is_aoe(Num)") X(slot_is_stun, "slot_is_stun(Num)")      \
	X(slot_is_heal, "slot_is_heal(Num)") X(slot_is_shield, "slot_is_shield(Num)") X(slot_is_reset, "slot_is_reset(Num)")  \
	X(dash_towards, "dash_towards(Num,Tile)") X(unit_gems, "unit_gems(Unit)") X(team_score, "team_score(Team)")            \
	X(map_width, "map_width()") X(map_height, "map_height()") X(camp_count, "camp_count()")                                \
	X(weakest, "weakest(UnitList)") X(richest, "richest(UnitList)") X(nearest, "nearest(UnitList)")                       \
	X(claim, "claim(Tile)") X(unclaim, "unclaim()") X(claimed_by_allies, "claimed_by_allies()") X(claim_count, "claim_count(Tile)")                           \
	X(set_team_target, "set_team_target(Unit)") X(team_target, "team_target()")                                          \
	X(wolf_tiles, "wolf_tiles()") X(elk_tiles, "elk_tiles()") X(gem_cluster_tiles, "gem_cluster_tiles()")                \
	X(gold_cluster_tiles, "gold_cluster_tiles()") X(monolith_tiles, "monolith_tiles()") X(golem_tiles, "golem_tiles()")    \
	X(in_danger, "in_danger()") X(move_away_from, "move_away_from(Tile)") X(allies_within, "allies_within(Num)")          \
	X(unit_health_frac, "unit_health_frac(Unit)") X(capturable_spawns, "capturable_spawns()") X(turns_idle, "turns_idle()")   \
	X(enemies_within, "enemies_within(Num)") X(local_strength, "local_strength(Num)")

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

// Arity of a block key such as "add(Num,Num)", computed at compile time (string work is
// expensive inside a wasm bot).
constexpr int key_arity(const char* k)
{
	int i = 0;
	while (k[i] != '(') ++i;
	if (k[i + 1] == ')') return 0;
	int n = 1;
	for (; k[i] != ')'; ++i) n += k[i] == ',';
	return n;
}

constexpr BlockInfo kBlockTable[] = {
#define X(id, key) { Op::id, key, key_arity(key) },
	INTERP_BLOCKS(X)
#undef X
};
constexpr int kNumBlocks = sizeof kBlockTable / sizeof *kBlockTable;

struct BlockTableView
{
	const BlockInfo* begin() const { return kBlockTable; }
	const BlockInfo* end() const { return kBlockTable + kNumBlocks; }
};
static BlockTableView block_table() { return {}; }

constexpr std::uint32_t fnv1a(std::string_view s)
{
	std::uint32_t h = 2166136261u;
	for (char c : s) h = (h ^ static_cast<unsigned char>(c)) * 16777619u;
	return h;
}

// Open-addressing table from block key to block, built once.
static const BlockInfo* find_block(std::string_view key)
{
	constexpr int kSlots = 512; // power of two, > 2 * kNumBlocks
	static_assert(kSlots > 2 * kNumBlocks);
	static const auto slots = [] {
		std::array<const BlockInfo*, kSlots> t{};
		for (const BlockInfo& b : kBlockTable)
		{
			std::uint32_t i = fnv1a(b.key) & (kSlots - 1);
			while (t[i]) i = (i + 1) & (kSlots - 1);
			t[i] = &b;
		}
		return t;
	}();
	for (std::uint32_t i = fnv1a(key) & (kSlots - 1); slots[i]; i = (i + 1) & (kSlots - 1))
		if (key == slots[i]->key) return slots[i];
	return nullptr;
}

// ---- fuel ------------------------------------------------------------------
// Each block is charged its self cost (excluding its argument blocks and the API calls it
// makes, which the bot-wrapper price table prices) as measured on the deploy bot in cambc and
// fitted by oracle/tools/fuel_calibrate.py (docs/FUEL.md). Terms (milli-fuel): constant, map
// rows, 8x8 chunks, occupancy-cache refreshes, refreshes x rows, distance-field destination
// tiles, expansions x chunks, camps, camp groups, tiles of the input set.
struct BlockCost
{
	const char* key;
	bool exec;
	std::int64_t milli[10];
};
static const BlockCost kCalibrated[] = {
#include "block_costs_gen.inc"
};
// Blocks the calibration did not exercise (load_program refuses such policies; only the bot's
// pre-encoded programs, which skip the charge anyway, can reach this): a simple block's cost.
constexpr std::int64_t kUncalibratedBlockMilli = 200000;

struct BlockCostTable
{
	const std::int64_t* row[2][kNumBlocks] = {};
	BlockCostTable()
	{
		for (const BlockCost& c : kCalibrated)
			if (const BlockInfo* b = find_block(c.key)) row[c.exec ? 1 : 0][b - kBlockTable] = c.milli;
	}
};
// Charges per block (count, fuel) [exec][op] while cbs::memo_stats().enabled (interp::charge_stats).
static std::array<std::array<std::array<long long, 2>, kNumBlocks>, 2>& charge_stats_table()
{
	static std::array<std::array<std::array<long long, 2>, kNumBlocks>, 2> t{};
	return t;
}
static const BlockCostTable& block_costs()
{
	static const BlockCostTable t;
	return t;
}

// Work counted while a block runs its own code (consumed when it finishes).
struct Work
{
	std::int64_t occ = 0, dests = 0, exp = 0, bits = 0;
};

std::vector<BlockCharge> charge_stats()
{
	std::vector<BlockCharge> out;
	for (int e = 0; e < 2; ++e)
		for (int i = 0; i < kNumBlocks; ++i)
			if (charge_stats_table()[e][i][0]) out.push_back({ (e ? "exec:" : "") + std::string(kBlockTable[i].key), charge_stats_table()[e][i][0], charge_stats_table()[e][i][1] });
	return out;
}

std::vector<std::string> supported_blocks()
{
	std::vector<std::string> out;
	for (auto& b : block_table()) out.push_back(b.key);
	return out;
}

// ---- program ---------------------------------------------------------------

struct Program
{
	std::unique_ptr<Expr[]> exprs;	   // argument nodes
	std::unique_ptr<Step[]> step_pool; // every block's steps, each block contiguous
	std::vector<std::string> strings;  // byte constants (reserved up front: views stay valid)
	Span<Step> steps;
};

// Programs are parsed from a compact code stream (one code per token) so that a bot can embed
// a pre-encoded policy and skip all string work (expensive inside wasm). Text input is
// encoded first. Codes: < kNumBlocks block index; kEnd, kEndTurn, kIf, kElse; kLet+t /
// kKeep+t (bind a new variable of type t); kNum then an index into the number table;
// kBytes then an index into the hex-string table; kVar + t*kMaxVars + i.
namespace codes
{
constexpr std::uint16_t kEnd = 0xFF00, kEndTurn = 0xFF01, kIf = 0xFF02, kElse = 0xFF03, kLet = 0xFE00, kKeep = 0xFD00, kNum = 0xFC00,
						kBytes = 0xFB00, kVar = 0xFA00;
}

namespace
{
int to_int(std::string_view s, int base = 10)
{
	int v = 0;
	if (std::from_chars(s.data(), s.data() + s.size(), v, base).ec != std::errc{}) throw std::runtime_error("policy: bad number " + std::string(s));
	return v;
}

int type_index(std::string_view name)
{
	for (int i = 0; i < kNumTypes; ++i)
		if (name == kTypes[i]) return i;
	throw std::runtime_error("policy: unknown type " + std::string(name));
}

std::string unhex(std::string_view s)
{
	std::string out;
	if (s == "-") return out;
	for (std::size_t i = 0; i + 1 < s.size(); i += 2) out.push_back(static_cast<char>(to_int(s.substr(i, 2), 16)));
	return out;
}

struct Parser
{
	const std::uint16_t* c;
	std::size_t n, pos = 0;
	const double* nums;
	std::size_t nnums;
	const char* const* bytes;
	std::size_t nbytes;
	int counts[kNumTypes] = {};
	// Pools sized to n codes (every node takes at least one code), filled front to back.
	Expr* exprs = nullptr;
	Step* step_pool = nullptr;
	std::size_t n_exprs = 0, n_steps = 0;
	std::vector<std::string>* strings = nullptr;

	std::uint16_t take()
	{
		if (pos >= n) throw std::runtime_error("policy: unexpected end of input");
		return c[pos++];
	}
	// Builds in place (no Expr/Step temporaries to move: each move is costly in a wasm bot).
	Expr expr()
	{
		Expr e;
		expr_into(e);
		return e;
	}
	void expr_into(Expr& e)
	{
		// Field by field: a whole-struct assignment compiles to memory.copy, ~1 fuel per byte in wasm.
		e.op = Op::const_num;
		e.var = -1;
		e.num = 0;
		e.bytes = {};
		e.args.p = nullptr;
		e.args.n = 0;
		const std::uint16_t t = take();
		if (t == codes::kNum)
		{
			const std::uint16_t k = take();
			if (k >= nnums) throw std::runtime_error("policy: bad number index");
			e.op = Op::const_num;
			e.num = nums[k];
		}
		else if (t == codes::kBytes)
		{
			const std::uint16_t k = take();
			if (k >= nbytes) throw std::runtime_error("policy: bad bytes index");
			e.op = Op::const_bytes;
			strings->push_back(unhex(bytes[k]));
			e.bytes = strings->back();
		}
		else if (t >= codes::kVar && t < codes::kVar + kNumTypes * kMaxVars)
		{
			e.op = Op::var;
			e.var = t - codes::kVar;
		}
		else if (t < kNumBlocks)
		{
			const BlockInfo& b = kBlockTable[t];
			e.op = b.op;
			const std::size_t k = n_exprs;
			n_exprs += static_cast<std::size_t>(b.arity);
			if (n_exprs > n) throw std::runtime_error("policy: expression pool overflow");
			e.args = { exprs + k, static_cast<std::uint32_t>(b.arity) };
			for (int i = 0; i < b.arity; ++i) expr_into(exprs[k + static_cast<std::size_t>(i)]);
		}
		else
			throw std::runtime_error("policy: bad code in expression");
	}
	// One block, ending at kEnd: its steps are gathered on a scratch stack (nested blocks are
	// gathered above them and moved to the pool first), then copied to the pool as one run.
	Step* scratch = nullptr; // n entries, uninitialised; used as a stack
	std::size_t n_scratch = 0;
	Span<Step> steps()
	{
		const std::size_t base = n_scratch;
		for (;;)
		{
			const std::uint16_t t = take();
			if (t == codes::kEnd)
			{
				const std::size_t m = n_scratch - base;
				if (n_steps + m > n) throw std::runtime_error("policy: step pool overflow");
				Step* dst = step_pool + n_steps;
				std::copy(scratch + base, scratch + n_scratch, dst);
				n_steps += m;
				n_scratch = base;
				return { dst, static_cast<std::uint32_t>(m) };
			}
			if (n_scratch == n) throw std::runtime_error("policy: step scratch overflow");
			Step& s = scratch[n_scratch++];
			s.kind = Step::do_;
			s.var = -1;
			s.then = {};
			s.orelse = {};
			if (t == codes::kEndTurn) s.kind = Step::end_turn;
			else if (t == codes::kIf)
			{
				s.kind = Step::if_;
				expr_into(s.expr);
				s.then = steps();
				if (pos < n && c[pos] == codes::kElse)
				{
					++pos;
					s.orelse = steps();
				}
			}
			else if ((t & 0xFF00) == codes::kLet || (t & 0xFF00) == codes::kKeep)
			{
				const int ty = t & 0xFF;
				if (ty >= kNumTypes) throw std::runtime_error("policy: bad type code");
				s.kind = (t & 0xFF00) == codes::kKeep ? Step::keep_ : Step::let_;
				expr_into(s.expr);
				if (counts[ty] >= kMaxVars) throw std::runtime_error("policy: too many variables");
				s.var = ty * kMaxVars + counts[ty]++;
			}
			else
			{
				--pos;
				s.kind = Step::do_;
				expr_into(s.expr);
			}
		}
	}
};
} // namespace

std::shared_ptr<const Program> load_program_static(const Step* steps, std::size_t n)
{
	auto prog = std::make_shared<Program>();
	prog->steps = { steps, static_cast<std::uint32_t>(n) };
	return prog;
}

static bool same_expr(const Expr& a, const Expr& b)
{
	if (a.op != b.op || a.var != b.var || !(a.num == b.num) || a.bytes != b.bytes || a.args.size() != b.args.size()) return false;
	for (std::size_t i = 0; i < a.args.size(); ++i)
		if (!same_expr(a.args[i], b.args[i])) return false;
	return true;
}
static bool same_steps(Span<Step> a, Span<Step> b)
{
	if (a.size() != b.size()) return false;
	for (std::size_t i = 0; i < a.size(); ++i)
	{
		const Step &x = a[i], &y = b[i];
		if (x.kind != y.kind || x.var != y.var || !same_steps(x.then, y.then) || !same_steps(x.orelse, y.orelse)) return false;
		if (x.kind != Step::end_turn && !same_expr(x.expr, y.expr)) return false;
	}
	return true;
}
bool same_program(const Program& a, const Program& b) { return same_steps(a.steps, b.steps); }

std::shared_ptr<const Program> load_program_codes(const std::uint16_t* code, std::size_t n, const double* nums, std::size_t nnums,
												  const char* const* bytes_hex, std::size_t nbytes)
{
	auto prog = std::make_shared<Program>();
	prog->exprs.reset(new Expr[n]);
	prog->step_pool.reset(new Step[n]);
	prog->strings.reserve(nbytes);
	Parser p{ code, n, 0, nums, nnums, bytes_hex, nbytes };
	p.exprs = prog->exprs.get();
	p.step_pool = prog->step_pool.get();
	p.strings = &prog->strings;
	std::unique_ptr<Step[]> scratch(new Step[n]);
	p.scratch = scratch.get();
	prog->steps = p.steps();
	if (p.pos != n) throw std::runtime_error("policy: trailing tokens");
	return prog;
}

// Simulated fuel is only trustworthy if every block has a measured cost: a policy using a block
// the calibration never exercised is refused (re-profile with policies/coverage.policy, see
// docs/FUEL.md). An effect step is charged its exec row; a pure block used as a step, and every
// argument, its eval row.
static void check_calibrated(const Program& prog)
{
	std::vector<std::string> missing;
	auto need = [&](Op op, bool exec)
	{
		const auto& t = block_costs();
		const int i = static_cast<int>(op);
		if (op >= Op::const_num || t.row[exec ? 1 : 0][i] || (exec && t.row[0][i])) return;
		const std::string k = kBlockTable[i].key;
		if (std::find(missing.begin(), missing.end(), k) == missing.end()) missing.push_back(k);
	};
	std::function<void(const Expr&)> expr = [&](const Expr& e)
	{
		need(e.op, false);
		for (const Expr& a : e.args) expr(a);
	};
	std::function<void(Span<Step>)> steps = [&](Span<Step> ss)
	{
		for (const Step& s : ss)
		{
			if (s.kind == Step::do_)
			{
				need(s.expr.op, true);
				for (const Expr& a : s.expr.args) expr(a);
			}
			else if (s.kind != Step::end_turn) expr(s.expr);
			steps(s.then);
			steps(s.orelse);
		}
	};
	steps(prog.steps);
	if (missing.empty()) return;
	std::string msg = "policy: no calibrated fuel cost for";
	for (const auto& k : missing) msg += " " + k;
	throw std::runtime_error(msg);
}

std::shared_ptr<const Program> load_program(const std::string& text)
{
	const std::size_t nl = text.find('\n');
	if (text.compare(0, nl, "policy v0") != 0) throw std::runtime_error("policy: missing 'policy v0' header");
	std::vector<std::uint16_t> code;
	std::vector<double> nums;
	std::vector<std::string> hex;
	bool num_next = false, bytes_next = false;
	std::istringstream in(nl == std::string::npos ? std::string() : text.substr(nl));
	for (std::string tok; in >> tok;)
	{
		if (num_next)
		{
			code.push_back(static_cast<std::uint16_t>(nums.size()));
			nums.push_back(std::strtod(tok.c_str(), nullptr));
			num_next = false;
		}
		else if (bytes_next)
		{
			code.push_back(static_cast<std::uint16_t>(hex.size()));
			hex.push_back(tok);
			bytes_next = false;
		}
		else if (tok == "END") code.push_back(codes::kEnd);
		else if (tok == "END_TURN") code.push_back(codes::kEndTurn);
		else if (tok == "IF") code.push_back(codes::kIf);
		else if (tok == "ELSE") code.push_back(codes::kElse);
		else if (tok == "CONST:Num") code.push_back(codes::kNum), num_next = true;
		else if (tok == "CONST:Bytes") code.push_back(codes::kBytes), bytes_next = true;
		else if (tok.rfind("LET:", 0) == 0) code.push_back(static_cast<std::uint16_t>(codes::kLet + type_index(std::string_view(tok).substr(4))));
		else if (tok.rfind("KEEP:", 0) == 0) code.push_back(static_cast<std::uint16_t>(codes::kKeep + type_index(std::string_view(tok).substr(5))));
		else if (tok.rfind("VAR:", 0) == 0)
		{
			const std::string_view v(tok);
			const auto c2 = v.find(':', 4);
			code.push_back(static_cast<std::uint16_t>(codes::kVar + type_index(v.substr(4, c2 - 4)) * kMaxVars + to_int(v.substr(c2 + 1))));
		}
		else
		{
			const BlockInfo* b = find_block(tok);
			if (!b) throw std::runtime_error("policy: unknown block " + tok);
			code.push_back(static_cast<std::uint16_t>(b - kBlockTable));
		}
	}
	std::vector<const char*> hp;
	for (auto& h : hex) hp.push_back(h.c_str());
	auto prog = load_program_codes(code.data(), code.size(), nums.data(), nums.size(), hp.data(), hp.size());
	check_calibrated(*prog);
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
	Vec2 idle_pos = { -1, -1 };
	int idle_turns = 0;
	std::uint64_t idle_last_turn = ~0ull;
	std::vector<std::uint32_t> camp_ids;

	const cbs::Map& m() const { return api.map(); }

	// Shared-memory layout used by the team-communication blocks.
	static constexpr int kClaimBytes = 6, kTargetByte = 6;
	int slot_ = -2; // this champion's index among its team's champion ids (-1: none)
	int my_slot()
	{
		if (slot_ != -2) return slot_;
		slot_ = -1;
		if (api.champ() < 0) return slot_;
		std::uint32_t ids[16], n = 0;
		api.allies(ids, 16, &n);
		const std::uint32_t me_id = self();
		int rank = 0;
		for (std::uint32_t i = 0; i < n && i < 16; ++i)
			if (ids[i] < me_id) ++rank;
		slot_ = rank < kClaimBytes ? rank : -1;
		return slot_;
	}
	int group_at(Vec2 p) const
	{
		if (!m().in_bounds(p)) return -1;
		const int c = m().camp_at[m().idx(p)];
		return c < 0 ? -1 : m().camps[c].group;
	}
	Work work;
	struct Charge
	{
		Interp& in;
		Op op;
		bool exec;
		bool skip = false;
		// Only the simulator charges (the real bot's engine meters fuel itself, and the
		// uncaught_exceptions() calls cost fuel there on every block).
		int unwinding = in.api.count_charges ? std::uncaught_exceptions() : 0;
		// May throw: a charge can suspend the bot, and cancelling a suspended bot resumes it with
		// an exception. Never charges while already unwinding.
		~Charge() noexcept(false)
		{
			if (!skip && in.api.count_charges && std::uncaught_exceptions() == unwinding) in.charge_block(op, exec);
		}
	};
	std::int64_t blocks_this_turn = 0;
	void charge_block(Op op, bool exec)
	{
		if (!api.count_charges) return; // real bot: the engine meters fuel, skip the bookkeeping
		++blocks_this_turn;
		const std::int64_t* c = block_costs().row[exec ? 1 : 0][static_cast<int>(op)];
		const Work w = work;
		work = {};
		if (!c)
		{
			api.compute(kUncalibratedBlockMilli / 1000);
			return;
		}
		const std::int64_t H = m().H, ch = static_cast<std::int64_t>((m().W + 7) / 8) * ((m().H + 7) / 8);
		const std::int64_t f[10] = { 1, H, ch, w.occ, w.occ * H, w.dests, w.exp * ch, static_cast<std::int64_t>(m().camps.size()),
									 static_cast<std::int64_t>(m().groups.size()), w.bits };
		std::int64_t milli = 0;
		for (int i = 0; i < 10; ++i) milli += c[i] * f[i];
		if (cbs::memo_stats().enabled)
		{
			auto& st = charge_stats_table()[exec ? 1 : 0][static_cast<int>(op)];
			++st[0];
			st[1] += std::max<std::int64_t>(0, milli / 1000);
		}
		api.compute(std::max<std::int64_t>(0, milli / 1000));
	}
	// Distance field through the API, recording its work for the calling block's cost.
	int distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, Bitboard& visited)
	{
		field.resize(static_cast<std::size_t>(m().W) * m().H);
		const int n = api.distance_field(walls, roots, dests, cbs::kUnreachable, field.data(), visited);
		if (api.count_charges)
		{
			work.exp += api.last_field.layers;
			work.dests += api.last_field.dests;
		}
		return n;
	}

	// false for the draft bot or when the champion record is unavailable
	bool me(ChampionInfo& ci)
	{
		if (api.champ() < 0) return false;
		return api.champion(static_cast<std::uint32_t>(api.my_champion()), &ci) == Err::success;
	}
	std::uint32_t self() { return static_cast<std::uint32_t>(api.my_champion()); }

	void turn()
	{
		++turn_no;
		// The deploy bot's one-off start-up (map, camp layout, allocator; the policy is embedded
		// pre-parsed; bot/src/main.cpp) on a champion's first turn, measured on 24 cambc games of
		// v5d / fs-1 as first-turn fuel minus the simulator's charge for that turn (docs/FUEL.md):
		// mae 1.3k on a mean of 47k.
		if (turn_no == 1 && api.champ() >= 0 && api.count_charges)
			api.compute(21662 + 2281 * m().W * m().H / 1000 + 247 * static_cast<std::int64_t>(m().camps.size()) +
						387 * static_cast<std::int64_t>(m().groups.size()));
		const std::uint64_t calls0 = api.api_calls;
		const std::int64_t spent0 = api.spent;
		last_end = last_do = nullptr;
		trace_target = trace_step = kNoTile;
		trace_dist = -1;
		blocks_this_turn = 0;
		run(prog.steps);
		// The step loop itself (Value temporaries etc. between blocks) and the calibration's
		// per-block / per-call corrections (block_costs_gen.inc), which may be negative; never
		// below zero for the turn as a whole.
		if (api.count_charges)
		{
			const auto adj = static_cast<std::int64_t>(
				INTERP_TURN_COST(blocks_this_turn, m().H, static_cast<std::int64_t>(api.api_calls - calls0)));
			api.compute(std::max<std::int64_t>(adj, -std::max<std::int64_t>(0, api.spent - spent0)));
			trace_turn();
		}
	}

	// Returns false when END_TURN was reached.
	// Simulator diagnostics (INTERP_TRACE=1): the END_TURN that ended the turn and the last
	// effect step run, as their ordinals in source order.
	const Step* last_end = nullptr;
	const Step* last_do = nullptr;
	Vec2 trace_target = kNoTile, trace_step = kNoTile;
	int trace_dist = -1;
	static int ordinal(Span<Step> steps, const Step* want, Step::Kind kind, int& k)
	{
		for (const Step& s : steps)
		{
			if (s.kind == kind && ++k && &s == want) return k;
			if (s.kind == Step::if_)
			{
				if (const int r = ordinal(s.then, want, kind, k)) return r;
				if (const int r = ordinal(s.orelse, want, kind, k)) return r;
			}
		}
		return 0;
	}
	void trace_turn()
	{
		static const bool on = std::getenv("INTERP_TRACE") != nullptr;
		if (!on || api.champ() < 0) return;
		const cbs::Game& g = api.game();
		const cbs::Champion& c = g.champs[api.champ()];
		int k1 = 0, k2 = 0;
		const int e = last_end ? ordinal(prog.steps, last_end, Step::end_turn, k1) : 0;
		const int d = last_do ? ordinal(prog.steps, last_do, Step::do_, k2) : 0;
		const char* act = last_do ? kBlockTable[static_cast<int>(last_do->expr.op)].key : "-";
		std::printf("@@TR r=%d team=%d champ=%d alive=%d pos=%d,%d hp=%.0f/%.0f gems=%u gold=%u submitted=%lld end_turn#%d last_do#%d %s\n",
					g.round, api.team(), api.champ(), c.alive ? 1 : 0, c.pos.x, c.pos.y, static_cast<double>(c.hp),
					static_cast<double>(c.max_hp), c.gems, c.gold_int(), static_cast<long long>(g.teams[api.team()].submitted), e, d, act);
		if (trace_target.x >= 0)
			std::printf("@@TRM   move_towards target %d,%d step %d,%d field %d\n", trace_target.x, trace_target.y, trace_step.x, trace_step.y, trace_dist);
		if (const char* tl = std::getenv("INTERP_TRACE_TILES")) // "x,y;x,y": blocked as this champion sees it
		{
			const Bitboard& b = blocked_tiles(c.pos);
			std::printf("@@TRB  ");
			for (const char* q = tl; *q;)
			{
				int x = 0, y = 0, n = 0;
				if (std::sscanf(q, "%d,%d%n", &x, &y, &n) < 2) break;
				std::printf(" %d,%d:%d", x, y, b.test(x, y) ? 1 : 0);
				q += n;
				if (*q == ';') ++q;
			}
			std::printf("\n");
		}
		if (const char* rc = std::getenv("INTERP_TRACE_CAMPS"))
			for (const auto& cp : g.camps)
				if (cbs::chebyshev(cp.pos, c.pos) <= std::max(1, std::atoi(rc)))
					std::printf("@@TRC   camp %d,%d group %d life %d hp %.0f\n", cp.pos.x, cp.pos.y, cp.group, static_cast<int>(cp.life),
								static_cast<double>(cp.hp));
	}

	bool run(Span<Step> steps)
	{
		for (const Step& s : steps)
		{
			switch (s.kind)
			{
			case Step::end_turn: last_end = &s; return false;
			case Step::do_: last_do = &s; exec(s.expr); break;
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

	// Occupancy is cached within a turn until anything that can change it: an effect other
	// than moving (it may kill or move units), or a move or dash attempt (our vision, and so
	// the visible occupancy, changes; even a failed one can reveal a tile). `epoch` counts those. Whole-board work is
	// expensive in a wasm bot (docs/FUEL.md), so this saves fuel there and charges in the sim.
	std::uint64_t turn_no = 0, epoch = 0, cache_turn = ~0ull, cache_epoch = ~0ull;
	bool static_ready = false;
	Bitboard static_block, dyn_block, camps_cache;

	void refresh_occupancy(Vec2 me)
	{
		if (cache_turn == turn_no && cache_epoch == epoch) return;
		cache_turn = turn_no;
		cache_epoch = epoch;
		++work.occ;
		Bitboard occ;
		api.ally_occupancy(dyn_block);
		dyn_block.reset(me);
		api.enemy_occupancy(occ);
		dyn_block |= occ;
		api.camp_occupancy(camps_cache, 0);
		dyn_block |= camps_cache;
	}
	const Bitboard& camp_occupancy(Vec2 me)
	{
		refresh_occupancy(me);
		return camps_cache;
	}

	// Blocked tiles for the champion at `me`; rebuilt only when the occupancy is refreshed or
	// the champion moved (both bump `epoch` or the turn).
	std::uint64_t blocked_turn = ~0ull, blocked_epoch = ~0ull;
	Vec2 blocked_me = kNoTile;
	Bitboard blocked_cache;
	const Bitboard& blocked_tiles(Vec2 me)
	{
		if (!static_ready)
		{
			static_block = m().walls;
			static_block |= m().holes;
			static_block |= m().altars;
			static_block |= m().spawn_mask[1 - api.team()];
			static_ready = true;
		}
		refresh_occupancy(me);
		if (blocked_turn != turn_no || blocked_epoch != epoch || !(blocked_me == me))
		{
			blocked_cache = static_block;
			blocked_cache |= dyn_block;
			blocked_cache.reset(me);
			blocked_turn = turn_no;
			blocked_epoch = epoch;
			blocked_me = me;
		}
		return blocked_cache;
	}

	// The starter bot's move_towards_closest: distance field from the goals, step downhill.
	void move_towards_goals(Bitboard goals, Vec2 me)
	{
		if (goals.test(me)) return;
		const Bitboard& blocked = blocked_tiles(me);
		const Bitboard& camps = camp_occupancy(me);
		Bitboard taken = blocked;
		taken.andnot(camps);
		goals.andnot(taken);
		if (!goals.any(m().H)) return;
		Bitboard walls = blocked, dest, visited;
		walls.andnot(goals);
		dest.set(me);
		distance_field(walls, goals, &dest, visited);
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
		trace_step = best;
		trace_dist = bd;
		if (best == me) return;
		std::int32_t ok = 0;
		api.move_to(best, &ok);
		++epoch; // our vision changed (we moved, or a failed move revealed a hidden unit)
	}

	// Landing tile within 2 steps that is closest (by walking distance) to `goal`, or none.
	Vec2 dash_target(Vec2 goal, Vec2 me)
	{
		if (goal == me) return kNoTile;
		const Bitboard& blocked = blocked_tiles(me);
		Bitboard root, visited, box;
		Bitboard walls = blocked;
		walls.reset(goal);
		root.set(goal);
		// Stop the search at the first layer touching the 5x5 box around us: every candidate
		// at the minimum distance is in that layer, so the choice is unchanged.
		cbs::draw_chebyshev(box, m().W, m().H, me, 2.0f);
		box.reset(goal); // the root is not a candidate and must not end the search
		distance_field(walls, root, &box, visited);
		Vec2 best = kNoTile;
		std::uint16_t bd = field[m().idx(me)];
		for (int dy = -2; dy <= 2; ++dy)
			for (int dx = -2; dx <= 2; ++dx)
			{
				const Vec2 p{ me.x + dx, me.y + dy };
				if (!m().in_bounds(p) || blocked.test(p) || p == me) continue;
				if (field[m().idx(p)] < bd)
				{
					bd = field[m().idx(p)];
					best = p;
				}
			}
		return best;
	}

	// Nearest tile of `set` by walking distance (same seeding rule as move_towards_goals).
	Vec2 closest(const Bitboard& set)
	{
		ChampionInfo ci{};
		if (!me(ci)) return kNoTile;
		const Vec2 pos{ ci.x, ci.y };
		if (set.test(pos)) return pos;
		const Bitboard& blocked = blocked_tiles(pos);
		const Bitboard& camps = camp_occupancy(pos);
		Bitboard cand = set, taken = blocked;
		taken.andnot(camps);
		cand.andnot(taken);
		if (!cand.any(m().H)) return kNoTile;
		Bitboard walls = blocked;
		walls.andnot(cand);
		Vec2 best = kNoTile;
		int n = 0;
		if (!api.nearest_by_walk(walls, pos, cand, best, &n)) best = kNoTile;
		if (api.count_charges)
		{
			work.exp += api.last_field.layers;
			work.dests += api.last_field.dests;
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
		Charge charge{ *this, e.op, false };
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
			for (int i = 0; i < 12; ++i)
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
		case Op::wolf_tiles:
		case Op::elk_tiles:
		case Op::gem_cluster_tiles:
		case Op::gold_cluster_tiles:
		case Op::monolith_tiles:
		case Op::golem_tiles:
		{
			// order matches cbs::CampType: wolf, elk, gem_cluster, gold_cluster, monolith, golem
			const int want = static_cast<int>(e.op) - static_cast<int>(Op::wolf_tiles);
			Bitboard b;
			for (auto& c : m().camps)
				if (static_cast<int>(c.type) == want) b.set(c.pos);
			return set_of(b);
		}
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
			api.visible_camps(camp_ids);
			r.units->reserve(camp_ids.size());
			for (std::uint32_t c : camp_ids) r.units->push_back({ EntityKind::camp, c });
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
			if (api.count_charges) work.bits += s.set->count(m().H);
			Bitboard b;
			s.set->for_each_unordered(m().H, [&](int x, int y) { cbs::draw_chebyshev(b, m().W, m().H, { x, y }, r); });
			return set_of(b);
		}
		case Op::closest: return tile(closest(*eval(a[0]).set));
		case Op::filter_tiles:
		{
			const Value s = eval(a[0]), p = eval(a[1]);
			if (api.count_charges) work.bits += s.set->count(m().H);
			Bitboard b;
			if (has_tile(p.tile))
				s.set->for_each_unordered(m().H, [&](int x, int y) {
					if (cbs::chebyshev({ x, y }, p.tile) <= p.n) b.set(x, y);
				});
			return set_of(b);
		}
		case Op::first_tile:
		{
			const Value s = eval(a[0]);
			if (api.count_charges) work.bits += s.set->count(m().H);
			Vec2 p;
			return tile(s.set->first(m().H, p) ? p : kNoTile);
		}
		case Op::exists_tile: return num(has_tile(eval(a[0]).tile));
		case Op::count_tiles:
		{
			const int n = eval(a[0]).set->count(m().H);
			work.bits += n;
			return num(n);
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
		case Op::champ_tavi:
		case Op::champ_heart_of_ruin: return num(static_cast<int>(e.op) - static_cast<int>(Op::champ_ryth));
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
		case Op::family_monster:
		case Op::family_power:
		case Op::family_durability:
		case Op::family_treasure:
		case Op::family_jungle:
		case Op::family_home:
		case Op::family_bruiser: return num(static_cast<int>(e.op) - static_cast<int>(Op::family_monster));
		case Op::shard_of:
		{
			// item id = 6 * family + 2 * stat (strength, focus, health); +1 would be the emblem
			const int fam = std::clamp(static_cast<int>(eval(a[0]).n), 0, 6);
			const int st = std::clamp(static_cast<int>(eval(a[1]).n), 0, 2);
			return num(6 * fam + 2 * st);
		}
		case Op::has_altar_lock:
		case Op::has_teleport:
		{
			if (api.champ() < 0) return num(0);
			std::uint32_t c[4] = {};
			api.champion_consumables(self(), c);
			return num(c[e.op == Op::has_altar_lock ? cbs::consumable::altar_lock : cbs::consumable::tp_crystal] > 0);
		}
		case Op::i_am_ranged:
		{
			ChampionInfo ci{};
			return num(me(ci) && ci.attack_range > 1);
		}
		case Op::slot_is_dash:
		case Op::slot_is_damage:
		case Op::slot_is_aoe:
		case Op::slot_is_stun:
		case Op::slot_is_heal:
		case Op::slot_is_shield:
		case Op::slot_is_reset:
		{
			const int slot = std::clamp(static_cast<int>(eval(a[0]).n), 0, 1);
			if (api.champ() < 0) return num(0);
			cbs::AbilityProps ap{};
			if (api.champion_ability_props(self(), static_cast<std::uint32_t>(slot), &ap) != Err::success) return num(0);
			using K = cbs::AbilityKind;
			const K k = static_cast<K>(ap.kind);
			switch (e.op)
			{
			case Op::slot_is_dash: return num(k == K::dash);
			case Op::slot_is_damage: return num(k == K::damage);
			case Op::slot_is_aoe: return num(k == K::aoe_damage);
			case Op::slot_is_stun: return num(k == K::cc);
			case Op::slot_is_heal: return num(k == K::heal);
			case Op::slot_is_shield: return num(k == K::shield);
			default: return num(k == K::attack_reset);
			}
		}
		case Op::weakest:
		case Op::richest:
		case Op::nearest:
		{
			const Value l = eval(a[0]);
			Value r;
			ChampionInfo ci{};
			const bool have_me = me(ci);
			double best = 1e18;
			for (const Unit& u : *l.units)
			{
				Vec2 pos;
				double hp;
				if (!unit_info(u, pos, hp)) continue;
				double key = hp;
				if (e.op == Op::richest)
				{
					std::uint32_t g = 0;
					if (u.kind == EntityKind::champion) api.champion_gems(u.h, &g);
					key = -static_cast<double>(g);
				}
				else if (e.op == Op::nearest)
					key = have_me ? cbs::chebyshev({ ci.x, ci.y }, pos) : 0;
				if (key < best)
				{
					best = key;
					r.unit = u;
				}
			}
			return r;
		}
		case Op::claimed_by_allies:
		{
			std::uint8_t mem[kClaimBytes] = {};
			api.read_shared_memory(0, mem, kClaimBytes);
			const int mine = my_slot();
			Bitboard b;
			for (int i = 0; i < kClaimBytes; ++i)
			{
				const int g = static_cast<int>(mem[i]) - 1;
				if (i == mine || g < 0 || g >= static_cast<int>(m().groups.size())) continue;
				for (int c : m().groups[g].camps) b.set(m().camps[c].pos);
			}
			return set_of(b);
		}
		case Op::claim_count:
		{
			const int g = group_at(eval(a[0]).tile);
			std::uint8_t mem[kClaimBytes] = {};
			api.read_shared_memory(0, mem, kClaimBytes);
			const int mine = my_slot();
			int n = 0;
			for (int i = 0; i < kClaimBytes; ++i)
				if (i != mine && g >= 0 && mem[i] == g + 1) ++n;
			return num(n);
		}
		case Op::team_target:
		{
			std::uint8_t v = 0;
			api.read_shared_memory(kTargetByte, &v, 1);
			Value r;
			if (v > 0) r.unit = { EntityKind::champion, static_cast<std::uint32_t>(v - 1) };
			return r;
		}
		case Op::in_danger:
		{
			ChampionInfo ci{};
			if (!me(ci)) return num(0);
			const Vec2 pos{ ci.x, ci.y };
			for (std::uint32_t c = 0; c < m().camps.size(); ++c)
			{
				const int range = cbs::camp_design(m().camps[c].type).attack_range;
				if (range <= 0 || cbs::chebyshev(pos, m().camps[c].pos) > range + 2) continue; // camps don't chase
				std::uint32_t life = 0;
				if (api.camp_state(c, &life) != Err::success || life != static_cast<std::uint32_t>(cbs::CampLife::awake)) continue;
				cbs::CampRecord cr{};
				if (api.camp(c, &cr) == Err::success && cr.health > 0 && cbs::chebyshev(pos, { cr.x, cr.y }) <= range) return num(1);
			}
			std::uint32_t ids[16], n = 0;
			api.enemies(ids, 16, &n);
			for (std::uint32_t i = 0; i < n && i < 16; ++i)
			{
				ChampionInfo ei{};
				if (api.champion(ids[i], &ei) != Err::success || !(ei.state & state_bit::alive)) continue;
				if (cbs::chebyshev(pos, { ei.x, ei.y }) <= ei.attack_range + 1) return num(1);
			}
			return num(0);
		}
		case Op::allies_within:
		{
			const double r = eval(a[0]).n;
			ChampionInfo ci{};
			if (!me(ci)) return num(0);
			const Value l = champions(false);
			int k = 0;
			for (const Unit& u : *l.units)
			{
				Vec2 p;
				double hp;
				if (unit_info(u, p, hp) && cbs::chebyshev({ ci.x, ci.y }, p) <= r) ++k;
			}
			return num(k);
		}
		case Op::enemies_within:
		{
			const double r = eval(a[0]).n;
			ChampionInfo ci{};
			if (!me(ci)) return num(0);
			std::uint32_t ids[16], n = 0;
			api.enemies(ids, 16, &n);
			int k = 0;
			for (std::uint32_t i = 0; i < n && i < 16; ++i)
			{
				ChampionInfo ei{};
				if (api.champion(ids[i], &ei) == Err::success && (ei.state & state_bit::alive) &&
					cbs::chebyshev({ ci.x, ci.y }, { ei.x, ei.y }) <= r)
					++k;
			}
			return num(k);
		}
		case Op::local_strength:
		{
			// (total health x total damage) of us and visible allies within r, over the same for
			// visible enemy champions within r (Lanchester square law); damage per unit is
			// strength + focus / 2. 100 when no enemy is within r.
			const double r = eval(a[0]).n;
			ChampionInfo ci{};
			if (!me(ci)) return num(0);
			double hp[2] = { ci.health, 0 }, dmg[2] = { ci.strength + 0.5 * ci.focus, 0 };
			for (int side = 0; side < 2; ++side)
			{
				std::uint32_t ids[16], n = 0;
				side ? api.enemies(ids, 16, &n) : api.allies(ids, 16, &n);
				for (std::uint32_t i = 0; i < n && i < 16; ++i)
				{
					if (side == 0 && ids[i] == self()) continue;
					ChampionInfo ei{};
					if (api.champion(ids[i], &ei) != Err::success || !(ei.state & state_bit::alive) ||
						cbs::chebyshev({ ci.x, ci.y }, { ei.x, ei.y }) > r)
						continue;
					hp[side] += ei.health;
					dmg[side] += ei.strength + 0.5 * ei.focus;
				}
			}
			if (hp[1] <= 0) return num(100);
			return num(std::min(100.0, hp[0] * dmg[0] / std::max(1e-6, hp[1] * dmg[1])));
		}
		case Op::unit_health_frac:
		{
			const Unit u = eval(a[0]).unit;
			if (u.kind == EntityKind::champion)
			{
				ChampionInfo ei{};
				if (api.champion(u.h, &ei) == Err::success && ei.max_health > 0) return num(ei.health / ei.max_health);
			}
			else if (u.kind == EntityKind::camp)
			{
				cbs::CampRecord cr{};
				if (api.camp(u.h, &cr) == Err::success && cr.max_health > 0) return num(cr.health / cr.max_health);
			}
			return num(0);
		}
		case Op::capturable_spawns:
		{
			Bitboard b;
			for (std::size_t g = 0; g < m().groups.size(); ++g)
			{
				std::uint32_t gs = 0;
				if (api.camp_group_state(static_cast<std::uint32_t>(g), &gs) != Err::success) continue;
				if (gs != static_cast<std::uint32_t>(cbs::GroupState::reward)) continue;
				for (int c : m().groups[g].camps) b.set(m().camps[c].pos);
			}
			return set_of(b);
		}
		case Op::turns_idle:
		{
			ChampionInfo ci{};
			if (!me(ci)) return num(0);
			const Vec2 p{ ci.x, ci.y };
			if (turn_no != idle_last_turn)
			{
				idle_turns = (p == idle_pos && idle_last_turn == turn_no - 1) ? idle_turns + 1 : 0;
				idle_pos = p;
				idle_last_turn = turn_no;
			}
			return num(idle_turns);
		}
		case Op::unit_gems:
		{
			const Unit u = eval(a[0]).unit;
			std::uint32_t g = 0;
			if (u.kind == EntityKind::champion) api.champion_gems(u.h, &g);
			return num(g);
		}
		case Op::team_score:
		{
			std::uint32_t g = 0;
			api.submitted_gems(static_cast<std::uint32_t>(eval(a[0]).n), &g);
			return num(g);
		}
		case Op::map_width: return num(m().W);
		case Op::map_height: return num(m().H);
		case Op::camp_count: return num(static_cast<double>(m().camps.size()));
		case Op::shard: return num(6 + 2 * std::clamp(static_cast<int>(eval(a[0]).n), 0, 2)); // power shard
		default: break;
		}
		exec(e); // an effect used as a value (cannot happen in well-typed policies)
		return Value{};
	}

	void exec(const Expr& e)
	{
		Charge charge{ *this, e.op, true };
		const auto& a = e.args;
		std::int32_t ok = 0;
		if (e.op != Op::move_towards && e.op != Op::dash_towards && e.op != Op::set_priority && e.op != Op::write_shared) ++epoch;
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
			trace_target = t;
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
		case Op::move_away_from:
		{
			const Vec2 t = eval(a[0]).tile;
			ChampionInfo ci{};
			if (!has_tile(t) || !me(ci)) break;
			const Vec2 pos{ ci.x, ci.y };
			const Bitboard blocked = blocked_tiles(pos);
			Vec2 best = pos;
			int bd = cbs::chebyshev(pos, t);
			for (int dy = -1; dy <= 1; ++dy)
				for (int dx = -1; dx <= 1; ++dx)
				{
					const Vec2 p{ pos.x + dx, pos.y + dy };
					if (!m().in_bounds(p) || blocked.test(p)) continue;
					const int d = cbs::chebyshev(p, t);
					if (d > bd)
					{
						bd = d;
						best = p;
					}
				}
			if (!(best == pos)) api.move_to(best, &ok);
			break;
		}
		case Op::claim:
		case Op::unclaim:
		{
			const int g = e.op == Op::claim ? group_at(eval(a[0]).tile) : -1;
			const int slot = my_slot();
			if (slot < 0) break;
			const std::uint8_t v = static_cast<std::uint8_t>(g < 0 || g > 254 ? 0 : g + 1);
			api.write_shared_memory(slot, &v, 1);
			break;
		}
		case Op::set_team_target:
		{
			const Unit u = eval(a[0]).unit;
			const std::uint8_t v = static_cast<std::uint8_t>(u.kind == EntityKind::champion && u.h < 255 ? u.h + 1 : 0);
			api.write_shared_memory(kTargetByte, &v, 1);
			break;
		}
		case Op::buy_altar_lock: api.buy_consumable(cbs::consumable::altar_lock); break;
		case Op::buy_teleport: api.buy_consumable(cbs::consumable::tp_crystal); break;
		case Op::place_altar_lock:
		case Op::teleport_to:
		{
			const Vec2 t = eval(a[0]).tile;
			const int type = e.op == Op::place_altar_lock ? cbs::consumable::altar_lock : cbs::consumable::tp_crystal;
			if (has_tile(t)) api.use_consumable(type, t, &ok);
			break;
		}
		case Op::dash_towards:
		{
			const int slot = std::clamp(static_cast<int>(eval(a[0]).n), 0, 1);
			const Vec2 t = eval(a[1]).tile;
			ChampionInfo ci{};
			if (!has_tile(t) || !me(ci)) break;
			const Vec2 d = dash_target(t, { ci.x, ci.y });
			if (has_tile(d))
			{
				api.cast(static_cast<std::uint32_t>(slot), 0, 0, d, &ok);
				++epoch;
			}
			break;
		}
		case Op::buy:
		{
			const int item = static_cast<int>(eval(a[0]).n);
			const double n = std::floor(eval(a[1]).n);
			if (n >= 1) api.buy_item(static_cast<std::uint32_t>(item), static_cast<std::uint32_t>(std::min(n, 1000.0)));
			break;
		}
		case Op::set_priority: api.set_priority(static_cast<std::int32_t>(std::clamp(eval(a[0]).n, -1e6, 1e6))); break;
		default: // a pure block used as a step: evaluate it (eval charges it)
			charge.skip = true;
			eval(e);
			break;
		}
	}
};

class PolicyPlayer : public cbs::Player
{
public:
	PolicyPlayer(std::shared_ptr<const Program> p, std::uint64_t seed, bool bot_seeds = false)
		: prog_(std::move(p)), seed_(seed), bot_seeds_(bot_seeds)
	{
	}
	const cbs::PriceTable* prices() const override { return &cbs::PriceTable::bot_wrapper(); }
	cbs::BotBody make_bot(int team, int champ) override
	{
		// bot_seeds: the deploy bot's seed for this instance (bot/src/main.cpp), so a simulated
		// game makes the same random choices as the same game in cambc.
		const std::uint64_t base = bot_seeds_ ? 0x5eed0000u + static_cast<unsigned>(team * 64 + champ + 1) : seed_;
		const std::uint64_t s = (base * 0x9E3779B97F4A7C15ull) ^ (static_cast<std::uint64_t>(team) << 32) ^
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
	bool bot_seeds_;
};
} // namespace

std::unique_ptr<cbs::Player> make_policy_player(std::shared_ptr<const Program> program, std::uint64_t seed, bool bot_seeds)
{
	return std::make_unique<PolicyPlayer>(std::move(program), seed, bot_seeds);
}
} // namespace interp
