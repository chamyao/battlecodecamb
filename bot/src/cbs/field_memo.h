// The deploy bot's distance-field memo, shared by the bot (bot/src/bot_api.cpp, over host
// imports) and the simulator (sim/src/api.cpp, over its own BFS). The bot uses it to answer
// distance_field / nearest_by_walk cheaply; the simulator runs the identical decisions only to
// price those calls as the bot pays for them (a hit costs a scan, a miss a host search). The
// simulator's answers do not come from here.
//
// Host fields cost 16 * chunks + chunks per BFS layer (2.7k + 169 per layer on 100x100), and
// the host's ComputeTo runs until *every* dest is reached. Callers only need the field up to
// the nearest dest (the simulator's semantics), so requests are narrowed and memoised:
//
// - If the champion's tile is a dest, searching to it alone gives every value up to the
//   nearest dest (which is no farther).
// - A field depends only on (walls, roots, max_distance) up to its stopping layer L: a BFS
//   stopped at L holds the exact distance of every tile at most L away. A request with the
//   same roots is answered from a cached field when the walls are identical and its own
//   stopping layer S (its nearest dest) is at most L (or the cached search ran to completion);
//   or, for requests whose dests lie in the 5x5 box around the champion (move_towards,
//   dash_towards, nearest_by_walk's first step), when the walls differ only in tiles that
//   provably cannot change any box distance (box_unaffected) and S <= L.
//   Values beyond S read as unreachable, exactly as a search stopped at S leaves them.
// Typical hits: fields rooted at a fixed goal (a camp tile, the candidate set) on consecutive
// turns, since the champion's own tile is never a wall and units elsewhere rarely matter.
//
// Ops supplies the board type and the primitives:
//   using Board;                       // cbs::Bitboard of the build
//   int fidx(int x, int y) const;      // index into a field (engine chunked layout)
//   int delta(const Board& a, const Board& b, Vec2* out) const;
//                                      // tiles of a ^ b: total count, the first 64 in out
//   std::uint16_t compute(const Board& walls, const Board& roots, const Board* dests,
//                         std::uint16_t maxd, std::uint16_t* field, Board& visited) const;
//                                      // host DistanceField Compute / ComputeTo (all dests);
//                                      // returns the expansion count
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <memory>
#include "core.h"

namespace cbs::field_memo
{
constexpr int kFieldWords = 13 * 13 * 64; // u16 entries: 100x100 in 8x8 chunks
constexpr int kSlots = 4;
constexpr std::uint16_t kFar = 0xFFFF; // unreached (kUnreachable)

template <class Board>
struct Slot
{
	Board walls, roots;
	alignas(16) std::uint16_t field[kFieldWords];
	int depth = -1;		   // last layer expanded; -1 = empty slot
	bool complete = false; // the search ran out of tiles (every reachable tile is exact)
	int maxd = 0;
	std::uint64_t used = 0;
};

inline int cheb(int x, int y, Vec2 p) { return std::max(std::abs(x - p.x), std::abs(y - p.y)); }

template <class Ops>
struct Answer
{
	const Ops* ops;
	const std::uint16_t* f;
	const typename Ops::Board* walls; // the request's: never reached by a fresh search
	int limit;						  // values above this read as unreachable (-1: none)
	int count;						  // the stopping layer (expansion count of an equivalent fresh search)
	bool miss;						  // a host search ran
	int layers;						  // its expansion count (0 on a hit)
	std::uint16_t at(int x, int y) const
	{
		const std::uint16_t v = f[ops->fidx(x, y)];
		return (limit >= 0 && v > limit) || walls->test(x, y) ? kFar : v;
	}
};

template <class Ops>
class Memo
{
public:
	using Board = typename Ops::Board;
	explicit Memo(Ops ops) : ops_(ops) {}
	const Ops& ops() const { return ops_; }

