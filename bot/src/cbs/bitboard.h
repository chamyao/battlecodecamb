// Fixed-capacity tile mask (up to 100x100) and the engine's geometry primitives.
// Row-major: bit x of row y. Every algorithm here is verified bit-for-bit against the
// engine's own host functions (oracle/fixtures/geom, docs/ENGINE_FINDINGS.md).
#pragma once
#include <bit>
#include <cstdint>
#include <cstring>
#include "core.h"

namespace cbs
{
// Rows that board-wide operations touch. Every tile set lies inside the map, so rows at or
// beyond the map height are always zero; a bot sets this to its map height once (inside
// wasm a full 100-row pass costs ~1.8k fuel). Per thread, so concurrent matches are safe.
inline thread_local int board_rows = kMaxDim;

struct Bitboard
{
	// Two words per row: bits 0..63 in w[y][0], 64..99 in w[y][1].
	std::uint64_t w[kMaxDim][2];
	// One row as a 128-bit vector (SSE2 natively, simd128 in a wasm bot).
	using Row = std::uint64_t __attribute__((vector_size(16)));
	static Row load(const std::uint64_t* p)
	{
		Row r;
		std::memcpy(&r, p, sizeof r);
		return r;
	}
	static void store(std::uint64_t* p, Row r) { std::memcpy(p, &r, sizeof r); }

	Bitboard() { clear(); }
	void clear() { std::memset(w, 0, sizeof w); }
	bool test(int x, int y) const { return (w[y][x >> 6] >> (x & 63)) & 1; }
	bool test(Vec2 p) const { return test(p.x, p.y); }
	void set(int x, int y) { w[y][x >> 6] |= std::uint64_t{ 1 } << (x & 63); }
	void set(Vec2 p) { set(p.x, p.y); }
	void reset(int x, int y) { w[y][x >> 6] &= ~(std::uint64_t{ 1 } << (x & 63)); }
	void reset(Vec2 p) { reset(p.x, p.y); }
	void assign(Vec2 p, bool v) { v ? set(p) : reset(p); }
	int count(int h) const
	{
		int n = 0;
		for (int y = 0; y < h; ++y) n += std::popcount(w[y][0]) + std::popcount(w[y][1]);
		return n;
	}
	bool any(int h) const
	{
		for (int y = 0; y < h; ++y)
			if (w[y][0] | w[y][1]) return true;
		return false;
	}
	Bitboard& operator|=(const Bitboard& o)
	{
		for (int y = 0, n = board_rows; y < n; ++y) store(w[y], load(w[y]) | load(o.w[y]));
		return *this;
	}
	Bitboard& operator&=(const Bitboard& o)
	{
		for (int y = 0, n = board_rows; y < n; ++y) store(w[y], load(w[y]) & load(o.w[y]));
		return *this;
	}
	// this &= ~o
	Bitboard& andnot(const Bitboard& o)
	{
		for (int y = 0, n = board_rows; y < n; ++y) store(w[y], load(w[y]) & ~load(o.w[y]));
		return *this;
	}
	// Calls f(x, y) for every set tile in rows [0, h), row-major.
	template <class F>
	void for_each(int h, F&& f) const
	{
		for (int y = 0; y < h; ++y)
			for (int k = 0; k < 2; ++k)
				for (std::uint64_t bits = w[y][k]; bits; bits &= bits - 1) f(64 * k + std::countr_zero(bits), y);
	}
	// First set tile in row-major order; false if empty.
	bool first(int h, Vec2& out) const
	{
		for (int y = 0; y < h; ++y)
			for (int k = 0; k < 2; ++k)
				if (w[y][k])
				{
					out = { 64 * k + std::countr_zero(w[y][k]), y };
					return true;
				}
		return false;
	}
	bool operator==(const Bitboard& o) const { return std::memcmp(w, o.w, sizeof w) == 0; }
};

// Linear (row-major, LSB-first) packing as exported by the SDK's export_linear_buffer.
void to_linear(const Bitboard& b, int W, int H, std::uint8_t* out);
void from_linear(Bitboard& b, int W, int H, const std::uint8_t* in);

// Symmetric shadowcasting from `origin` with Chebyshev radius `dist`.
// `blocking(x, y)` is queried only for in-map tiles; out-of-map tiles never block.
// Blocking tiles are never marked visible; the origin always is.
template <class Blocking, class Mark>
void shadowcast(int W, int H, Vec2 origin, int dist, Blocking&& blocking, Mark&& mark);

// Engine Bitboard::shadow_cast with `walls` as the blocking set.
void shadow_cast(const Bitboard& walls, int W, int H, Vec2 origin, int dist, Bitboard& out);
// Engine Bitboard::reachable_tiles: 8-neighbour BFS over non-walls up to `dist` steps.
void reachable(const Bitboard& walls, int W, int H, Vec2 origin, int dist, Bitboard& out);
// Engine DistanceField compute / compute_to. `dests` may be null. Returns the expansion count.
constexpr std::uint16_t kUnreachable = 0xFFFF;
int distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int W, int H, int max_distance,
				   std::uint16_t* dist /* W*H row-major */, Bitboard& visited);
