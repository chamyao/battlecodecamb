#include "cbs/map.h"
#include <algorithm>
#include <fstream>
#include <iterator>
#include <stdexcept>

namespace cbs
{
namespace
{
struct Reader
{
	const std::uint8_t* d;
	std::size_t n, pos;
	std::uint16_t u16()
	{
		if (pos + 2 > n) throw std::runtime_error("map: truncated");
		const std::uint16_t v = static_cast<std::uint16_t>(d[pos] | d[pos + 1] << 8);
		pos += 2;
		return v;
	}
	std::uint8_t u8()
	{
		if (pos >= n) throw std::runtime_error("map: truncated");
		return d[pos++];
	}
};

// Alternating 0/1 run lengths over the 8x8-chunk-padded grid in engine chunk order.
void chunk_layer(Reader& r, int W, int H, Bitboard* out)
{
	const int CW = (W + 7) / 8, CH = (H + 7) / 8, N = CW * CH * 64;
	int s = 0, v = 0;
	while (s < N)
	{
		const int len = r.u16();
		if (v && out)
			for (int t = s; t < s + len && t < N; ++t)
			{
				const int c = t / 64, q = t % 64;
				const int x = (c % CW) * 8 + q % 8, y = (c / CW) * 8 + q / 8;
				if (x < W && y < H) out->set(x, y);
			}
		s += len;
		v ^= 1;
	}
	if (s != N) throw std::runtime_error("map: bad layer length");
}
} // namespace

Vec2 Map::mirror(Vec2 p) const
{
	switch (symmetry)
	{
	case Symmetry::horizontal: return { W - 1 - p.x, p.y };
	case Symmetry::vertical: return { p.x, H - 1 - p.y };
	default: return { W - 1 - p.x, H - 1 - p.y };
	}
}

std::shared_ptr<const Map> decode_map(const std::uint8_t* data, std::size_t size, std::string name)
{
	if (size < 80 || std::memcmp(data, "w62pam\0\0", 8) != 0) throw std::runtime_error("map: bad magic");
	auto m = std::make_shared<Map>();
	m->name = std::move(name);
	m->symmetry = static_cast<Symmetry>(data[72]);
	m->draft_rounds = data[73];
	Reader r{ data, size, 74 };
	m->W = r.u16();
	m->H = r.u16();
	const int W = m->W, H = m->H;
	if (W <= 0 || H <= 0 || W > kMaxDim || H > kMaxDim) throw std::runtime_error("map: bad size");
	const int nregions = r.u16();
	chunk_layer(r, W, H, &m->bushes);
	chunk_layer(r, W, H, &m->walls);
	chunk_layer(r, W, H, &m->holes);
	chunk_layer(r, W, H, &m->altars);
	m->cluster.assign(static_cast<std::size_t>(W) * H, 0);
	for (int s = 0; s < W * H;)
	{
		const std::uint16_t v = r.u16(), n = r.u16();
		if (s + n > W * H) throw std::runtime_error("map: bad cluster map");
		std::fill_n(m->cluster.begin() + s, n, v);
		s += n;
	}
	for (int i = 0; i < nregions; ++i) chunk_layer(r, W, H, nullptr);
	Box a{};
	a.min_x = r.u16();
	a.min_y = r.u16();
	a.max_x = r.u16();
	a.max_y = r.u16();
	m->spawn[0] = a;
	const Vec2 b0 = m->mirror({ a.max_x - 1, a.max_y - 1 }), b1 = m->mirror({ a.min_x, a.min_y });
	m->spawn[1] = { std::min(b0.x, b1.x), std::min(b0.y, b1.y), std::max(b0.x, b1.x) + 1, std::max(b0.y, b1.y) + 1 };
	for (int t = 0; t < 2; ++t)
		for (int y = m->spawn[t].min_y; y < m->spawn[t].max_y; ++y)
			for (int x = m->spawn[t].min_x; x < m->spawn[t].max_x; ++x) m->spawn_mask[t].set(x, y);
	const int ncamps = r.u8();
	for (int k = 0; k < ncamps; ++k)
	{
		const int type = r.u8(), x = r.u8(), y = r.u8();
		if (type >= static_cast<int>(CampType::count)) throw std::runtime_error("map: bad camp type");
		m->camps.push_back({ static_cast<CampType>(type), { x, y }, -1 });
		const Vec2 mp = m->mirror({ x, y });
		if (!(mp == Vec2{ x, y })) m->camps.push_back({ static_cast<CampType>(type), mp, -1 });
	}
	if (r.pos != size) throw std::runtime_error("map: trailing bytes");
	m->camp_at.assign(static_cast<std::size_t>(W) * H, -1);
	for (std::size_t i = 0; i < m->camps.size(); ++i) m->camp_at[m->idx(m->camps[i].pos)] = static_cast<int>(i);
	// Groups: cardinal flood fill in handle order.
	for (std::size_t i = 0; i < m->camps.size(); ++i)
	{
		if (m->camps[i].group >= 0) continue;
		const int g = static_cast<int>(m->groups.size());
		m->groups.emplace_back();
		std::vector<int> stack{ static_cast<int>(i) };
		m->camps[i].group = g;
		while (!stack.empty())
		{
			const int c = stack.back();
			stack.pop_back();
			m->groups[g].camps.push_back(c);
			const Vec2 p = m->camps[c].pos;
			const Vec2 nb[4] = { { p.x + 1, p.y }, { p.x - 1, p.y }, { p.x, p.y + 1 }, { p.x, p.y - 1 } };
			for (auto q : nb)
				if (m->in_bounds(q))
				{
					const int o = m->camp_at[m->idx(q)];
					if (o >= 0 && m->camps[o].group < 0)
					{
						m->camps[o].group = g;
						stack.push_back(o);
					}
				}
		}
		auto& grp = m->groups[g];
		std::sort(grp.camps.begin(), grp.camps.end());
		for (int c : grp.camps)
		{
			const auto& d = camp_design(m->camps[c].type);
			grp.gold += d.gold;
			grp.gems += d.gems;
			grp.respawn = std::max(grp.respawn, d.respawn);
		}
	}
	for (int y = 0; y < H; ++y)
		for (int x = 0; x < W; ++x)
			if (m->altars.test(x, y)) m->altar_list.push_back({ x, y });
	m->vision_cache_.resize(static_cast<std::size_t>(W) * H);
	m->ward_vision_cache_.resize(static_cast<std::size_t>(W) * H);
	m->window_ready_.reset(new std::atomic<std::uint8_t>[static_cast<std::size_t>(W) * H]);
	for (int i = 0; i < W * H; ++i) m->window_ready_[i].store(0, std::memory_order_relaxed);
	return m;
}

std::shared_ptr<const Map> load_map(const std::string& path)
{
	std::ifstream f(path, std::ios::binary);
	if (!f) throw std::runtime_error("map: cannot open " + path);
	std::vector<std::uint8_t> data((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
	std::string name = path.substr(path.find_last_of('/') + 1);
	if (name.size() > 7 && name.ends_with(".map26a")) name.resize(name.size() - 7);
	return decode_map(data.data(), data.size(), name);
}

void Map::vision(Vec2 from, int radius, Bitboard& out) const
{
	const std::uint16_t own = bushes.test(from) ? cluster[idx(from)] : 0;
	shadowcast(
		W, H, from, radius,
		[&](int x, int y) { return walls.test(x, y) || (bushes.test(x, y) && !(own && cluster[y * W + x] == own)); },
		[&](int x, int y) { out.set(x, y); });
}

void Map::fill_windows(int i) const
{
	std::lock_guard<std::mutex> lk(window_mu_);
	if (window_ready_[i].load(std::memory_order_relaxed)) return;
	const int x = i % W, y = i / W;
	Window w{};
	const Vec2 from{ x, y };
	const std::uint16_t own = bushes.test(from) ? cluster[idx(from)] : 0;
	shadowcast(
		W, H, from, 8, [&](int bx, int by) { return walls.test(bx, by) || (bushes.test(bx, by) && !(own && cluster[by * W + bx] == own)); },
		[&](int vx, int vy) { w.rows[vy - y + 8] |= 1u << (vx - x + 8); });
	vision_cache_[i] = w;
	Window w6{};
	for (int r = 2; r <= 14; ++r) w6.rows[r] = w.rows[r] & 0x7FFCu; // Chebyshev <= 6
	ward_vision_cache_[i] = w6;
	window_ready_[i].store(1, std::memory_order_release);
}

void Map::add_window(const Window& w, Vec2 from, Bitboard& out) const
{
	// Window bits are in-map only, so each row is one shifted OR into the 128-bit board row.
	const int sx = from.x - 8;
	const int r0 = std::max(0, 8 - from.y), r1 = std::min(16, H - 1 - from.y + 8);
	for (int r = r0; r <= r1; ++r)
	{
		if (!w.rows[r]) continue;
		const unsigned __int128 bits = static_cast<unsigned __int128>(w.rows[r]);
		const unsigned __int128 v = sx >= 0 ? bits << sx : bits >> -sx;
		std::uint64_t* row = out.w[from.y - 8 + r];
		row[0] |= static_cast<std::uint64_t>(v);
		row[1] |= static_cast<std::uint64_t>(v >> 64);
	}
}
} // namespace cbs
