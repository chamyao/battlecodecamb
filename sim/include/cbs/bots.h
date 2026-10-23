// Built-in reference policies.
#pragma once
#include <memory>
#include <string>
#include "cbs/runner.h"

namespace cbs
{
// Port of the official starter bot (bots/starter-cpp): random draft, farm the nearest camps,
// tribute carried gems, buy Power shards of a random stat, recall below 35% health.
std::unique_ptr<Player> make_starter_player(std::uint64_t seed = 1);
// Does nothing (yields every turn); useful as a punching bag and for measuring engine cost.
std::unique_ptr<Player> make_idle_player();
std::unique_ptr<Player> make_player(const std::string& name, std::uint64_t seed = 1);
} // namespace cbs