void draw_circle(Bitboard& b, int W, int H, Vec2 c, float r);
void draw_chebyshev(Bitboard& b, int W, int H, Vec2 c, float r);

// ---- implementation of the templated shadowcaster ----
namespace detail
{
// floor(a / b) for b > 0.
constexpr long floor_div(long a, long b) { return a >= 0 ? a / b : -((-a + b - 1) / b); }
constexpr long ceil_div(long a, long b) { return -floor_div(-a, b); }

template <class Blocking, class Mark>
struct Caster
{
	int W, H, ox, oy, dist, q;
	Blocking& blocking;
	Mark& mark;
	void tr(int row, int col, int& x, int& y) const
	{
		switch (q)
		{
		case 0: x = ox + col, y = oy - row; break;
		case 1: x = ox + col, y = oy + row; break;
		case 2: x = ox + row, y = oy + col; break;
		default: x = ox - row, y = oy + col; break;
		}
	}
	bool wall(int row, int col) const
	{
		int x, y;
		tr(row, col, x, y);
		return x >= 0 && y >= 0 && x < W && y < H && blocking(x, y);
	}
	// Slopes are sn/sd and en/ed with positive denominators.
	void scan(int depth, long sn, long sd, long en, long ed)
	{
		if (depth > dist) return;
		// min_col = round_ties_up(depth*s) = floor(depth*sn/sd + 1/2); max_col = round_ties_down(depth*e) = ceil(depth*en/ed - 1/2)
		const long min_col = floor_div(2 * depth * sn + sd, 2 * sd);
		const long max_col = ceil_div(2 * depth * en - ed, 2 * ed);
		bool has_prev = false, prev_wall = false;
		for (long col = min_col; col <= max_col; ++col)
		{
			const bool w = wall(depth, static_cast<int>(col));
			// symmetric: depth*s <= col <= depth*e
			if (!w && col * sd >= depth * sn && col * ed <= depth * en)
			{
				int x, y;
				tr(depth, static_cast<int>(col), x, y);
				if (x >= 0 && y >= 0 && x < W && y < H) mark(x, y);
			}
			if (has_prev && prev_wall && !w)
			{
				sn = 2 * col - 1;
				sd = 2 * depth;
			}
			if (has_prev && !prev_wall && w) scan(depth + 1, sn, sd, 2 * col - 1, 2 * depth);
			has_prev = true;
			prev_wall = w;
		}
		if (has_prev && !prev_wall) scan(depth + 1, sn, sd, en, ed);
	}
};
} // namespace detail

template <class Blocking, class Mark>
void shadowcast(int W, int H, Vec2 origin, int dist, Blocking&& blocking, Mark&& mark)
{
	mark(origin.x, origin.y);
	for (int q = 0; q < 4; ++q)
	{
		detail::Caster<Blocking, Mark> c{ W, H, origin.x, origin.y, dist, q, blocking, mark };
		c.scan(1, -1, 1, 1, 1);
	}
}
} // namespace cbs
