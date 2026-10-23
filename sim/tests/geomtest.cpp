// Replays oracle geometry probes (oracle/bots/geom) against the simulator's primitives.
// Usage: zcat oracle/fixtures/geom/MAP.txt.gz | geomtest maps/MAP.map26a
#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include "cbs/map.h"

using namespace cbs;

static bool parse_hex(const std::string& hex, int W, int H, Bitboard& b)
{
	const std::size_t n = (static_cast<std::size_t>(W) * H + 7) / 8;
	if (hex.size() != 2 * n) return false;
	std::vector<std::uint8_t> bytes(n);
	for (std::size_t i = 0; i < n; ++i) bytes[i] = static_cast<std::uint8_t>(std::stoi(hex.substr(2 * i, 2), nullptr, 16));
	from_linear(b, W, H, bytes.data());
	return true;
}

int main(int argc, char** argv)
{
	auto map = load_map(argv[1]);
	const int W = map->W, H = map->H;
	std::vector<std::string> L;
	for (std::string line; std::getline(std::cin, line);) L.push_back(line);
	int ok[9] = {}, bad[9] = {};
	const char* names[9] = { "shadow", "reach", "field", "circle", "cheb", "cv", "wv", "cv8", "wv6" };
	auto word = [](const std::string& s, int i) {
		std::istringstream is(s);
		std::string w;
		for (int k = 0; k <= i; ++k) is >> w;
		return w;
	};
	for (std::size_t i = 0; i + 1 < L.size(); ++i)
	{
		const std::string& l = L[i];
		if (l.rfind("walls ", 0) == 0 && L[i + 1].rfind("origin ", 0) == 0)
		{
			Bitboard walls, exp, got;
			if (!parse_hex(word(l, 1), W, H, walls)) continue;
			int ox, oy, d;
			std::sscanf(L[i + 1].c_str(), "origin %d %d %d", &ox, &oy, &d);
			std::size_t j = i + 2;
			if (j + 1 < L.size() && L[j] == "rc 0" && L[j + 1].rfind("shadow ", 0) == 0)
			{
				if (parse_hex(word(L[j + 1], 1), W, H, exp))
				{
					shadow_cast(walls, W, H, { ox, oy }, d, got);
					(got == exp ? ok : bad)[0]++;
				}
				j += 2;
			}
			else ++j;
			if (j + 1 < L.size() && L[j] == "rc 0" && L[j + 1].rfind("reach ", 0) == 0 && parse_hex(word(L[j + 1], 1), W, H, exp))
			{
				reachable(walls, W, H, { ox, oy }, d, got);
				(got == exp ? ok : bad)[1]++;
			}
		}
		else if (l.rfind("field ", 0) == 0 && i >= 3 && i + 1 < L.size())
		{
			Bitboard walls, roots, dests, vis, gvis;
			if (!parse_hex(word(L[i - 3], 1), W, H, walls) || !parse_hex(word(L[i - 2], 1), W, H, roots) ||
				!parse_hex(word(L[i - 1], 1), W, H, dests) || !parse_hex(word(L[i + 1], 1), W, H, vis))
				continue;
			int to, maxd, cnt;
			std::sscanf(l.c_str(), "field %d %d %d", &to, &maxd, &cnt);
			std::vector<std::uint16_t> exp;
			std::istringstream is(word(l, 4));
			for (std::string v; std::getline(is, v, ',');)
				if (!v.empty()) exp.push_back(static_cast<std::uint16_t>(std::stoi(v, nullptr, 16)));
			if (exp.size() != static_cast<std::size_t>(W * H)) continue;
			std::vector<std::uint16_t> got(W * H);
			const int c = distance_field(walls, roots, to ? &dests : nullptr, W, H, maxd, got.data(), gvis);
			(got == exp && gvis == vis && c == cnt ? ok : bad)[2]++;
		}
		else if (l.rfind("radius ", 0) == 0 && i >= 1 && L[i - 1] == "rc 0 0" && i + 2 < L.size())
		{
			int x, y;
			char rs[64];
			std::sscanf(l.c_str(), "radius %d %d %63s", &x, &y, rs);
			const float r = static_cast<float>(std::strtod(rs, nullptr));
			Bitboard c, k, gc, gk;
			if (!parse_hex(word(L[i + 1], 1), W, H, c) || !parse_hex(word(L[i + 2], 1), W, H, k)) continue;
			draw_circle(gc, W, H, { x, y }, r);
			draw_chebyshev(gk, W, H, { x, y }, r);
			(gc == c ? ok : bad)[3]++;
			(gk == k ? ok : bad)[4]++;
		}
		else if (l.rfind("vision ", 0) == 0)
		{
			int x, y, rc, rw;
			std::sscanf(l.c_str(), "vision %d %d %d %d", &x, &y, &rc, &rw);
			std::size_t j = i + 1;
			Bitboard exp;
			if (rc == 0 && j < L.size() && L[j].rfind("cv ", 0) == 0)
			{
				if (parse_hex(word(L[j], 1), W, H, exp))
				{
					Bitboard got, got8;
					map->vision({ x, y }, 8, got);
					(got == exp ? ok : bad)[5]++;
					map->add_window(map->vision8({ x, y }), { x, y }, got8);
					(got8 == exp ? ok : bad)[7]++;
				}
				++j;
			}
			if (rw == 0 && j < L.size() && L[j].rfind("wv ", 0) == 0 && parse_hex(word(L[j], 1), W, H, exp))
			{
				Bitboard got;
				map->vision({ x, y }, 6, got);
				(got == exp ? ok : bad)[6]++;
				Bitboard got6;
				map->add_window(map->vision6({ x, y }), { x, y }, got6);
				(got6 == exp ? ok : bad)[8]++;
			}
		}
	}
	int total_bad = 0;
	for (int k = 0; k < 9; ++k)
	{
		std::printf("%-7s ok=%d bad=%d\n", names[k], ok[k], bad[k]);
		total_bad += bad[k];
		if (ok[k] == 0) total_bad++;
	}
	return total_bad ? 1 : 0;
}
