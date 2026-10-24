// Checks the guest pathfinding primitives against the engine's search (simulator build):
// wfield with k = 0 equals the BFS field to the same goals over the same walls; path_len equals the
// field distance; path_step is a neighbour one step closer. Usage: test_guest MAP...
#include <cstdio>
#include <random>
#include "cbs/map.h"
#include "cbs/game.h"
#include "genome_rt.h"

int main(int argc, char** argv)
{
	int bad = 0, checks = 0;
	for (int a = 1; a < argc; ++a)
	{
		auto mp = cbs::load_map(argv[a]);
		cbs::Game game(mp);
		cbs::Api api(game, 0, -1);
		genome::Ctx X(api);
		const auto& m = *mp;
		std::mt19937 rng(7);
		auto walls = std::make_shared<cbs::Bitboard>(m.walls);
		*walls |= m.holes;
		genome::Tiles W{ walls }, E{ std::make_shared<cbs::Bitboard>() };
		for (int trial = 0; trial < 20; ++trial)
		{
			// goals: a few random open tiles
			auto g = std::make_shared<cbs::Bitboard>();
			for (int i = 0; i < 1 + trial % 4; ++i)
			{
				const int x = rng() % m.W, y = rng() % m.H;
				if (!walls->test(x, y)) g->set(x, y);
			}
			if (!g->any(m.H)) continue;
			genome::Tiles G{ g };
			const genome::Field wf = X.wfield(G, W, E, 0);
			cbs::Bitboard blocked = *walls, visited;
			blocked.andnot(*g);
			std::vector<std::uint16_t> ref(m.W * m.H);
			cbs::distance_field(blocked, *g, nullptr, m.W, m.H, cbs::kUnreachable, ref.data(), visited);
			for (int y = 0; y < m.H; ++y)
				for (int x = 0; x < m.W; ++x)
				{
					const double v = X.field_at(wf, { x, y });
					const double r = ref[y * m.W + x] == cbs::kUnreachable ? 1e9 : ref[y * m.W + x];
					++checks;
					if (v != r && !(walls->test(x, y))) ++bad;
				}
			// path_len / path_step from random tiles to the first goal tile
			cbs::Vec2 gt{};
			g->first(m.H, gt);
			for (int i = 0; i < 20; ++i)
			{
				const int x = rng() % m.W, y = rng() % m.H;
				if (walls->test(x, y)) continue;
				genome::Tiles one{ std::make_shared<cbs::Bitboard>() };
				const_cast<cbs::Bitboard*>(one.b.get())->set(gt);
				cbs::Bitboard bl = *walls;
				bl.reset(gt);
				std::vector<std::uint16_t> f1(m.W * m.H);
				cbs::distance_field(bl, *one.b, nullptr, m.W, m.H, cbs::kUnreachable, f1.data(), visited);
				const double want = f1[y * m.W + x] == cbs::kUnreachable ? 1e9 : f1[y * m.W + x];
				const double got = X.path_len({ x, y }, { gt.x, gt.y }, W, 1e9);
				const genome::Tile st = X.path_step({ x, y }, { gt.x, gt.y }, W, 1e9);
				++checks;
				if (got != want) ++bad, std::printf("path_len %s (%d,%d)->(%d,%d) got %.0f want %.0f\n", argv[a], x, y, gt.x, gt.y, got, want);
				if (want < 1e9 && want > 0 && (!st.valid() || f1[st.y * m.W + st.x] != want - 1 || cbs::chebyshev(st.v(), { x, y }) != 1))
					++bad, std::printf("path_step %s bad\n", argv[a]);
			}
		}
	}
	std::printf("%d checks, %d bad\n", checks, bad);
	return bad != 0;
}
