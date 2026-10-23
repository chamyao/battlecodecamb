"""Decode dump-bot '@@' records (raw engine ABI structs) into JSON.

Usage: parse_dump.py BUNDLE.repl26a [team]  -> JSON on stdout
"""
import json, struct, sys
from bundle import oracle_lines

ABILITY_KINDS = ["none", "attack_reset", "damage", "aoe_damage", "cc", "heal", "dash", "shield"]
CHAMPIONS = ["ryth", "vesper_vale", "vendetta", "cassi", "issac", "stellar", "prism", "marcella",
             "willow", "ren", "varg", "tavi", "heart_of_ruin"]
CAMPS = ["wolf", "elk", "gem_cluster", "gold_cluster", "monolith", "golem"]
SETTINGS = [("capture_time", "i"), ("camp_sleep_time", "i"), ("respawn_time", "i"), ("recall_time", "i"),
            ("submit_gem_duration_multiplier", "d"), ("submit_gem_base_duration", "i"),
            ("submit_gem_minimum_duration", "i"), ("submit_gems_range", "i"), ("max_rounds", "I"),
            ("winning_gems", "I"), ("kill_gold", "I"), ("assist_gold", "I"), ("passive_gold", "I"),
            ("spawn_healing", "f"), ("active_wards", "I"), ("ward_charges", "I"), ("shared_memory_bytes", "I"),
            ("draft_memory_bytes", "I"), ("tile_reveal_rounds", "I"), ("ward_cooldown", "i"), ("ward_lifetime", "i"),
            ("ward_vision_radius", "f"), ("ward_placement_radius", "f"), ("control_ward_vision_radius", "f"),
            ("control_ward_placement_radius", "f"), ("altar_lock_hits", "I"), ("tp_scroll_time", "i"),
            ("tp_crystal_time", "i"), ("reserved", "I")]


def ability(b):
    kind, cooldown, max_charges, targets, attributes = struct.unpack_from("<IiIII", b, 0)
    p = b[20:36]
    out = dict(kind=ABILITY_KINDS[kind] if kind < len(ABILITY_KINDS) else kind, cooldown=cooldown,
               max_charges=max_charges, targets=targets, attributes=attributes)
    k = out["kind"]
    if k == "attack_reset":
        out["enhanced_attack"] = struct.unpack_from("<I", p)[0]
    elif k in ("damage", "heal"):
        out["range"], out["modifier"] = struct.unpack_from("<ff", p)
    elif k in ("aoe_damage", "dash"):
        out["range"], out["radius"], out["modifier"], out["duration"] = struct.unpack_from("<fffi", p)
    elif k in ("cc", "shield"):
        out["range"], out["modifier"], out["duration"] = struct.unpack_from("<ffi", p)
    out["raw_payload"] = p.hex()
    return out


def definition(b):
    t, vision_type, passive = struct.unpack_from("<iIB", b, 0)
    abilities = [ability(b[12 + 36 * i: 48 + 36 * i]) for i in range(2)]
    attack_type = b[84]
    return dict(type=t, vision_type=vision_type, passive=passive, attack_type=attack_type, abilities=abilities)


def decode(lines):
    out = {"champions": {}, "camps": {}, "items": {}, "consumables": {}, "groups": [], "masks": {}}
    for line in lines:
        parts = line.split(" ")
        tag = parts[0]
        if tag == "settings":
            b = bytes.fromhex(parts[2])
            fmt = "<" + "".join(t for _, t in SETTINGS)
            out["settings"] = dict(zip([n for n, _ in SETTINGS], struct.unpack_from(fmt, b)))
        elif tag == "champion_design":
            b = bytes.fromhex(parts[2]); i = int(parts[1])
            d = definition(b[:88])
            names = ["vision_radius", "base_move_speed", "base_attack_range", "base_health", "health_growth",
                     "base_strength", "strength_growth", "base_focus", "focus_growth", "camp_damage_multiplier"]
            d["stats"] = dict(zip(names, struct.unpack_from("<iiifffffff", b, 88)))
            out["champions"][CHAMPIONS[i] if i < len(CHAMPIONS) else str(i)] = d
        elif tag == "camp_design":
            b = bytes.fromhex(parts[2]); i = int(parts[1])
            d = definition(b[:88])
            names = ["vision_radius", "base_move_speed", "base_attack_range", "base_health", "health_growth",
                     "base_strength", "strength_growth", "base_focus", "focus_growth"]
            d["stats"] = dict(zip(names, struct.unpack_from("<fiiffffff", b, 88)))
            out["camps"][CAMPS[i] if i < len(CAMPS) else str(i)] = d
        elif tag == "item_info":
            b = bytes.fromhex(parts[2])
            names = ["cost", "purchasable", "health_points", "strength_points", "focus_points", "passive",
                     "passive_magnitude", "combine_count", "result", "combine_cost"]
            out["items"][int(parts[1])] = dict(zip(names, struct.unpack_from("<IIiiiIfIII", b)))
        elif tag == "consumable_info":
            cost, limit = struct.unpack_from("<II", bytes.fromhex(parts[2]))
            out["consumables"][int(parts[1])] = dict(cost=cost, carry_limit=limit)
        elif tag == "metadata":
            names = ["width", "height", "chunked_width", "chunked_height", "chunk_stride", "board_bytes", "field_bytes"]
            out["metadata"] = dict(zip(names, struct.unpack_from("<iiIIIII", bytes.fromhex(parts[2]))))
        elif tag == "symmetry":
            out["symmetry"] = int(parts[1])
        elif tag == "mask":
            out["masks"][int(parts[1])] = parts[2]
        elif tag == "spawn":
            out.setdefault("spawn", {})[int(parts[1])] = [int(x) for x in parts[2:6]]
        elif tag == "camp_layout":
            w = struct.unpack("<" + "I" * (len(parts[2]) // 8), bytes.fromhex(parts[2]))
            i = 0; layout = []
            while i + 5 <= len(w):
                g, gold, gems, resp, n = w[i:i + 5]; i += 5
                camps = []
                for _ in range(n):
                    h, t, x, y = w[i:i + 4]; i += 4
                    camps.append(dict(handle=h, type=CAMPS[t], x=x, y=y))
                layout.append(dict(group=g, gold=gold, gems=gems, respawn=resp, camps=camps))
            out["camp_layout"] = layout
    return out


if __name__ == "__main__":
    team = sys.argv[2] if len(sys.argv) > 2 else "a"
    lines = list(oracle_lines(sys.argv[1], team))
    # Prefer play-phase records (draft-phase camp designs are empty).
    if "phase play" in lines:
        lines = lines[lines.index("phase play"):]
    print(json.dumps(decode(lines), indent=1))
