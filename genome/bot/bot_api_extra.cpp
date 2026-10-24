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
// raw SDK reads (genome SDK coverage)
Err Api::champion_channel_time(std::uint32_t h, std::int32_t* out) { return E2(sdk_champion_channel_time(h, out)); }
Err Api::champion_can_sell(std::uint32_t h, std::int32_t* out) { return E2(sdk_champion_can_sell(h, out)); }
Err Api::champion_ward_positions(std::uint32_t h, Vec2* out, std::uint32_t cap, std::uint32_t* count)
{
	static_assert(sizeof(Vec2) == sizeof(cambc::detail::position));
	return E2(sdk_champion_ward_positions(h, reinterpret_cast<cambc::detail::position*>(out), cap, count));
}
Err Api::hypothetical_vision(std::int32_t type, Vec2 p, Bitboard& out)
{
	const Err e = E2(sdk_hypothetical_vision(type, p.x, p.y, out.w));
	if (e != Err::success) out.clear();
	return e;
}
Err Api::ward_vision(Vec2 p, Bitboard& out)
{
	const Err e = E2(sdk_ward_vision(p.x, p.y, out.w));
	if (e != Err::success) out.clear();
	return e;
}
Err Api::camp_group_cooldown(std::uint32_t g, std::int32_t* out) { return E2(sdk_camp_group_cooldown(g, out)); }
Err Api::camp_buffs(std::uint32_t h, CampBuffRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	static_assert(sizeof(CampBuffRecord) == sizeof(camp_buff_data));
	return E2(sdk_camp_buffs(h, reinterpret_cast<camp_buff_data*>(out), cap, count));
}
Err Api::wards(WardRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	static_assert(sizeof(WardRecord) == sizeof(ward_info));
	return E2(sdk_wards(reinterpret_cast<ward_info*>(out), cap, count));
}
Err Api::teleports(TeleportRecord* out, std::uint32_t cap, std::uint32_t* count)
{
	static_assert(sizeof(TeleportRecord) == sizeof(teleport_info));
	return E2(sdk_teleports(reinterpret_cast<teleport_info*>(out), cap, count));
}
} // namespace cbs
