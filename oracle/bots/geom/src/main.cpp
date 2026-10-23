// Oracle bot: fuzzes the engine's geometry primitives and prints inputs/outputs as "@@" lines.
// Team A's draft bot does the work; everything else idles. Parsed by oracle/tools/geom_check.
#include <cambc.h>
#include <cstdio>
#include <cstdint>
#include <vector>

using namespace cambc;
using namespace cambc::detail;

static std::uint64_t rng_state = 0x9E3779B97F4A7C15ull;
static std::uint32_t rnd()
{
	rng_state ^= rng_state << 13;
	rng_state ^= rng_state >> 7;
	rng_state ^= rng_state << 17;
	return static_cast<std::uint32_t>(rng_state >> 11);
}

static void print_board(const char* tag, const bitboard& b)
{
	auto lin = b.export_linear_buffer();
	std::printf("@@%s ", tag);
	for (auto c : lin) std::printf("%02x", c);
	std::printf("\n");
}

static bitboard random_walls(int density_pct)
{
	bitboard b;
	const int W = map::width(), H = map::height();
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
			if (static_cast<int>(rnd() % 100) < density_pct) b.set({ x, y });
	return b;
}

int main()
{
	if (!is_draft())
	{
		if (sdk_my_champion() == 0)
		{
			const int W = map::width(), H = map::height();
			std::printf("@@dims %d %d\n", W, H);
	// 4. real-map hypothetical vision (champion design) and ward vision.
	for (int t = 0; t < 2000; ++t)
	{
		const vec2 o{ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) };
		bitboard v, wv;
		const int rc = sdk_hypothetical_vision(0, o.x, o.y, v.ptr());
		const int rw = sdk_ward_vision(o.x, o.y, wv.ptr());
		std::printf("@@vision %d %d %d %d\n", o.x, o.y, rc, rw);
		if (rc == 0) print_board("cv", v);
		if (rw == 0) print_board("wv", wv);
	}
			std::printf("@@vdone\n");
		}
		for (;;) end_turn();
	}
	if (sdk_my_team() != 0)
		for (;;) end_turn();
	const int W = map::width(), H = map::height();
	std::printf("@@dims %d %d\n", W, H);
	// 1. shadow_cast and reachable on random walls.
	for (int t = 0; t < 300; ++t)
	{
		const int density = static_cast<int>(rnd() % 45);
		auto walls = random_walls(density);
		const vec2 o{ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) };
		const int dist = static_cast<int>(rnd() % 13);
		print_board("walls", walls);
		std::printf("@@origin %d %d %d\n", o.x, o.y, dist);
		bitboard out;
		int rc = sdk_Bitboard_ShadowCast(walls.ptr(), o.x, o.y, out.ptr(), static_cast<std::uint16_t>(dist));
		std::printf("@@rc %d\n", rc);
		if (rc == 0) print_board("shadow", out);
		rc = sdk_Bitboard_ReachableMask(walls.ptr(), o.x, o.y, out.ptr(), static_cast<std::uint16_t>(dist));
		std::printf("@@rc %d\n", rc);
		if (rc == 0) print_board("reach", out);
	}
	// 2. distance fields.
	for (int t = 0; t < 100; ++t)
	{
		auto walls = random_walls(static_cast<int>(rnd() % 40));
		bitboard roots, dests, visited;
		const int nroots = 1 + static_cast<int>(rnd() % 3);
		for (int i = 0; i < nroots; ++i) roots.set({ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) });
		dests.set({ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) });
		const std::uint16_t maxd = (rnd() % 3 == 0) ? static_cast<std::uint16_t>(rnd() % 20) : distance_field::unreachable;
		const bool to = rnd() % 2;
		distance_field f;
		std::uint16_t count{};
		int rc = to ? sdk_DistanceField_ComputeToWithExpansionCount(walls.ptr(), roots.ptr(), dests.ptr(), visited.ptr(), f.ptr(), maxd, &count)
					: sdk_DistanceField_ComputeWithExpansionCount(walls.ptr(), roots.ptr(), visited.ptr(), f.ptr(), maxd, &count);
		std::printf("@@rc %d\n", rc);
		print_board("walls", walls);
		print_board("roots", roots);
		print_board("dests", dests);
		std::printf("@@field %d %u %u ", to ? 1 : 0, maxd, count);
		for (auto v : f.export_linear_buffer()) std::printf("%x,", v);
		std::printf("\n");
		print_board("visited", visited);
	}
	// 3. circles and chebyshev with fractional radii.
	for (int t = 0; t < 60; ++t)
	{
		const vec2 o{ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) };
		const float r = static_cast<float>(rnd() % 1200) / 100.0f;
		bitboard c, k;
		std::printf("@@rc %d %d\n", sdk_Bitboard_DrawCircle(c.ptr(), o.x, o.y, r), sdk_Bitboard_DrawChebyshev(k.ptr(), o.x, o.y, r));
		std::printf("@@radius %d %d %a\n", o.x, o.y, static_cast<double>(r));
		print_board("circle", c);
		print_board("cheb", k);
	}
	// 5. ComputeTo with several dests (some may be walls or unreachable): when does it stop?
	for (int t = 0; t < 60; ++t)
	{
		auto walls = random_walls(static_cast<int>(rnd() % 40));
		bitboard roots, dests, visited;
		roots.set({ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) });
		const int ndests = 2 + static_cast<int>(rnd() % 4);
		for (int i = 0; i < ndests; ++i) dests.set({ static_cast<int>(rnd() % W), static_cast<int>(rnd() % H) });
		const std::uint16_t maxd = (rnd() % 3 == 0) ? static_cast<std::uint16_t>(rnd() % 30) : distance_field::unreachable;
		distance_field f;
		std::uint16_t count{};
		int rc = sdk_DistanceField_ComputeToWithExpansionCount(walls.ptr(), roots.ptr(), dests.ptr(), visited.ptr(), f.ptr(), maxd, &count);
		std::printf("@@rc %d\n", rc);
		print_board("walls", walls);
		print_board("roots", roots);
		print_board("dests", dests);
		std::printf("@@fieldm %u %u ", maxd, count);
		for (auto v : f.export_linear_buffer()) std::printf("%x,", v);
		std::printf("\n");
		print_board("visited", visited);
	}
	// 6. GetSetBits with more set bits than the output holds: is n the total or the number written?
	{
		auto b = random_walls(30);
		vec2 pos[64];
		std::uint32_t n = 0;
		const int rc = sdk_Bitboard_GetSetBits(b.ptr(), pos, 64, &n);
		std::printf("@@setbits %d %u %d\n", rc, n, static_cast<int>(b.count()));
	}
	std::printf("@@done\n");
	draft::pick(champion_draft::ryth);
	for (;;)
	{
		end_turn();
		try { draft::pick(static_cast<champion_draft>(rnd() % 12)); } catch (...) {}
	}
}
