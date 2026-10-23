// Full game state and rules. All mutation goes through Game; bots see the game only
// through cbs::Api (api.h), which enforces each champion's perspective.
#pragma once
#include <array>
#include <memory>
#include <vector>
#include "cbs/map.h"

namespace cbs
{
enum class BuffType : std::uint8_t { shield = 0, stun = 1, enhanced_attack = 2 };

struct Buff
{
	BuffType type;
	int duration;
	float value; // shield amount
};

constexpr int kMaxBuffs = 8;
struct BuffList
{
	Buff b[kMaxBuffs];
	int n = 0;
	void add(Buff x)
	{
		if (n < kMaxBuffs) b[n++] = x;
	}
	void remove(int i)
	{
		for (int k = i + 1; k < n; ++k) b[k - 1] = b[k];
		--n;
	}
	bool has(BuffType t) const
	{
		for (int i = 0; i < n; ++i)
			if (b[i].type == t) return true;
		return false;
	}
	int find(BuffType t) const
	{
		for (int i = 0; i < n; ++i)
			if (b[i].type == t) return i;
		return -1;
	}
};

enum class Channel : std::uint8_t { none, recall, tribute, teleport };

struct Champion
{
	int id = 0, team = 0;
	ChampionType type{};
	int partner = -1; // Cassi <-> Issac
	bool alive = true;
	Vec2 pos{};
	float hp = 0;
	int items[kNumItems] = {};
	int health_pts = 0, strength_pts = 0, focus_pts = 0;
	std::uint32_t passives = 0; // bit per ItemPassive
	float max_hp = 0, strength = 0, focus = 0;
	// Gold is kept exactly in hundredths (bonus gold accumulates fractions); the API reports floor(gold).
	std::int64_t gold_cents = 0;
	std::uint32_t gems = 0;
	std::int64_t earned_gold_cents = 0;
	std::uint64_t spent_gold = 0;
	std::uint32_t gold_int() const { return static_cast<std::uint32_t>(gold_cents / 100); }
	double gold() const { return static_cast<double>(gold_cents) / 100.0; }
	int cons[kNumConsumables] = {};
	int cooldown[2] = {};
	BuffList buffs;
	int ward_charges = 1, ward_cooldown = 0;
	bool ward_active = false;
	Vec2 ward_pos{};
	Channel channel = Channel::none;
	int channel_timer = 0;
	Vec2 channel_target{};
	int priority = 0, next_priority = 0;
	int respawn_timer = 0;
	int kills = 0, deaths = 0;
	// Per-turn allowances and flags.
	bool moved = false, attacked = false, cast = false, cast_exclusive = false;
	bool recall_started = false, submit_started = false, recall_cancelled = false, submit_cancelled = false, sold = false;
	bool completed_turn = false;
	bool attack_reset = false; // an attack reset restored the attack allowance this turn
	int revealed_n = 0;
	Vec2 revealed[8];
	// Camp groups this champion has seen respawning (the engine keeps reporting them until they respawn).
	std::vector<std::uint8_t> seen_respawning;

	bool has_passive(ItemPassive p) const { return passives >> static_cast<int>(p) & 1; }
};

enum class CampLife : std::uint8_t { dead = 0, awake = 1, asleep = 2 };

struct Camp
{
	CampType type{};
	int group = 0;
	Vec2 pos{};
	float hp = 0, max_hp = 0, strength = 0, focus = 0;
	CampLife life = CampLife::asleep;
	int cooldown[2] = {};
	BuffList buffs;
	// Sleep timer: reset to camp_sleep_time when woken or when the camp acquires a target,
	// decremented at each camp turn end; a camp with no target and a zero timer falls asleep.
	int sleep_timer = 0;
};

enum class GroupState : std::uint8_t { alive = 1, reward = 2, respawning = 3 };

struct Group
{
	GroupState state = GroupState::alive;
	int respawn_timer = 0;
	int capture_team = -1, capture_timer = 0;
};

struct Ward
{
	int owner, team;
	Vec2 pos;
};

struct AltarLock
{
	int handle, team;
	Vec2 pos;
	int hits;
};

struct TeamState
{
	std::uint32_t submitted = 0;
	std::int64_t earned_gold_cents = 0;
	int kills = 0;
	std::uint8_t shared[kSharedMemory] = {};
	std::uint8_t draft_mem[kDraftMemory] = {};
	std::uint32_t draft_mem_size = 0;
	int picks[6] = { -1, -1, -1, -1, -1, -1 };
	int npicks = 0;
};

struct DraftState
{
	int rounds = 5;
	int round = 0;		// current draft round
	int pending[2] = { -1, -1 }; // pick submitted this draft round
	bool done = false;
};

struct GameResult
{
	int winner = -1; // 0 = team A, 1 = team B
	int reason = 0;	 // 1 gems reached, 2 round limit, 3 resign/crash
	int rounds = 0;
};

class Game
{
public:
	explicit Game(std::shared_ptr<const Map> map);

