// Prints a decoded map in the oracle fixture's terms, for tests/check_maps.py.
#include <cstdio>
#include <vector>
#include "cbs/map.h"

int main(int argc, char** argv)
{
	auto m = cbs::load_map(argv[1]);
	std::printf("dims %d %d\nsymmetry %d\n", m->W, m->H, static_cast<int>(m->symmetry));
	const char* names[4] = { "walls", "bushes", "holes", "altars" };
	const cbs::Bitboard* boards[4] = { &m->walls, &m->bushes, &m->holes, &m->altars };
	std::vector<std::uint8_t> buf((m->W * m->H + 7) / 8);
	for (int k = 0; k < 4; ++k)
	{
		cbs::to_linear(*boards[k], m->W, m->H, buf.data());
		std::printf("mask %s ", names[k]);
		for (auto b : buf) std::printf("%02x", b);
		std::printf("\n");
	}
	for (int t = 0; t < 2; ++t) std::printf("spawn %d %d %d %d %d\n", t, m->spawn[t].min_x, m->spawn[t].min_y, m->spawn[t].max_x, m->spawn[t].max_y);
	for (std::size_t g = 0; g < m->groups.size(); ++g)
	{
		const auto& G = m->groups[g];
		std::printf("group %zu %d %d %d", g, G.gold, G.gems, G.respawn);
		for (int c : G.camps) std::printf(" %d:%d:%d:%d", c, static_cast<int>(m->camps[c].type), m->camps[c].pos.x, m->camps[c].pos.y);
		std::printf("\n");
	}
}
