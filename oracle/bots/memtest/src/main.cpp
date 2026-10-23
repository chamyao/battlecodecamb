// Oracle bot: how much linear memory can a bot instance grow to? Grows by 4 MiB pages
// (memory.grow via __builtin_wasm_memory_grow) until refused; prints the last success.
#include <cambc.h>
#include <cstdio>
using namespace cambc;
int main()
{
	if (is_draft() && detail::sdk_my_team() == 0)
	{
		const std::size_t start = __builtin_wasm_memory_size(0);
		std::size_t pages = start;
		while (__builtin_wasm_memory_grow(0, 64) != static_cast<std::size_t>(-1)) pages += 64; // 64 pages = 4 MiB
		std::printf("@@MEM start_pages=%zu max_pages=%zu max_mib=%zu\n", start, pages, pages * 64 / 1024);
	}
	for (int i = 0;; ++i)
	{
		if (is_draft()) try { draft::pick(static_cast<champion_draft>(i % 11)); } catch (...) {}
		end_turn();
	}
}
