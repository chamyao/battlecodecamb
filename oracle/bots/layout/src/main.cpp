// Oracle bot: prints where tile (x, y) lands in the engine's raw bitboard buffer
// (word index and bit) and in the raw distance-field buffer (u16 index).
#include <cambc.h>
#include <cstdio>
#include <vector>
using namespace cambc;
using namespace cambc::detail;
int main()
{
	if (is_draft() && sdk_my_team() == 0)
	{
		metadata md{};
		sdk_bc_metadata(&md);
		std::printf("@@meta %d %d cw=%u ch=%u stride=%u board=%u field=%u\n", md.width, md.height, md.chunked_width, md.chunked_height,
					md.chunk_stride, md.board_bytes, md.field_bytes);
		const int pts[][2] = { { 0, 0 }, { 1, 0 }, { 7, 0 }, { 8, 0 }, { 0, 1 }, { 0, 7 }, { 0, 8 }, { 9, 9 }, { 17, 3 }, { 3, 17 }, { md.width - 1, md.height - 1 } };
		for (auto& p : pts)
		{
			std::vector<std::uint64_t> b(md.board_bytes / 8 + 2, 0);
			sdk_Bitboard_Zero(b.data());
			sdk_Bitboard_Set(b.data(), p[0], p[1], 1);
			for (std::size_t i = 0; i < md.board_bytes / 8; ++i)
				if (b[i]) std::printf("@@bb %d %d word=%zu bit=%d\n", p[0], p[1], i, __builtin_ctzll(b[i]));
			std::vector<std::uint16_t> f(md.field_bytes / 2 + 2, 0);
			sdk_DistanceField_Set(f.data(), p[0], p[1], 7);
			for (std::size_t i = 0; i < md.field_bytes / 2; ++i)
				if (f[i] == 7) std::printf("@@df %d %d idx=%zu\n", p[0], p[1], i);
		}
	}
	if (is_draft() && sdk_my_team() == 0)
	{
		metadata md{};
		sdk_bc_metadata(&md);
		alignas(16) static std::uint64_t a[256], b[256], o[256];
		sdk_Bitboard_Zero(a);
		sdk_Bitboard_Zero(b);
		sdk_Bitboard_Set(a, 1, 1, 1);
		sdk_Bitboard_Set(b, 20, 3, 1);
		std::printf("@@alias union=%d", sdk_Bitboard_Union(a, b, a));
		std::int32_t v = 0;
		sdk_Bitboard_Test(a, 20, 3, &v);
		std::printf(" result_has_b=%d not=%d intersect=%d\n", v, sdk_Bitboard_Not(a, a), sdk_Bitboard_Intersect(a, b, a));
		sdk_Bitboard_Zero(a);
		const int pts[][2] = { { 9, 0 }, { 1, 1 }, { 0, 9 }, { 15, 2 }, { 2, 15 }, { 3, 0 } };
		for (auto& p : pts) sdk_Bitboard_Set(a, p[0], p[1], 1);
		struct P { std::int32_t x, y; } ps[16];
		std::uint32_t n = 0;
		std::printf("@@getset rc=%d", sdk_Bitboard_GetSetBits(a, ps, 16, &n));
		for (std::uint32_t i = 0; i < n; ++i) std::printf(" %d,%d", ps[i].x, ps[i].y);
		std::printf("\n");
	}
	for (int i = 0;; ++i)
	{
		if (is_draft()) try { draft::pick(static_cast<champion_draft>(i % 11)); } catch (...) {}
		end_turn();
	}
}
