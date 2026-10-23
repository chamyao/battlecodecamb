#include <algorithm>
#include "cbs/bitboard.h"

namespace cbs
{
namespace
{
inline int ctz128(unsigned __int128 v)
{
	const auto lo = static_cast<std::uint64_t>(v);
	return lo ? std::countr_zero(lo) : 64 + std::countr_zero(static_cast<std::uint64_t>(v >> 64));
}
inline int popcount128(unsigned __int128 v)
{
	return std::popcount(static_cast<std::uint64_t>(v)) + std::popcount(static_cast<std::uint64_t>(v >> 64));
}
} // namespace

void to_linear(const Bitboard& b, int W, int H, std::uint8_t* out)
{
	std::memset(out, 0, (static_cast<std::size_t>(W) * H + 7) / 8);
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
			if (b.test(x, y))
			{
				const int i = y * W + x;
				out[i >> 3] |= static_cast<std::uint8_t>(1u << (i & 7));
			}
}

void from_linear(Bitboard& b, int W, int H, const std::uint8_t* in)
{
	b.clear();
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
		{
			const int i = y * W + x;
			if (in[i >> 3] >> (i & 7) & 1) b.set(x, y);
		}
}

void shadow_cast(const Bitboard& walls, int W, int H, Vec2 origin, int dist, Bitboard& out)
{
	out.clear();
	shadowcast(W, H, origin, dist, [&](int x, int y) { return walls.test(x, y); }, [&](int x, int y) { out.set(x, y); });
}

void reachable(const Bitboard& walls, int W, int H, Vec2 origin, int dist, Bitboard& out)
{
	// Layered 8-neighbour dilation over whole rows (no queue: small stack, as in a wasm bot).
	out.clear();
	if (walls.test(origin)) return;
	using Row = unsigned __int128;
	const Row full = W >= 128 ? ~Row{ 0 } : (Row{ 1 } << W) - 1;
	auto row = [](const Bitboard& b, int y) { return static_cast<Row>(b.w[y][0]) | static_cast<Row>(b.w[y][1]) << 64; };
	Row seen[kMaxDim], front[kMaxDim], next[kMaxDim];
	for (int y = 0; y < H; ++y) seen[y] = front[y] = 0;
	seen[origin.y] = front[origin.y] = Row{ 1 } << origin.x;
	int y0 = origin.y, y1 = origin.y;
	for (int d = 0; d < dist; ++d)
	{
		const int lo = std::max(0, y0 - 1), hi = std::min(H - 1, y1 + 1);
		int n0 = H, n1 = -1;
		for (int y = lo; y <= hi; ++y)
		{
			Row h = 0;
			for (int yy = std::max(y0, y - 1); yy <= std::min(y1, y + 1); ++yy) h |= front[yy];
			h |= h << 1 | h >> 1;
			next[y] = h & full & ~row(walls, y) & ~seen[y];
			if (next[y]) n0 = std::min(n0, y), n1 = y;
		}
		if (n1 < 0) break;
		for (int y = lo; y <= hi; ++y)
		{
			front[y] = next[y];
			seen[y] |= next[y];
		}
		y0 = n0, y1 = n1;
	}
	for (int y = 0; y < H; ++y)
	{
		out.w[y][0] = static_cast<std::uint64_t>(seen[y]);
		out.w[y][1] = static_cast<std::uint64_t>(seen[y] >> 64);
	}
}

int distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int W, int H, int max_distance,
				   std::uint16_t* dist, Bitboard& visited, bool all_dests)
{
	// Layered BFS over whole rows (128-bit), matching the engine's queue BFS layer by layer.
	using Row = unsigned __int128;
	auto load = [](const Bitboard& b, int y) { return static_cast<Row>(b.w[y][0]) | static_cast<Row>(b.w[y][1]) << 64; };
	const Row full = W >= 128 ? ~Row{ 0 } : (Row{ 1 } << W) - 1;
	Row open[kMaxDim], seen[kMaxDim], front[kMaxDim], next[kMaxDim];
	visited.clear();
	for (int i = 0; i < W * H; ++i) dist[i] = kUnreachable;
	bool reached = false, any = false;
	int left = 0; // all_dests: dests not yet reached
	if (dests && all_dests)
		for (int y = 0; y < H; ++y) left += popcount128(load(*dests, y) & full);
	auto arrive = [&](Row layer, int y) {
		const Row hit = layer & load(*dests, y);
		if (!hit) return;
		if (!all_dests) reached = true;
		else if ((left -= popcount128(hit)) == 0) reached = true;
	};
	int y0 = H, y1 = -1; // rows spanned by the frontier
	for (int y = 0; y < H; ++y)
	{
		open[y] = ~load(walls, y) & full;
		front[y] = load(roots, y) & open[y];
		seen[y] = front[y];
		if (front[y])
		{
			any = true;
			y0 = std::min(y0, y), y1 = y;
			if (dests) arrive(front[y], y);
			for (Row b = front[y]; b; b &= b - 1) dist[y * W + ctz128(b)] = 0;
		}
	}
	int count = 0, depth = 0;
	while (any)
	{
		if (dests && reached) break;
		if (depth >= max_distance) break;
		any = false;
		const int lo = std::max(0, y0 - 1), hi = std::min(H - 1, y1 + 1);
		int n0 = H, n1 = -1;
		for (int y = lo; y <= hi; ++y)
		{
			Row h = 0;
			for (int yy = std::max(0, y - 1); yy <= std::min(H - 1, y + 1); ++yy)
				if (yy >= y0 && yy <= y1) h |= front[yy];
			h |= h << 1 | h >> 1;
			next[y] = h & open[y] & ~seen[y];
			if (next[y])
			{
				any = true;
				n0 = std::min(n0, y), n1 = y;
			}
		}
		const std::uint16_t d = static_cast<std::uint16_t>(depth + 1);
		for (int y = lo; y <= hi; ++y)
		{
			front[y] = next[y];
			if (!next[y]) continue;
			seen[y] |= next[y];
			if (dests) arrive(next[y], y);
			for (Row b = next[y]; b; b &= b - 1) dist[y * W + ctz128(b)] = d;
		}
		// Rows of the old frontier outside [lo, hi] cannot exist; clear stale rows outside the new span.
		y0 = n0, y1 = n1;
		++depth;
		++count;
	}
	for (int y = 0; y < H; ++y)
	{
		visited.w[y][0] = static_cast<std::uint64_t>(seen[y]);
		visited.w[y][1] = static_cast<std::uint64_t>(seen[y] >> 64);
	}
	return count;
}

