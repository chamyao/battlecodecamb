#pragma once
#include <memory>
#include "cbs/map.h"

namespace cbs
{
// Static map data (terrain, spawns, camps, groups) read from the engine at startup.
std::shared_ptr<const Map> build_map_from_engine();
} // namespace cbs
