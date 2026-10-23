// Static map data decoded from .map26a files (format: oracle/tools/map26a.py).
#pragma once
#include <memory>
#include <string>
#include <vector>
#include "bitboard.h"

namespace cbs
{
struct CampSpawn
{
	CampType type;
	Vec2 pos;
	int group;
};

struct CampGroupInfo
{
	std::vector<int> camps; // handles, ascending
	int gold = 0, gems = 0, respawn = 0;
};

struct Box
{
	int min_x, min_y, max_x, max_y; // exclusive max
	bool contains(Vec2 p) const { return p.x >= min_x && p.x < max_x && p.y >= min_y && p.y < max_y; }
};

struct Map
{
	std::string name;
	int W = 0, H = 0;
	Symmetry symmetry = Symmetry::rotational180;
	int draft_rounds = 5; // champions picked per team (header byte 73)
	Bitboard walls, bushes, holes, altars;
	std::vector<std::uint16_t> cluster; // bush cluster id per tile (0 = not a bush), row-major
	Box spawn[2];
	Bitboard spawn_mask[2];
	std::vector<CampSpawn> camps;		// index = camp handle
	std::vector<CampGroupInfo> groups;	// index = group handle
	std::vector<Vec2> altar_list;		// row-major order
	std::vector<int> camp_at;			// handle of the camp spawning on each tile, or -1

	int idx(Vec2 p) const { return p.y * W + p.x; }
	bool in_bounds(Vec2 p) const { return p.x >= 0 && p.y >= 0 && p.x < W && p.y < H; }
	Vec2 mirror(Vec2 p) const;

	// Champion vision from a tile (radius 8): walls and bushes outside the viewer's cluster block.
	void vision(Vec2 from, int radius, Bitboard& out) const;
	// Cached vision as a 17x17 window centred on `from` (bit 8 of row 8 is `from`): radius 8
	// (champions) and radius 6 (wards). Only in-map tiles are set.
	struct Window
	{
		std::uint32_t rows[17];
	};
	const Window& vision8(Vec2 from) const { return vision_cache_[idx(from)]; }
	const Window& vision6(Vec2 from) const { return ward_vision_cache_[idx(from)]; }
	void add_window(const Window& w, Vec2 from, Bitboard& out) const;

	std::vector<Window> vision_cache_, ward_vision_cache_; // filled at load
};

// Throws std::runtime_error on malformed data.
std::shared_ptr<const Map> load_map(const std::string& path);
std::shared_ptr<const Map> decode_map(const std::uint8_t* data, std::size_t size, std::string name = {});
} // namespace cbs