	const Map& map() const { return *map_; }
	std::shared_ptr<const Map> map_ptr() const { return map_; }

	// ---- draft ----
	DraftState draft;
	TeamState teams[2];
	Err draft_pick(int team, int choice);
	// Resolve the current draft round (missing picks are filled from `rng`).
	void draft_end_round(std::uint64_t& rng);
	// Create champions from the picks and place them on spawn.
	void start_play();

	// ---- state ----
	int round = 0;
	std::vector<Champion> champs;
	std::vector<Camp> camps;
	std::vector<Group> groups;
	std::vector<Ward> wards;
	std::vector<AltarLock> locks;
	int next_lock_handle = 0;
	bool over = false;
	GameResult result;

	// ---- round structure ----
	void begin_round();					 // world update + camp turns
	void turn_order(std::vector<int>& out) const; // champion ids in execution order for this round
	void begin_turn(int c);				 // zero-timer resolution
	void end_turn(int c);				 // timer decrement, spawn recovery
	void end_round();					 // round limit / tiebreak

	// ---- actions (validated; return engine error codes) ----
	Err move(int c, Vec2 to, bool& ok);
	Err attack(int c, EntityKind kind, int handle);
	Err cast(int c, int slot, EntityKind kind, int handle, Vec2 dest, bool& ok);
	Err buy_item(int c, int item, int count);
	Err buy_consumable(int c, int type);
	Err sell(int c, int item);
	Err use_consumable(int c, int type, Vec2 dest, bool& ok);
	Err recall(int c);
	Err cancel_channel(int c);
	Err submit_gems(int c, Vec2 altar);
	Err place_ward(int c, Vec2 dest, bool& ok);
	Err set_priority(int c, int p);
	Err write_shared(int team, int offset, const std::uint8_t* data, int n);
	void resign(int team);

	// ---- queries used by the API ----
	bool can_shop(int c, bool consumables) const;
	bool can_sell(int c) const;
	std::uint32_t state_bits(int c) const;
	std::uint8_t restrictions(int c) const;
	bool is_stunned(int c) const;
	void champion_vision(int c, Bitboard& out) const; // own vision + ward + reveals
	int champion_at(Vec2 p) const;					   // living champion on tile, or -1
	int camp_at(Vec2 p) const;						   // living camp on tile, or -1
	int lock_at(Vec2 p, int team) const;
	bool tile_reserved_by_teleport(Vec2 p) const;
	int channel_time(int c) const;
	float ability_damage(int c, int slot) const;
	float ability_heal(int c, int slot) const;
	float ability_shield(int c, int slot) const;

	// Record respawning groups currently in the champion's vision.
	void update_group_memory(int c);
	// Capture progress resets the moment a reward region becomes empty or contested.
	void check_capture_regions();
	void on_position_changed(int c);

	// Recompute derived stats (max hp, strength, focus) from items and passives.
	void recompute_stats(Champion& ch);

private:
	std::shared_ptr<const Map> map_;
	std::vector<int> round_order_; // this round's champion execution order

	struct Hit
	{
		int src_champ = -1; // attacking champion or -1
		int src_camp = -1;	// attacking camp or -1
		float amount = 0;
		bool basic = false;
		bool splash = false;	   // Varg splash: does not trigger retaliation
		bool retaliation = false; // Ren's retaliation: does not trigger retaliation (RULE?)
	};
	void damage_champion(int target, const Hit& hit);
	void damage_camp(int camp, const Hit& hit);
	void kill_champion(int target, int killer);
	void kill_camp(int camp, int killer);
	void wake_group(int group);
	float apply_outgoing(const Champion& src, float amount, bool vs_camp) const;
	void stun_champion(int target, int duration);
	void stun_camp(int camp, int duration);
	void interrupt_channel(Champion& ch, bool by_damage);
	void grant_gold(Champion& ch, std::uint32_t amount, bool earned);
	void camp_turn(int camp);
	void process_captures();
	void process_respawns();
	void complete_channel(int c);
	void respawn_champion(int c);
	Err common_action_checks(const Champion& ch) const;
	bool landing_ok(const Champion& ch, Vec2 to, bool& hidden_block, bool known_only) const;
	void apply_basic_attack(int c, EntityKind kind, int handle);
	void check_win(int team);
	Vec2 spawn_slot(int team, int i) const;
	bool free_spawn_tile(int team, Vec2& out) const;
	bool on_spawn(const Champion& ch) const { return map_->spawn[ch.team].contains(ch.pos); }
};
} // namespace cbs
