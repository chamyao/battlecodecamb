// Oracle bot: dumps every engine constant and the full static map as "@@"-prefixed
// lines on stdout. Run with --rounds 1; parsed by oracle/tools/parse_dump.py.
#include <cambc.h>
#include <cstdio>
#include <cstring>
#include <vector>

using namespace cambc;
using namespace cambc::detail;

static void hexdump(const char* tag, int id, const void* p, std::size_t n)
{
	std::printf("@@%s %d ", tag, id);
	auto* b = static_cast<const unsigned char*>(p);
	for (std::size_t i = 0; i < n; ++i) std::printf("%02x", b[i]);
	std::printf("\n");
}

static void dump_constants()
{
	hexdump("settings", 0, &cached_game_settings, sizeof(game_settings));
	for (int t = 0; t < 16; ++t)
	{
		champion_design d{};
		if (sdk_champion_design(t, &d) == 0) hexdump("champion_design", t, &d, sizeof d);
	}
	for (int t = 0; t < 16; ++t)
	{
		camp_design d{};
		if (sdk_camp_design(t, &d) == 0) hexdump("camp_design", t, &d, sizeof d);
	}
	for (int t = 0; t < 96; ++t) // 84 items since engine 2.0.0
	{
		detail::item_info d{};
		if (sdk_item_info(t, &d) == 0) hexdump("item_info", t, &d, sizeof d);
	}
	for (int t = 0; t < 8; ++t)
	{
		detail::consumable_info d{};
		if (sdk_consumable_info(t, &d) == 0) hexdump("consumable_info", t, &d, sizeof d);
	}
	std::uint32_t sm{}, dm{};
	sdk_shared_memory_size(&sm);
	sdk_draft_memory_size(&dm);
	std::printf("@@memsize %u %u\n", sm, dm);
}

static void dump_map()
{
	metadata md{};
	sdk_bc_metadata(&md);
	hexdump("metadata", 0, &md, sizeof md);
	std::int32_t sym{};
	sdk_bc_map_symmetry(&sym);
	std::printf("@@symmetry %d\n", sym);
	for (int k = 0; k < 8; ++k)
	{
		bitboard b;
		if (sdk_bc_map_mask(k, b.ptr()) != 0) continue;
		auto lin = b.export_linear_buffer();
		hexdump("mask", k, lin.data(), lin.size());
	}
	for (int t = 0; t < 2; ++t)
	{
		aabb a{};
		if (sdk_spawn_region(t, &a) == 0) std::printf("@@spawn %d %d %d %d %d\n", t, a.min_x, a.min_y, a.max_x, a.max_y);
	}
	std::vector<std::uint32_t> words(4096);
	std::uint32_t count{};
	int rc = sdk_map_camp_layout(words.data(), words.size(), &count);
	std::printf("@@camp_layout_rc %d %u\n", rc, count);
	if (rc == 0) hexdump("camp_layout", 0, words.data(), count * 4);
	std::uint32_t ng{};
	if (sdk_map_num_camp_groups(&ng) == 0)
		for (std::uint32_t g = 0; g < ng; ++g)
		{
			camp_group_info gi{};
			std::int32_t resp{};
			sdk_map_camp_group(g, &gi);
			sdk_bc_camp_group_max_respawn(g, &resp);
			std::printf("@@group %u gems=%u gold=%u respawn=%d\n", g, gi.gems, gi.gold, resp);
		}
}

int main()
{
	if (is_draft())
	{
		std::printf("@@phase draft\n");
		dump_constants();
		dump_map();
		std::uint8_t rounds{};
		sdk_draft_num_rounds(&rounds);
		std::printf("@@draft_rounds %u\n", rounds);
		for (;;)
		{
			auto mine = draft::current_draft(team::ally);
			// Deterministic picks: lowest unpicked index, including Heart of Ruin probing at the end.
			for (int i = 11; i >= 0; --i)
			{
				bool used = false;
				for (auto c : mine) used |= static_cast<int>(c) == i;
				if (!used)
				{
					try { draft::pick(static_cast<champion_draft>(i)); std::printf("@@picked %d\n", i); break; }
					catch (const error& e) { std::printf("@@pick_error %d %d\n", i, static_cast<int>(e.code())); }
				}
			}
			end_turn();
		}
	}
	std::printf("@@phase play\n");
	if (sdk_my_champion() == 0)
	{
		dump_constants();
		dump_map();
	}
	std::uint32_t n{};
	sdk_num_allies(&n);
	std::vector<std::uint32_t> ids(16);
	std::uint32_t got{};
	sdk_allies(ids.data(), ids.size(), &got);
	for (std::uint32_t i = 0; i < got; ++i)
	{
		champion_info ci{};
		sdk_champion(ids[i], &ci);
		hexdump("ally", ids[i], &ci, sizeof ci);
	}
	sdk_enemies(ids.data(), ids.size(), &got);
	for (std::uint32_t i = 0; i < got; ++i)
	{
		champion_identity ci{};
		sdk_champion_identity(ids[i], &ci);
		hexdump("enemy", ids[i], &ci, sizeof ci);
	}
	std::printf("@@me %d team %d\n", sdk_my_champion(), sdk_my_team());
	for (;;) end_turn();
}
