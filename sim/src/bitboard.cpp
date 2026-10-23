#include "cbs/bitboard.h"

namespace cbs
{
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
	out.clear();
	if (walls.test(origin)) return;
	Vec2 frontier[kMaxDim * kMaxDim];
	int n = 0;
	frontier[n++] = origin;
	out.set(origin);
	int begin = 0;
	for (int d = 0; d < dist && begin < n; ++d)
	{
		const int end = n;
		for (int i = begin; i < end; ++i)
		{
			const Vec2 p = frontier[i];
			for (int dy = -1; dy <= 1; ++dy)
				for (int dx = -1; dx <= 1; ++dx)
				{
					const int x = p.x + dx, y = p.y + dy;
					if (x < 0 || y < 0 || x >= W || y >= H || walls.test(x, y) || out.test(x, y)) continue;
					out.set(x, y);
					frontier[n++] = { x, y };
				}
		}
		begin = end;
	}
}

int distance_field(const Bitboard& walls, const Bitboard& roots, const Bitboard* dests, int W, int H, int max_distance,
				   std::uint16_t* dist, Bitboard& visited)
{
	visited.clear();
	for (int i = 0; i < W * H; ++i) dist[i] = kUnreachable;
	static thread_local Vec2 queue[kMaxDim * kMaxDim];
	int n = 0;
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
			if (roots.test(x, y) && !walls.test(x, y))
			{
				dist[y * W + x] = 0;
				visited.set(x, y);
				queue[n++] = { x, y };
			}
	bool reached = false;
	auto check_dest = [&](int x, int y) {
		if (dests && dests->test(x, y)) reached = true;
	};
	for (int i = 0; i < n; ++i) check_dest(queue[i].x, queue[i].y);
	int count = 0, begin = 0, depth = 0;
	while (begin < n)
	{
		if (dests && reached) break;
		if (depth >= max_distance) break;
		const int end = n;
		for (int i = begin; i < end; ++i)
		{
			const Vec2 p = queue[i];
			for (int dy = -1; dy <= 1; ++dy)
				for (int dx = -1; dx <= 1; ++dx)
				{
					const int x = p.x + dx, y = p.y + dy;
					if (x < 0 || y < 0 || x >= W || y >= H || walls.test(x, y) || dist[y * W + x] != kUnreachable) continue;
					dist[y * W + x] = static_cast<std::uint16_t>(depth + 1);
					visited.set(x, y);
					queue[n++] = { x, y };
					check_dest(x, y);
				}
		}
		begin = end;
		++depth;
		++count;
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
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
			if (chebyshev({ x, y }, c) <= r) b.set(x, y);
}
} // namespace cbs
