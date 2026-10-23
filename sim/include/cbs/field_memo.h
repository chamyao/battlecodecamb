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
//   int delta(const Board& a, const Board& b, Vec2* out, int cap) const;
//                                      // tiles of a ^ b: total count, the first cap in out
//   std::uint16_t compute(const Board& walls, const Board& roots, const Board* dests,
//                         std::uint16_t maxd, std::uint16_t* field, Board& visited) const;
//                                      // host DistanceField Compute / ComputeTo (all dests);
//                                      // returns the expansion count
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <memory>
#include "cbs/core.h"

namespace cbs::field_memo
{
constexpr int kFieldWords = 13 * 13 * 64; // u16 entries: 100x100 in 8x8 chunks
constexpr int kSlots = 4;
// Many changed tiles rarely pass box_unaffected; each removed one costs ~300 fuel to examine.
constexpr int kMaxDelta = 24;
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
	int path;						  // 0 miss, 1 same walls, 2 walls changed outside the box
	int depth;						  // depth / complete of the slot used, before this call
	int complete;
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
	bool reference = false; // never reuse or narrow: a fresh search each time (bot BOT_REFERENCE)

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
		Answer<Ops> ans{ &ops_, nullptr, &walls, -1, 0, false, 0, 0, -1, -1 };
		Slot<Board>*use = nullptr, *same_roots = nullptr;
		for (int i = 0; i < kSlots && !use; ++i)
		{
			Slot<Board>& sl = slots_[i];
			if (reference) continue;
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
		{
			ans.count = ans.limit >= 0 ? ans.limit : use->depth;
			ans.path = use->walls == walls ? 1 : 2;
			ans.depth = use->depth;
			ans.complete = use->complete;
		}
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
			// Scratch boards: compute writes all of visited_; me_only_ is kept empty between calls.
			const Board* sd = dests;
			const bool to_me = !reference && dests && have_me && dests->test(me);
			if (to_me)
			{
				me_only_.set(me);
				sd = &me_only_;
			}
			const std::uint16_t count = ops_.compute(walls, roots, sd, maxd, use->field, visited_);
			use->walls = walls;
			use->roots = roots;
			use->maxd = maxd;
			use->depth = count;
			// Stopped early only if a dest was reached (visited = every reached tile) or at maxd.
			bool reached = false;
			if (to_me)
			{
				reached = visited_.test(me);
				me_only_.reset(me);
			}
			else if (sd)
			{
				visited_ &= *sd;
				reached = visited_.any(H);
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
		Vec2 delta[kMaxDelta];
		const int n = ops_.delta(sl.walls, walls, delta, kMaxDelta);
		if (n > kMaxDelta) return false;
		const int L = sl.depth;
		auto d = [&](int x, int y) {
			const int v = sl.field[ops_.fidx(x, y)];
			return v <= L ? v : L + 1;
		};
		// Each changed tile is tested once against all of Q (cheb(t, q) >= cheb(t, me) - qr, and
		// every target is at most S, or S + 1 for tiles beyond S). Measured on the bot: per-q
		// loops cost ~1.3k + ~700 per tile and attempts often fail; this is cheap, and a
		// rejection only costs a fresh search.
		for (int i = 0; i < n; ++i)
		{
			const int x = delta[i].x, y = delta[i].y;
			if (roots.test(x, y)) return false;
			const int c = cheb(x, y, me);
			if (walls.test(x, y))
			{
				// a is excluded from Q (walls read as unreachable), so cheb(a, q) >= 1 for q in Q.
				if (d(x, y) + std::max(1, c - qr) <= S) return false;
			}
			else
			{
				if (c - qr >= S) continue; // lb >= 1
				int lb = 0x10000;
				for (int yy = std::max(0, y - 1); yy <= std::min(H - 1, y + 1); ++yy)
					for (int xx = std::max(0, x - 1); xx <= std::min(W - 1, x + 1); ++xx)
						if ((xx != x || yy != y) && !sl.walls.test(xx, yy)) lb = std::min(lb, d(xx, yy) + 1);
				if (lb + std::max(0, c - qr) < S + 1) return false;
			}
		}
		return true;
	}

	Ops ops_;
	std::unique_ptr<Slot<Board>[]> slots_;
	Board visited_, me_only_;
	std::uint64_t clock_ = 0;
};
} // namespace cbs::field_memo
