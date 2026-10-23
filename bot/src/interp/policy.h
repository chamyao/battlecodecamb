// Runs grammar policies (policygen) inside the simulator.
//
// A policy is loaded from the prefix format written by policygen/compile.py and
// executed by one interpreter per bot instance: each turn it walks the steps from
// the top, evaluating blocks through cbs::Api (which prices every engine call) and
// charging its own work with api.compute(). `keep` variables persist across turns.
#pragma once
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include "../cbs/runner.h"

namespace interp
{
struct Program;
struct Step;

// Throws std::runtime_error on malformed input or unknown blocks.
std::shared_ptr<const Program> load_program(const std::string& text);
std::shared_ptr<const Program> load_program_file(const std::string& path);
// Pre-encoded form (see the code table in policy.cpp; bot/encode_policy.py writes it): avoids
// all string work, for bots.
std::shared_ptr<const Program> load_program_codes(const std::uint16_t* code, std::size_t n, const double* nums, std::size_t nnums,
												  const char* const* bytes_hex, std::size_t nbytes);

// Constant data from bot/encode_policy.py (the same program load_program_codes would build):
// no parsing at all. The arrays must outlive the program.
std::shared_ptr<const Program> load_program_static(const Step* steps, std::size_t n);
// Structural equality (ops, variables, constants, nesting), for checking a static program.
bool same_program(const Program& a, const Program& b);

// bot_seeds: seed each instance as the deploy bot does (bot/src/main.cpp) instead of from `seed`,
// so a simulated game reproduces the bot's random choices in the same cambc game.
std::unique_ptr<cbs::Player> make_policy_player(std::shared_ptr<const Program> program, std::uint64_t seed, bool bot_seeds = false);

// Blocks charged so far in this process (simulator diagnostics; not thread-safe).
struct BlockCharge
{
	std::string key;
	long long count, fuel;
};
std::vector<BlockCharge> charge_stats();

// Diagnostics: print each champion's own state at the start of its turn ("@@ST" lines, through
// the Api, so the simulator and a trace build of the bot print the same thing). Off by default.
inline bool state_trace = false;
inline int state_trace_r0 = 0, state_trace_r1 = 1 << 30;
inline int state_trace_tiles = -1; // round whose vision tiles are listed // rounds that also dump the tile sets pathing saw

// Block keys the interpreter implements, e.g. "move_towards(Tile)".
std::vector<std::string> supported_blocks();
} // namespace interp
