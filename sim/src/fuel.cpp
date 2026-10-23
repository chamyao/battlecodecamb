#include "cbs/fuel.h"

namespace cbs
{
PriceTable::PriceTable()
{
	// PLACEHOLDER prices (to be replaced by values measured against cambc).
	for (int i = 0; i < static_cast<int>(Call::count); ++i)
	{
		base[i] = 200;
		per_n[i] = 0;
	}
	auto set = [&](Call c, std::int64_t b, std::int64_t n) {
		base[static_cast<int>(c)] = b;
		per_n[static_cast<int>(c)] = n;
	};
	set(Call::compute, 0, 1); // explicit charges are passed through as n
	set(Call::fuel_remaining, 50, 0);
	set(Call::yield, 0, 0);
	set(Call::allies, 200, 20);
	set(Call::enemies, 200, 20);
	set(Call::vision, 800, 0);
	set(Call::champion_vision, 800, 0);
	set(Call::hypothetical_vision, 1500, 0);
	set(Call::ward_vision, 1200, 0);
	set(Call::bitboard_op, 300, 0);
	set(Call::bitboard_shadow_cast, 1500, 0);
	set(Call::bitboard_reachable, 500, 10);
	set(Call::distance_field, 1000, 15);
	set(Call::map_mask, 600, 0);
	set(Call::move_to, 400, 0);
	set(Call::attack, 400, 0);
	set(Call::cast, 600, 0);
}

const PriceTable& PriceTable::placeholder()
{
	static const PriceTable t;
	return t;
}
} // namespace cbs