void draw_circle(Bitboard& b, int W, int H, Vec2 c, float r)
{
	const double rr = static_cast<double>(r) * r;
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
		{
			const double dx = x - c.x, dy = y - c.y;
			if (dx * dx + dy * dy <= rr) b.set(x, y);
		}
}

void draw_chebyshev(Bitboard& b, int W, int H, Vec2 c, float r)
{
	// Integer distances: d <= r  <=>  d <= floor(r). One row mask over the clamped box.
	if (!(r >= 0)) return;
	const int k = r >= 2 * kMaxDim ? 2 * kMaxDim : static_cast<int>(r);
	const int x0 = std::max(0, c.x - k), x1 = std::min(W - 1, c.x + k);
	const int y0 = std::max(0, c.y - k), y1 = std::min(H - 1, c.y + k);
	if (x0 > x1 || y0 > y1) return;
	using Row = unsigned __int128;
	const Row mask = ((x1 - x0 + 1 >= 128 ? ~Row{ 0 } : (Row{ 1 } << (x1 - x0 + 1)) - 1)) << x0;
	for (int y = y0; y <= y1; ++y)
	{
		b.w[y][0] |= static_cast<std::uint64_t>(mask);
		b.w[y][1] |= static_cast<std::uint64_t>(mask >> 64);
	}
}
} // namespace cbs
