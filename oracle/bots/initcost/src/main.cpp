// Oracle bot: is work done in C++ static initialisers charged to the first turn, or
// snapshotted at build time? A static initialiser burns ~5M instructions; main() prints
// the fuel left on each instance's first turn.
#include <cambc.h>
#include <cstdio>
using namespace cambc;
static unsigned burn()
{
	volatile unsigned acc = 0;
	for (unsigned i = 0; i < 300000; ++i) acc = acc * 1664525u + i;
	return acc;
}
static const unsigned kBurn = burn();
int main()
{
	std::printf("@@INIT champ=%d draft=%d fuel=%lld burn=%u\n", detail::sdk_my_champion(), is_draft() ? 1 : 0,
				static_cast<long long>(detail::sdk_fuel_remaining()), kBurn);
	for (int i = 0;; ++i)
	{
		if (is_draft()) try { draft::pick(static_cast<champion_draft>(i % 11)); } catch (...) {}
		end_turn();
	}
}
