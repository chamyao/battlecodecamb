// Self-test of the bot's host-backed cbs::Bitboard (bot/bitboard_host.h) against a plain
// bool-array reference, on the real engine. Prints @@BB lines; run via bot/tools/bbtest.sh.
#include <cambc.h>
#include <cstdio>
#include <vector>
#include "cbs/bitboard.h"
using namespace cbs;
static std::uint64_t s = 88172645463325252ull;
static int rnd(int n) { s ^= s << 13; s ^= s >> 7; s ^= s << 17; return (int)(s % n); }
int W, H, fails = 0;
struct Ref { std::vector<char> b; Ref() : b(W * H, 0) {} };
static void fill(Bitboard& bb, Ref& r, int k)
{
	for (int i = 0; i < k; ++i) { int x = rnd(W), y = rnd(H); bb.set(x, y); r.b[y * W + x] = 1; }
}
static bool same(const Bitboard& bb, const Ref& r, const char* what)
{
	std::vector<std::pair<int, int>> got, want;
	bb.for_each(H, [&](int x, int y) { got.push_back({ x, y }); });
	for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) if (r.b[y * W + x]) want.push_back({ x, y });
	bool ok = got == want;
	for (int y = 0; y < H && ok; ++y) for (int x = 0; x < W; ++x) ok &= bb.test(x, y) == (bool)r.b[y * W + x];
	ok &= bb.count(H) == (int)want.size();
	ok &= bb.any(H) == !want.empty();
	Vec2 f{ -1, -1 };
	bool hf = bb.first(H, f);
	ok &= hf == !want.empty() && (!hf || (f.x == want[0].first && f.y == want[0].second));
	if (!ok)
	{
		++fails;
		std::printf("@@BB FAIL %s n=%zu got=%zu count=%d any=%d first=%d,%d want0=%d,%d\n", what, want.size(), got.size(), bb.count(H), bb.any(H), f.x, f.y,
					want.empty() ? -1 : want[0].first, want.empty() ? -1 : want[0].second);
		for (std::size_t i = 0; i < got.size() && i < 12; ++i) std::printf("@@BB   %zu got %d,%d want %d,%d\n", i, got[i].first, got[i].second, want[i].first, want[i].second);
		for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) if (bb.test(x, y) != (bool)r.b[y * W + x]) std::printf("@@BB   test mismatch %d,%d\n", x, y);
	}
	return ok;
}
int main()
{
	hostbb::init();
	W = hostbb::md.width, H = hostbb::md.height;
	if (!cambc::is_draft()) for (;;) cambc::end_turn();
	for (int it = 0; it < 30; ++it)
	{
		int k = it < 10 ? rnd(4) : rnd(W * H / 2);
		Bitboard a, b; Ref ra, rb;
		fill(a, ra, k); fill(b, rb, rnd(W * H / 3));
		same(a, ra, "fill");
		Bitboard c = a; same(c, ra, "copy");
		Bitboard d; d = b; same(d, rb, "assign");
		Bitboard u = a; u |= b; Ref ru; for (int i = 0; i < W * H; ++i) ru.b[i] = ra.b[i] | rb.b[i]; same(u, ru, "or");
		Bitboard n = a; n &= b; Ref rn; for (int i = 0; i < W * H; ++i) rn.b[i] = ra.b[i] & rb.b[i]; same(n, rn, "and");
		Bitboard m = a; m.andnot(b); Ref rm; for (int i = 0; i < W * H; ++i) rm.b[i] = ra.b[i] & !rb.b[i]; same(m, rm, "andnot");
		int x = rnd(W), y = rnd(H); m.reset(x, y); rm.b[y * W + x] = 0; same(m, rm, "reset");
		if (!(c == a) || (k > 0 && a == b && !(ra.b == rb.b))) { ++fails; std::printf("@@BB FAIL eq\n"); }
		Bitboard e; e.clear(); same(e, Ref(), "clear");
		// ring: chebyshev squares, compare with direct definition
		Bitboard r; Ref rr; int cx = rnd(W), cy = rnd(H), rad = rnd(4);
		draw_chebyshev(r, W, H, { cx, cy }, (float)rad);
		for (int yy = 0; yy < H; ++yy) for (int xx = 0; xx < W; ++xx) rr.b[yy * W + xx] = std::abs(xx - cx) <= rad && std::abs(yy - cy) <= rad;
		same(r, rr, "chebyshev");
	}
	// nested for_each
	Bitboard a, b; Ref ra, rb; fill(a, ra, 50); fill(b, rb, 70);
	long acc = 0, want = 0;
	a.for_each(H, [&](int x, int y) { b.for_each(H, [&](int u, int v) { acc += x * u + y * v; }); });
	for (int i = 0; i < W * H; ++i) for (int j = 0; j < W * H; ++j) if (ra.b[i] && rb.b[j]) want += (i % W) * (j % W) + (i / W) * (j / W);
	if (acc != want) { ++fails; std::printf("@@BB FAIL nested\n"); }
	{
		// distance-field raw layout: chunk index uses chunked_width (as bot_api.cpp assumes)
		static std::uint16_t field[13 * 14 * 64];
		Bitboard walls, roots, vis;
		Ref rw; fill(walls, rw, W * H / 5);
		int rx = rnd(W), ry = rnd(H); walls.reset(rx, ry); roots.set(rx, ry);
		std::uint16_t cnt = 0;
		cambc::detail::sdk_DistanceField_ComputeWithExpansionCount(walls.w, roots.w, vis.w, field, 0xFFFF, &cnt);
		int bad = 0;
		for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x)
		{
			std::uint16_t v = 0;
			cambc::detail::sdk_DistanceField_Get(field, x, y, &v);
			std::uint16_t mine = field[((y >> 3) * (int)hostbb::md.chunked_width + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7)];
			bad += v != mine;
		}
		if (bad) { ++fails; std::printf("@@BB FAIL field layout %d tiles\n", bad); }
		std::printf("@@BB field_bytes=%u\n", hostbb::md.field_bytes);
	}
	{
		Bitboard walls, out, roots, vis, scratch1, scratch2;
		cambc::detail::sdk_bc_map_mask(0, walls.w);
		int ox = 0, oy = 0;
		for (int y = H / 2; y < H; ++y) { for (int x = W / 2; x < W; ++x) if (!walls.test(x, y)) { ox = x, oy = y; break; } if (ox) break; }
		for (int k : { 0, 1, 2, 4, 8, 16, 32, 64, 128, 200, 400 })
		{
			auto f0 = cambc::detail::sdk_fuel_remaining();
			cambc::detail::sdk_Bitboard_ReachableMask(walls.w, ox, oy, out.w, k);
			auto f1 = cambc::detail::sdk_fuel_remaining();
			cambc::detail::sdk_Bitboard_ReachableMaskWithScratch(walls.w, ox, oy, out.w, k, scratch1.w, scratch2.w);
			auto f2 = cambc::detail::sdk_fuel_remaining();
			static std::uint16_t field[13 * 14 * 64];
			std::uint16_t cnt = 0;
			roots.clear(); roots.set(ox, oy);
			auto f3 = cambc::detail::sdk_fuel_remaining();
			cambc::detail::sdk_DistanceField_ComputeWithExpansionCount(walls.w, roots.w, vis.w, field, k, &cnt);
			auto f4 = cambc::detail::sdk_fuel_remaining();
			std::printf("@@BB reach k=%d fuel=%lld scratch=%lld n=%d | df fuel=%lld exp=%u\n", k, (long long)(f0 - f1), (long long)(f1 - f2), out.count(H), (long long)(f3 - f4), cnt);
		}
	}
	{
		Bitboard b; Ref r; fill(b, r, 92);
		static hostbb::Pos buf[10000];
		for (int cap : { 100, 1000, 10000 })
		{
			std::uint32_t n = 0;
			auto f0 = cambc::detail::sdk_fuel_remaining();
			cambc::detail::sdk_Bitboard_GetSetBits(b.w, buf, cap, &n);
			auto f1 = cambc::detail::sdk_fuel_remaining();
			std::printf("@@BB getsetbits cap=%d n=%u fuel=%lld\n", cap, n, (long long)(f0 - f1));
		}
		long acc = 0;
		auto f0 = cambc::detail::sdk_fuel_remaining();
		b.for_each_unordered(H, [&](int x, int y) { acc += x + y; });
		auto f1 = cambc::detail::sdk_fuel_remaining();
		b.for_each(H, [&](int x, int y) { acc += x + y; });
		auto f2 = cambc::detail::sdk_fuel_remaining();
		Vec2 p; b.first(H, p);
		auto f3 = cambc::detail::sdk_fuel_remaining();
		std::printf("@@BB for_each_unordered=%lld for_each=%lld first=%lld acc=%ld\n", (long long)(f0 - f1), (long long)(f1 - f2), (long long)(f2 - f3), acc);
	}
	for (int it = 0; it < 5; ++it)
	{
		// ComputeTo: visited == tiles with a distance, and the BFS stops at the first layer touching a dest
		static std::uint16_t field[13 * 14 * 64];
		Bitboard walls, roots, dests, vis;
		Ref rw; fill(walls, rw, W * H / 6);
		int rx = rnd(W), ry = rnd(H); walls.reset(rx, ry); roots.set(rx, ry);
		Ref rd; fill(dests, rd, 3);
		vis.set(0, 0); vis.set(W - 1, H - 1); // stale bits must be overwritten
		std::uint16_t cnt = 0;
		cambc::detail::sdk_DistanceField_ComputeToWithExpansionCount(walls.w, roots.w, dests.w, vis.w, field, 0xFFFF, &cnt);
		int bad = 0, mind = 65535, maxv = -1;
		for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x)
		{
			std::uint16_t v = field[((y >> 3) * (int)hostbb::md.chunked_width + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7)];
			bad += vis.test(x, y) != (v != 65535);
			if (v != 65535 && v > maxv) maxv = v;
			if (dests.test(x, y) && v < mind) mind = v;
		}
		std::printf("@@BB computeTo cnt=%u maxv=%d mindest=%d visited_mismatch=%d\n", cnt, maxv, mind, bad);
		if (bad) ++fails;
	}
	{
		// Does ComputeTo overwrite every entry of the output field, or only the tiles it reaches?
		static std::uint16_t field[13 * 14 * 64];
		for (auto& v : field) v = 5;
		Bitboard walls, roots, dests, vis;
		roots.set(W / 2, H / 2);
		dests.set(W / 2 + 3, H / 2);
		std::uint16_t cnt = 0;
		cambc::detail::sdk_DistanceField_ComputeToWithExpansionCount(walls.w, roots.w, dests.w, vis.w, field, 0xFFFF, &cnt);
		int stale = 0, unreached = 0;
		for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x)
		{
			std::uint16_t v = field[((y >> 3) * (int)hostbb::md.chunked_width + (x >> 3)) * 64 + (y & 7) * 8 + (x & 7)];
			if (!vis.test(x, y)) { stale += v == 5; unreached += v == 65535; }
		}
		std::printf("@@BB stale-check cnt=%u unvisited: stale=%d unreachable=%d\n", cnt, stale, unreached);
	}
	std::printf("@@BB done W=%d H=%d stride=%d words=%d fails=%d\n", W, H, hostbb::stride, hostbb::words, fails);
	for (int i = 0;; ++i) { try { cambc::draft::pick(static_cast<cambc::champion_draft>(i % 11)); } catch (...) {} cambc::end_turn(); }
}
