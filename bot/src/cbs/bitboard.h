// Bot-only replacement for sim/include/cbs/bitboard.h (bot/sync.sh installs it as
// bot/src/cbs/bitboard.h). Same interface as the simulator's cbs::Bitboard, but the bits live
// in the engine's chunked layout (one 64-bit word per 8x8 chunk: word (y/8)*stride + x/8,
// bit (y%8)*8 + x%8) and board-wide work goes through the host imports, which cost about
// 6 + chunks fuel each, against ~1 fuel per byte (1600 per board) for the same work in wasm
// (docs/FUEL.md). for_each and first are row-major, as in the simulator; for_each_unordered
// is the cheap host order.
#pragma once
#include <cambc.h>
#include <bit>
#include <cstdint>
#include <cstring>
#include "core.h"

namespace cbs
{
// Unused in the bot (kept so shared headers compile).
inline int board_rows = kMaxDim;

namespace hostbb
{
inline cambc::detail::metadata md{}; // set by init() before any Bitboard is built
inline int stride = 0, words = 0;
inline void init()
{
	cambc::detail::sdk_bc_metadata(&md);
	stride = static_cast<int>(md.chunk_stride);
	words = static_cast<int>(md.board_bytes / 8);
}
constexpr int kWords = 256; // >= board_bytes / 8 on every map up to 100x100
struct Pos
{
	std::int32_t x, y;
};
// GetSetBits output, one buffer per nesting level of for_each (callbacks may iterate too).
constexpr int kDepth = 3;
inline Pos pos_buf[kDepth][kMaxDim * kMaxDim];
inline int depth = 0;
} // namespace hostbb

struct Bitboard
{
	alignas(16) std::uint64_t w[hostbb::kWords];

	Bitboard() { cambc::detail::sdk_Bitboard_Zero(w); }
	Bitboard(const Bitboard& o) { cambc::detail::sdk_Bitboard_Union(o.w, o.w, w); }
	Bitboard& operator=(const Bitboard& o)
	{
		if (this != &o) cambc::detail::sdk_Bitboard_Union(o.w, o.w, w);
		return *this;
	}
	void clear() { cambc::detail::sdk_Bitboard_Zero(w); }

	static int word(int x, int y) { return (y >> 3) * hostbb::stride + (x >> 3); }
	static int bit(int x, int y) { return (y & 7) * 8 + (x & 7); }
	bool test(int x, int y) const { return (w[word(x, y)] >> bit(x, y)) & 1; }
	bool test(Vec2 p) const { return test(p.x, p.y); }
	void set(int x, int y) { w[word(x, y)] |= std::uint64_t{ 1 } << bit(x, y); }
	void set(Vec2 p) { set(p.x, p.y); }
	void reset(int x, int y) { w[word(x, y)] &= ~(std::uint64_t{ 1 } << bit(x, y)); }
	void reset(Vec2 p) { reset(p.x, p.y); }
	void assign(Vec2 p, bool v) { v ? set(p) : reset(p); }

	int count(int) const
	{
		std::uint32_t n = 0;
		cambc::detail::sdk_Bitboard_NumSetBits(w, &n);
		return static_cast<int>(n);
	}
	bool any(int) const
	{
		std::int32_t z = 1;
		cambc::detail::sdk_Bitboard_IsZero(w, &z);
		return !z;
	}
	Bitboard& operator|=(const Bitboard& o)
	{
		cambc::detail::sdk_Bitboard_Union(w, o.w, w);
		return *this;
	}
	Bitboard& operator&=(const Bitboard& o)
	{
		cambc::detail::sdk_Bitboard_Intersect(w, o.w, w);
		return *this;
	}
	// this &= ~o, as this ^ (this & o)
	Bitboard& andnot(const Bitboard& o)
	{
		alignas(16) static std::uint64_t t[hostbb::kWords];
		cambc::detail::sdk_Bitboard_Intersect(w, o.w, t);
		cambc::detail::sdk_Bitboard_Xor(w, t, w);
		return *this;
	}
	// Calls f(x, y) for every set tile in the host's order (chunk by chunk; row-major inside a
	// chunk). Cheapest iteration: 11 + chunks + n fuel for the host call.
	template <class F>
	void for_each_unordered(int, F&& f) const
	{
		std::uint32_t n = 0;
		hostbb::Pos* buf = hostbb::pos_buf[hostbb::depth];
		cambc::detail::sdk_Bitboard_GetSetBits(w, buf, kMaxDim * kMaxDim, &n);
		++hostbb::depth;
		for (std::uint32_t i = 0; i < n; ++i) f(buf[i].x, buf[i].y);
		--hostbb::depth;
	}
	// Calls f(x, y) for every set tile, row-major (as the simulator's Bitboard does).
	template <class F>
	void for_each(int, F&& f) const
	{
		std::uint32_t n = 0;
		hostbb::Pos* buf = hostbb::pos_buf[hostbb::depth];
		cambc::detail::sdk_Bitboard_GetSetBits(w, buf, kMaxDim * kMaxDim, &n);
		// Host order is (chunk row, chunk column, y, x): sort each chunk row's run by (y, x).
		for (std::uint32_t i = 1; i < n; ++i)
		{
			const hostbb::Pos p = buf[i];
			std::uint32_t j = i;
			for (; j > 0 && (buf[j - 1].y > p.y || (buf[j - 1].y == p.y && buf[j - 1].x > p.x)); --j) buf[j] = buf[j - 1];
			buf[j] = p;
		}
		++hostbb::depth;
		for (std::uint32_t i = 0; i < n; ++i) f(buf[i].x, buf[i].y);
		--hostbb::depth;
	}
	// First set tile in row-major order; false if empty.
	bool first(int, Vec2& out) const
	{
		const int ch = static_cast<int>(hostbb::md.chunked_height), cw = static_cast<int>(hostbb::md.chunked_width);
		for (int cy = 0; cy < ch; ++cy)
		{
			const std::uint64_t* row = w + cy * hostbb::stride;
			// lowest sub-row (y % 8) with a bit in any chunk of this chunk row, then lowest x on it
			int best_y = 8, best_x = 0;
			for (int cx = 0; cx < cw; ++cx)
				if (const std::uint64_t v = row[cx])
				{
					const int b = std::countr_zero(v), y = b >> 3;
					if (y < best_y) best_y = y, best_x = cx * 8 + (b & 7);
				}
			if (best_y < 8)
			{
				out = { best_x, cy * 8 + best_y };
				return true;
			}
		}
		return false;
	}
	bool operator==(const Bitboard& o) const
	{
		std::int32_t eq = 0;
		cambc::detail::sdk_Bitboard_IsEqual(w, o.w, &eq);
		return eq != 0;
	}
};

// Engine geometry (the simulator's versions are verified bit-for-bit against these).
inline void draw_circle(Bitboard& b, int, int, Vec2 c, float r) { cambc::detail::sdk_Bitboard_DrawCircle(b.w, c.x, c.y, r); }
inline void draw_chebyshev(Bitboard& b, int, int, Vec2 c, float r) { cambc::detail::sdk_Bitboard_DrawChebyshev(b.w, c.x, c.y, r); }
constexpr std::uint16_t kUnreachable = 0xFFFF;
} // namespace cbs
