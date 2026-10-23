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
#include "cbs/runner.h"

namespace interp
{
struct Program;

// Throws std::runtime_error on malformed input or unknown blocks.
std::shared_ptr<const Program> load_program(const std::string& text);
std::shared_ptr<const Program> load_program_file(const std::string& path);

std::unique_ptr<cbs::Player> make_policy_player(std::shared_ptr<const Program> program, std::uint64_t seed);

// Block keys the interpreter implements, e.g. "move_towards(Tile)".
std::vector<std::string> supported_blocks();
} // namespace interp