	// `me` is the champion's tile (have_me false for the draft bot). The caller reads the
	// answer only at dests and at open tiles within Chebyshev `qr` of `me` (qr > 2: no
	// walls-changed reuse).
	Answer<Ops> query(const Board& walls, const Board& roots, const Board* dests, int max_distance, bool have_me, Vec2 me, int qr,
					  int W, int H)
	{
		if (!slots_) slots_.reset(new Slot<Board>[kSlots]);
		const auto maxd = static_cast<std::uint16_t>(std::clamp(max_distance, 0, 0xFFFF));
		// Nearest dest in a cached field (0x10000 if none within its depth); -1 if need_box and
		// some dest lies outside the box around the champion.
		auto nearest = [&](const Slot<Board>& sl, bool need_box) {
			int best = 0x10000;
			const int L = sl.depth;
			dests->for_each_unordered(H, [&](int x, int y) {
				if (best < 0) return;
				if (need_box && cheb(x, y, me) > qr)
				{
					best = -1;
					return;
				}
				const int v = sl.field[ops_.fidx(x, y)];
				if (v <= L && v < best && !walls.test(x, y)) best = v; // a wall dest is never reached
			});
			return best;
		};
		Answer<Ops> ans{ &ops_, nullptr, &walls, -1, 0, false, 0 };
		Slot<Board>*use = nullptr, *same_roots = nullptr;
		for (int i = 0; i < kSlots && !use; ++i)
		{
			Slot<Board>& sl = slots_[i];
			if (sl.depth < 0 || sl.maxd != maxd || !(sl.roots == roots)) continue;
			same_roots = &sl;
			if (sl.walls == walls)
			{
				if (!dests)
				{
					if (sl.complete) use = &sl;
					continue;
				}
				const int best = nearest(sl, false);
				if (best <= sl.depth) use = &sl, ans.limit = best;
				else if (sl.complete) use = &sl; // no dest reachable: a fresh search would run to completion
			}
			else if (dests && have_me && qr <= 2)
			{
				const int best = nearest(sl, true);
				if (best >= 0 && best <= sl.depth && box_unaffected(sl, walls, roots, me, best, qr, W, H)) use = &sl, ans.limit = best;
			}
		}
		if (use)
			ans.count = ans.limit >= 0 ? ans.limit : use->depth;
		else
		{
			// Replace the stale field with the same roots, else the least recently used one.
			use = same_roots;
			if (!use)
			{
				use = &slots_[0];
				for (int i = 1; i < kSlots; ++i)
					if (slots_[i].used < use->used) use = &slots_[i];
			}
			Board visited, me_only;
			const Board* sd = dests;
			if (dests && have_me && dests->test(me))
			{
				me_only.set(me);
				sd = &me_only;
			}
			const std::uint16_t count = ops_.compute(walls, roots, sd, maxd, use->field, visited);
			use->walls = walls;
			use->roots = roots;
			use->maxd = maxd;
			use->depth = count;
			// Stopped early only if a dest was reached (visited = every reached tile) or at maxd.
			bool reached = false;
			if (sd)
			{
				visited &= *sd;
				reached = visited.any(H);
			}
			use->complete = !reached && count < maxd;
			if (dests)
			{
				const int best = nearest(*use, false);
				if (best <= use->depth) ans.limit = best;
			}
			ans.count = ans.limit >= 0 ? ans.limit : count;
			ans.miss = true;
			ans.layers = count;
		}
		use->used = ++clock_;
		ans.f = use->field;
		return ans;
	}

private:
	// Can the walls of `sl` be replaced by `walls` for a request that stops at layer S <= L (its
	// nearest dest) and is read only on Q, the open tiles within Chebyshev `qr` of `me` (all its
	// dests are in Q)? Every q in Q must keep its cached distance D_q if D_q <= S, and stay
	// farther than S otherwise. (Tiles that are walls in the request read as unreachable, which
	// is exact: see Answer.) Let A be the tiles that became walls and R those that opened.
	//  - An old shortest path to q passes through a in A only if d(a) + cheb(a, q) <= D_q. If no
	//    a qualifies, an old shortest path survives, so q gets no farther. (Walls only removed
	//    paths, so tiles farther than S stay so.)
	//  - A new path that uses R enters its first r in R from a neighbour n reached without R, so
	//    it is at least lb(r) + cheb(r, q) long, lb(r) = min_n d(n) + 1 over old-open n. If that
	//    is at least D_q (or S + 1 for tiles farther than S), q gets no closer.
	// Unknown distances (beyond L) are taken as L + 1: a lower bound, so the test stays sound.
	bool box_unaffected(const Slot<Board>& sl, const Board& walls, const Board& roots, Vec2 me, int S, int qr, int W, int H)
	{
		Vec2 delta[64];
		const int n = ops_.delta(sl.walls, walls, delta);
		if (n > 64) return false;
		const int L = sl.depth;
		auto d = [&](int x, int y) {
			const int v = sl.field[ops_.fidx(x, y)];
			return v <= L ? v : L + 1;
		};
		// Q and the targets: D_q if D_q <= S, else S + 1 (filled on first need).
		struct Q
		{
			int x, y, t;
			bool known;
		};
		Q box[25];
		int nb = -1;
		auto fill_box = [&]() {
			nb = 0;
			for (int y = std::max(0, me.y - qr); y <= std::min(H - 1, me.y + qr); ++y)
				for (int x = std::max(0, me.x - qr); x <= std::min(W - 1, me.x + qr); ++x)
					if (!walls.test(x, y))
					{
						const int v = d(x, y);
						box[nb++] = { x, y, v <= S ? v : S + 1, v <= S };
					}
		};
		for (int i = 0; i < n; ++i)
		{
			const int x = delta[i].x, y = delta[i].y;
			if (roots.test(x, y)) return false;
			const int c = cheb(x, y, me);
			if (walls.test(x, y))
			{
				const int da = d(x, y);
				if (da > S || da + c - qr > S) continue;
				if (nb < 0) fill_box();
				for (int k = 0; k < nb; ++k)
					if (box[k].known && da + std::max(std::abs(x - box[k].x), std::abs(y - box[k].y)) <= box[k].t) return false;
			}
			else
			{
				int lb = 0x10000;
				for (int yy = std::max(0, y - 1); yy <= std::min(H - 1, y + 1); ++yy)
					for (int xx = std::max(0, x - 1); xx <= std::min(W - 1, x + 1); ++xx)
						if ((xx != x || yy != y) && !sl.walls.test(xx, yy)) lb = std::min(lb, d(xx, yy) + 1);
				if (lb + c - qr >= S + 1) continue;
				if (nb < 0) fill_box();
				for (int k = 0; k < nb; ++k)
					if (lb + std::max(std::abs(x - box[k].x), std::abs(y - box[k].y)) < box[k].t) return false;
			}
		}
		return true;
	}

	Ops ops_;
	std::unique_ptr<Slot<Board>[]> slots_;
	std::uint64_t clock_ = 0;
};
} // namespace cbs::field_memo
