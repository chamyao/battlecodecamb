"""(Copied from branch sim/engine; partial= added to decode a map embedded in a replay.)
Reference decoder for .map26a map files (reverse-engineered; verified against engine dumps).

Layout (little-endian):
  0   char[8]  magic "w62pam\\0\\0"
  8   u8[3]    version (00 00 01)
  11  ...      visualiser palette (ignored)
  72  u8       symmetry (0 horizontal, 1 vertical, 2 rotational180)
  73  u8       unknown (3 or 5)
  74  u16 W, u16 H
  78  u16      number of bush-region masks that follow the cluster map (= clusters + 1)
  then u16 words:
    4 chunk-RLE layers: bushes, walls, holes, altars.
       chunk-RLE: alternating run lengths (starting with 0s) over the padded
       ceil(W/8)*ceil(H/8) 8x8 chunks, tiles ordered chunk-major, row-major inside a chunk.
    bush cluster id map: (value, count) pairs, row-major over W*H.
    N chunk-RLE layers: union of bushes, then one mask per cluster.
    u16 spawn A box: min_x, min_y, max_x, max_y (exclusive max)
  then bytes: u8 camp count, then (type, x, y) per camp for one half of the map;
    handles are assigned in order: each listed camp, then its mirror
    image unless the camp lies on the symmetry axis/centre (then it has no twin).
"""
import struct

CAMPS = ["wolf", "elk", "gem_cluster", "gold_cluster", "monolith", "golem"]


def mirror(sym, W, H, x, y):
    if sym == 0: return W - 1 - x, y
    if sym == 1: return x, H - 1 - y
    return W - 1 - x, H - 1 - y


def decode(data, partial=False):
    assert data[:8] == b"w62pam\0\0", data[:8]
    sym, unk = data[72], data[73]
    W, H = struct.unpack_from("<HH", data, 74)
    CW, CH = (W + 7) // 8, (H + 7) // 8
    N = CW * CH * 64
    pos = 78

    def u16():
        nonlocal pos
        v = struct.unpack_from("<H", data, pos)[0]; pos += 2; return v

    def chunk_layer():
        tiles = set(); s = 0; v = 0
        while s < N:
            n = u16()
            if v:
                for t in range(s, s + n):
                    c, r = divmod(t, 64)
                    tiles.add(((c % CW) * 8 + r % 8, (c // CW) * 8 + r // 8))
            s += n; v ^= 1
        assert s == N
        return tiles

    nregions = u16()
    layers = {k: chunk_layer() for k in ("bushes", "walls", "holes", "altars")}
    cluster = [0] * (W * H); s = 0
    while s < W * H:
        v, n = u16(), u16()
        cluster[s:s + n] = [v] * n; s += n
    regions = [chunk_layer() for _ in range(nregions)]
    spawn_a = [u16() for _ in range(4)]
    ncamps = data[pos]; pos += 1
    camps = []
    for k in range(ncamps):
        t, x, y = data[pos:pos + 3]; pos += 3
        camps.append(dict(handle=len(camps), type=CAMPS[t], x=x, y=y))
        mx, my = mirror(sym, W, H, x, y)
        if (mx, my) != (x, y):
            camps.append(dict(handle=len(camps), type=CAMPS[t], x=mx, y=my))
    if not partial:
        assert pos == len(data), (pos, len(data))
    ax0, ay0, ax1, ay1 = spawn_a
    bx0, by0 = mirror(sym, W, H, ax1 - 1, ay1 - 1)
    bx1, by1 = mirror(sym, W, H, ax0, ay0)
    spawn_b = [min(bx0, bx1), min(by0, by1), max(bx0, bx1) + 1, max(by0, by1) + 1]
    return dict(symmetry=sym, unknown=unk, width=W, height=H, cluster=cluster, regions=regions,
                spawn=[spawn_a, spawn_b], camps=camps, end=pos, **layers)


if __name__ == "__main__":
    import sys, json, glob, os
    fixdir = sys.argv[1]
    bad = 0
    for path in sorted(glob.glob(os.path.join(sys.argv[2], "*.map26a"))):
        name = os.path.basename(path)[:-7]
        m = decode(open(path, "rb").read())
        f = json.load(open(os.path.join(fixdir, name + ".json")))
        W, H = m["width"], m["height"]
        errs = []
        if (W, H) != (f["metadata"]["width"], f["metadata"]["height"]): errs.append("dims")
        if m["symmetry"] != f["symmetry"]: errs.append("sym")
        for k in ("walls", "bushes", "holes", "altars"):
            b = bytes.fromhex(f["masks"][k])
            ft = {(i % W, i // W) for i in range(W * H) if b[i // 8] >> (i % 8) & 1}
            if ft != m[k]: errs.append(k)
        if [m["spawn"][0], m["spawn"][1]] != [f["spawn"]["0"], f["spawn"]["1"]]: errs.append(f"spawn {m['spawn']} {f['spawn']}")
        fc = sorted((c["handle"], c["type"], c["x"], c["y"]) for g in f["camp_layout"] for c in g["camps"])
        mc = [(c["handle"], c["type"], c["x"], c["y"]) for c in m["camps"]]
        if fc != mc: errs.append("camps")
        nclusters = max(m["cluster"])
        if len(m["regions"]) != nclusters + 1: errs.append(f"regions {len(m['regions'])} vs {nclusters}")
        print(name, W, H, "unk", m["unknown"], "OK" if not errs else errs)
        bad += bool(errs)
    print("failures:", bad)
