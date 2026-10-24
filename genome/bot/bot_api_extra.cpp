// Engine-backed cbs::Api calls the genome runtime uses that the policy bot (bot/src/bot_api.cpp) does
// not implement. Same style: one raw import each, errors passed through.
#include <cambc.h>
#include "cbs/api.h"

namespace cbs
{
using namespace cambc::detail;
static Err E2(std::int32_t rc) { return static_cast<Err>(rc); }
Err Api::cancel_channel() { return E2(sdk_cancel_channel()); }
Err Api::champion_can_shop(std::uint32_t h, bool consumables, std::int32_t* out) { return E2(sdk_champion_can_shop(h, consumables ? 1 : 0, out)); }
Err Api::champion_items(std::uint32_t h, std::uint32_t* out) { return E2(sdk_champion_items(h, out)); }
Err Api::champion_wards(std::uint32_t h, WardResources* out)
{
	ward_resources w{};
	const std::int32_t rc = sdk_champion_wards(h, &w);
	out->charges = w.charges;
	out->cooldown = w.cooldown;
	return E2(rc);
}
Err Api::is_visible(Vec2 p, std::int32_t* out) { return E2(sdk_is_visible(p.x, p.y, out)); }
} // namespace cbs
