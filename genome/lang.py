"""Gene language: parse, type-check and compile a genome to C++ (docs/GENOME.md).

A genome file is Python syntax restricted to a small typed subset:

    STRIKE: Num = 2.5                       # keep: persistent per bot instance (only update() may assign)

    @gene("g7", "danger at a tile", parents=["g2"])
    def danger_at(t: Tile) -> Num:
        return sum(u.strength for u in enemies() if dist(u.pos, t) <= 5)

    @gene("g1", "value of doing this option now")
    def score(o: Option) -> Num: ...

Entry genes: score(o: Option) -> Num (required); update() -> None (optional; runs at the start of each
turn, the only gene that may assign keep variables or call write_shared).
"""
import ast
import os
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field

TYPES = {"Num", "Bool", "Tile", "Unit", "Units", "Tiles", "Option", "Field", "None"}
CPP = {"Num": "double", "Bool": "bool", "Tile": "Tile", "Unit": "Unit", "Units": "Units", "Tiles": "Tiles",
       "Option": "Option", "Field": "Field", "None": "void"}
ELEM = {"Units": "Unit", "Tiles": "Tile"}
DEFAULT = {"Num": "0.0", "Bool": "false", "Tile": "Tile{}", "Unit": "Unit{}", "Units": "Units{}", "Tiles": "Tiles{}",
           "Option": "Option{}", "Field": "Field{}"}

# Named constants (all Num). Values mirror the runtime (genome/runtime/genome_rt.h) and the engine enums.
CONSTANTS = {
    # option kinds
    "PICK": 1, "MOVE": 2, "ATTACK": 3, "CAST": 4, "WARD": 5, "BUY": 6, "RECALL": 7, "TRIBUTE": 8, "CANCEL": 9,
    "LOCK": 10, "BUY_LOCK": 11,
    # champion types (cbs::ChampionType); draft picks use the same numbers (Cassi & Issac = CASSI)
    "RYTH": 0, "VESPER_VALE": 1, "VENDETTA": 2, "CASSI": 3, "ISSAC": 4, "STELLAR": 5, "PRISM": 6, "MARCELLA": 7,
    "WILLOW": 8, "REN": 9, "VARG": 10, "TAVI": 11, "HEART_OF_RUIN": 12,
    # camp types (cbs::CampType)
    "WOLF": 0, "ELK": 1, "GEM_CLUSTER": 2, "GOLD_CLUSTER": 3, "MONOLITH": 4, "GOLEM": 5,
    # ability kinds (cbs::AbilityKind)
    "AB_NONE": 0, "AB_RESET": 1, "AB_DAMAGE": 2, "AB_AOE": 3, "AB_CC": 4, "AB_HEAL": 5, "AB_DASH": 6, "AB_SHIELD": 7,
    # item passives (cbs::ItemPassive)
    "P_NONE": 0, "P_MONSTER": 1, "P_DURABILITY": 2, "P_TREASURE": 3, "P_JUNGLE": 4, "P_HOME": 5,
    # ability target bits
    "T_CAMPS": 1, "T_ENEMIES": 2, "T_ALLIES": 4, "T_SELF": 8, "T_GROUND": 16,
    "INF": 1e9,
}

# Primitives: name -> (arg types, return type, C++ expression template). The game's SDK, plus generic
# operations. `{0}`... are arguments; `X` is the per-instance context.
PRIMS = {
    # self and game state
    "me": ((), "Unit", "X.me()"),
    "gems": ((), "Num", "X.gems()"),
    "gold": ((), "Num", "X.gold()"),
    "round": ((), "Num", "X.round()"),
    "fuel": ((), "Num", "X.fuel()"),
    "can_shop": ((), "Bool", "X.can_shop()"),
    "alive": ((), "Bool", "X.alive()"),
    "can_move": ((), "Bool", "X.my_state(cbs::state_bit::can_move)"),
    "can_attack": ((), "Bool", "X.my_state(cbs::state_bit::can_attack)"),
    "channeling": ((), "Bool", "X.channeling()"),
    "team_gems": ((), "Num", "X.submitted(false)"),
    "enemy_gems": ((), "Num", "X.submitted(true)"),
    # units in vision
    "enemies": ((), "Units", "X.enemies()"),
    "allies": ((), "Units", "X.allies()"),
    "camps": ((), "Units", "X.camps()"),
    "unit_gems": (("Unit",), "Num", "X.unit_gems({0})"),
    "is_recalling": (("Unit",), "Bool", "X.unit_state({0}, 2)"),
    "is_tributing": (("Unit",), "Bool", "X.unit_state({0}, 4)"),
    "camp_group": (("Unit",), "Num", "X.camp_group({0})"),
    "is_awake": (("Unit",), "Bool", "X.camp_awake({0})"),
    "camp_spawn": (("Unit",), "Tile", "X.camp_spawn({0})"),
    "group_gems": (("Num",), "Num", "X.group_gems({0})"),
    "group_gold": (("Num",), "Num", "X.group_gold({0})"),
    "group_respawning": (("Num",), "Bool", "X.group_respawning({0})"),
    "group_reward": (("Num",), "Bool", "X.group_reward({0})"),
    "group_tiles": (("Num",), "Tiles", "X.group_tiles({0})"),
    "num_groups": ((), "Num", "X.num_groups()"),
    "visible": (("Tile",), "Bool", "X.visible({0})"),
    "vision": ((), "Tiles", "X.vision()"),
    "ally_tiles": ((), "Tiles", "X.ally_tiles()"),
    "enemy_tiles": ((), "Tiles", "X.enemy_tiles()"),
    "camp_tiles": ((), "Tiles", "X.camp_tiles()"),
    # static map
    "altars": ((), "Tiles", "X.altars()"),
    "walls": ((), "Tiles", "X.walls()"),
    "bushes": ((), "Tiles", "X.bushes()"),
    "holes": ((), "Tiles", "X.holes()"),
    "my_spawn": ((), "Tiles", "X.spawn(false)"),
    "enemy_spawn": ((), "Tiles", "X.spawn(true)"),
    "camp_spawns": ((), "Tiles", "X.camp_spawns()"),
    "type_spawns": (("Num",), "Tiles", "X.type_spawns({0})"),
    "locked_altars": ((), "Tiles", "X.locked_altars()"),
    "spawn_type": (("Tile",), "Num", "X.spawn_type({0})"),
    "spawn_group": (("Tile",), "Num", "X.spawn_group({0})"),
    "camp_base_health": (("Num",), "Num", "X.camp_base({0}, 0)"),
    "camp_base_strength": (("Num",), "Num", "X.camp_base({0}, 1)"),
    "width": ((), "Num", "X.width()"),
    "height": ((), "Num", "X.height()"),
    # geometry
    "tile": (("Num", "Num"), "Tile", "Tile{{int({0}), int({1})}}"),
    "dist": (("Tile", "Tile"), "Num", "X.dist({0}, {1})"),
    "near": (("Tile", "Num"), "Tiles", "X.near({0}, {1})"),
    "nearest": (("Tiles", "Tile"), "Tile", "X.nearest({0}, {1})"),
    "size": (("Tiles",), "Num", "X.size({0})"),
    "count_units": (("Units",), "Num", "double({0}.size())"),
    "valid": (("Tile",), "Bool", "{0}.valid()"),
    "exists": (("Unit",), "Bool", "{0}.valid()"),
    "field": (("Tiles",), "Field", "X.field({0})"),
    "field_avoid": (("Tiles", "Tiles", "Tiles"), "Field", "X.field_avoid({0}, {1}, {2})"),
    "box_field": (("Tiles", "Tiles"), "Field", "X.box_field({0}, {1})"),
    "dash_field": (("Tile", "Tiles"), "Field", "X.dash_field({0}, {1})"),
    "wfield": (("Tiles", "Tiles", "Tiles", "Num"), "Field", "X.wfield({0}, {1}, {2}, {3})"),
    "path_step": (("Tile", "Tile", "Tiles", "Num"), "Tile", "X.path_step({0}, {1}, {2}, {3})"),
    "path_len": (("Tile", "Tile", "Tiles", "Num"), "Num", "X.path_len({0}, {1}, {2}, {3})"),
    "territory": (("Tiles", "Tiles", "Tiles"), "Tiles", "X.territory({0}, {1}, {2})"),
    "attack_damage": (("Unit", "Unit"), "Num", "X.attack_damage({0}, {1})"),
    "cast_damage": (("Unit", "Num", "Unit"), "Num", "X.cast_damage({0}, {1}, {2})"),
    "shield": (("Unit",), "Num", "X.shield({0})"),
    "hits_to_kill": (("Unit", "Unit"), "Num", "X.hits_to_kill({0}, {1})"),
    "at": (("Field", "Tile"), "Num", "X.field_at({0}, {1})"),
    # raw unit reads (any visible unit; 0 when out of vision)
    "cooldown": (("Unit", "Num"), "Num", "X.cooldown({0}, {1})"),
    "ability_kind": (("Unit", "Num"), "Num", "X.ability({0}, {1}, 0)"),
    "ability_cooldown": (("Unit", "Num"), "Num", "X.ability({0}, {1}, 1)"),
    "ability_range": (("Unit", "Num"), "Num", "X.ability({0}, {1}, 2)"),
    "ability_radius": (("Unit", "Num"), "Num", "X.ability({0}, {1}, 3)"),
    "ability_targets": (("Unit", "Num"), "Num", "X.ability({0}, {1}, 4)"),
    "ability_modifier": (("Unit", "Num"), "Num", "X.ability({0}, {1}, 5)"),
    "ability_duration": (("Unit", "Num"), "Num", "X.ability({0}, {1}, 6)"),
    "ability_moveless": (("Unit", "Num"), "Num", "X.ability({0}, {1}, 7)"),
    "item_count": (("Unit", "Num"), "Num", "X.item_count({0}, {1})"),
    "unit_gold": (("Unit",), "Num", "X.unit_gold({0})"),
    "buff_value": (("Unit", "Num"), "Num", "X.buff_value({0}, {1})"),
    "buff_turns": (("Unit", "Num"), "Num", "X.buff_turns({0}, {1})"),
    "channel_left": (("Unit",), "Num", "X.channel_left({0})"),
    "group_cooldown": (("Num",), "Num", "X.group_cooldown({0})"),
    "lock_hits": (("Tile",), "Num", "X.lock_hits({0})"),
    "lock_enemy": (("Tile",), "Bool", "X.lock_enemy({0})"),
    "walk_nearest": (("Tiles", "Tile", "Tiles"), "Tile", "X.walk_nearest({0}, {1}, {2})"),
    # abilities (my slots 0 and 1)
    "slot_kind": (("Num",), "Num", "X.slot_kind({0})"),
    "slot_ready": (("Num",), "Bool", "X.slot_ready({0})"),
    "slot_range": (("Num",), "Num", "X.slot_range({0})"),
    "slot_radius": (("Num",), "Num", "X.slot_radius({0})"),
    "slot_targets": (("Num",), "Num", "X.slot_targets({0})"),
    "slot_moveless": (("Num",), "Bool", "X.slot_moveless({0})"),
    # items (ids 0-41)
    "item_cost": (("Num",), "Num", "X.item_cost({0})"),
    "item_strength": (("Num",), "Num", "X.item_stat({0}, 1)"),
    "item_focus": (("Num",), "Num", "X.item_stat({0}, 2)"),
    "item_health": (("Num",), "Num", "X.item_stat({0}, 0)"),
    "item_passive": (("Num",), "Num", "X.item_passive({0})"),
    "items_owned": (("Num",), "Num", "X.items_owned({0})"),
    "has_lock": ((), "Bool", "X.has_lock()"),
    # memory
    "read_shared": (("Num",), "Num", "X.read_shared({0})"),
    "write_shared": (("Num", "Num"), "None", "X.write_shared({0}, {1})"),
    # turn order (takes effect next round)
    "set_priority": (("Num",), "None", "X.set_priority({0})"),
    # what the loop did this turn (for after(): e.g. announce a claim in shared memory)
    "acted": (("Num",), "Bool", "X.acted({0})"),
    "acted_tile": (("Num",), "Tile", "X.acted_tile({0})"),
    # draft
    "picked_by_us": (("Num",), "Bool", "X.picked(false, {0})"),
    "picked_by_them": (("Num",), "Bool", "X.picked(true, {0})"),
    # generic
    "abs": (("Num",), "Num", "std::fabs({0})"),
    "floor": (("Num",), "Num", "std::floor({0})"),
    "sqrt": (("Num",), "Num", "std::sqrt(std::max(0.0, {0}))"),
    "rand": (("Num",), "Num", "X.rand({0})"),
}
# Primitives whose simulator price is not yet calibrated against cambc (genome/FUEL.md): rejected unless
# GENOME_UNCALIBRATED=1 (calibration probes), so the search cannot use them before they are priced.
UNCALIBRATED = set()
# calibrated Oct 24 (genome/FUEL.md): wfield, path_step, path_len, territory, dash_field, attack_damage, cast_damage, shield,
# hits_to_kill; the raw SDK reads cooldown, ability_*, item_count, unit_gold, buff_value, buff_turns, channel_left,
# group_cooldown, lock_hits, lock_enemy
EFFECT_PRIMS = {"write_shared", "set_priority"}  # allowed only in update() and after()
MEMORY_GENES = ("update", "after")  # the entry genes that may assign keeps and call effects

FIELDS = {
    "Unit": {"pos": ("Tile", "{0}.pos"), "health": ("Num", "double({0}.health)"),
             "max_health": ("Num", "double({0}.max_health)"), "strength": ("Num", "double({0}.strength)"),
             "focus": ("Num", "double({0}.focus)"), "attack_range": ("Num", "double({0}.attack_range)"),
             "move_speed": ("Num", "double({0}.move_speed)"),
             "type": ("Num", "double({0}.type)"), "is_enemy": ("Bool", "{0}.enemy"),
             "is_champion": ("Bool", "({0}.kind == 1)"), "is_camp": ("Bool", "({0}.kind == 2)"),
             "health_frac": ("Num", "({0}.max_health > 0 ? double({0}.health) / {0}.max_health : 0.0)")},
    "Tile": {"x": ("Num", "double({0}.x)"), "y": ("Num", "double({0}.y)")},
    "Option": {"kind": ("Num", "double({0}.kind)"), "unit": ("Unit", "X.unit_of({0})"), "tile": ("Tile", "{0}.tile"),
               "slot": ("Num", "double({0}.slot)"), "item": ("Num", "double({0}.item)"),
               "champ": ("Num", "double({0}.champ)"), "count": ("Num", "double({0}.count)")},
}


class GenomeError(Exception):
    pass


@dataclass
class Gene:
    id: str
    name: str
    desc: str
    parents: list
    params: list            # [(name, type)]
    ret: str
    node: ast.FunctionDef
    calls: set = field(default_factory=set)       # gene names called
    keep_reads: set = field(default_factory=set)
    keep_writes: set = field(default_factory=set)
    shared_reads: set = field(default_factory=set)   # constant offsets, or "*"
    shared_writes: set = field(default_factory=set)


@dataclass
class Genome:
    genes: dict             # name -> Gene
    keeps: dict             # name -> (type, ast default expr)
    source: str

    def edges(self):
        """Dependency edges as (a, b, kind): calls, keep links (writer -> reader), shared-byte links."""
        out = set()
        for g in self.genes.values():
            for c in g.calls:
                out.add((g.name, c, "call"))
        for w in self.genes.values():
            for r in self.genes.values():
                if w is r:
                    continue
                if w.keep_writes & r.keep_reads:
                    out.add((w.name, r.name, "keep"))
                sw, sr = w.shared_writes, r.shared_reads
                if sw and sr and ("*" in sw or "*" in sr or sw & sr):
                    out.add((w.name, r.name, "shared"))
        return sorted(out)

    def ids(self):
        return {g.id: g.name for g in self.genes.values()}

    def digest(self):
        return hashlib.sha256(self.source.encode()).hexdigest()[:16]


# ---------------------------------------------------------------- parsing

_ID_RE = re.compile(r"[A-Za-z0-9_.-]{1,64}")


def _const_str(node, what):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise GenomeError(f"{what} must be a string literal")


def _gene_id(node, what):
    s = _const_str(node, what)
    if not _ID_RE.fullmatch(s):
        raise GenomeError(f"{what} {s!r}: letters, digits, '_', '.', '-' only (1-64)")
    return s


def _one_line(node, what):
    # descriptions land in C++ // comments: a line break of any kind (\r, \n, U+2028, ...) would end the
    # comment, so control, format and separator characters are rejected; a backslash could splice lines
    s = _const_str(node, what)
    bad = [c for c in s if unicodedata.category(c) in ("Cc", "Cf", "Zl", "Zp") or c == "\\"]
    if bad:
        raise GenomeError(f"{what}: one plain line, no control characters or backslashes (found {bad[0]!r})")
    return s


def _comment(s):
    """Defensive: printable text only, so nothing can leave a // comment."""
    return "".join(c if c.isprintable() and c != "\\" else " " for c in s)


def _ann(node, what):
    if isinstance(node, ast.Name) and node.id in TYPES:
        return node.id
    if isinstance(node, ast.Constant) and node.value is None:
        return "None"
    raise GenomeError(f"{what}: unknown type annotation {ast.unparse(node) if node else None}")


def parse(source):
    try:
        mod = ast.parse(source)
    except SyntaxError as e:
        raise GenomeError(f"syntax error line {e.lineno}: {e.msg}")
    genes, keeps = {}, {}
    for st in mod.body:
        if isinstance(st, ast.AnnAssign) and isinstance(st.target, ast.Name):
            name = st.target.id
            if name in keeps or name in CONSTANTS or name in PRIMS:
                raise GenomeError(f"line {st.lineno}: keep {name} redefined or shadows a builtin")
            t = _ann(st.annotation, f"keep {name}")
            if t not in ("Num", "Bool", "Tile", "Tiles", "Field"):
                raise GenomeError(f"line {st.lineno}: keep {name} must be Num, Bool, Tile, Tiles or Field")
            keeps[name] = (t, st.value)
        elif isinstance(st, ast.FunctionDef):
            if len(st.decorator_list) != 1 or not isinstance(st.decorator_list[0], ast.Call) or \
                    getattr(st.decorator_list[0].func, "id", None) != "gene":
                raise GenomeError(f"line {st.lineno}: {st.name} needs exactly one @gene(id, description, parents=[...])")
            d = st.decorator_list[0]
            if len(d.args) != 2:
                raise GenomeError(f"line {st.lineno}: @gene takes (id, description)")
            gid, desc = _gene_id(d.args[0], "gene id"), _one_line(d.args[1], "gene description")
            parents = []
            for kw in d.keywords:
                if kw.arg != "parents" or not isinstance(kw.value, ast.List):
                    raise GenomeError(f"line {st.lineno}: @gene keywords: parents=[...] only")
                parents = [_gene_id(e, "parent id") for e in kw.value.elts]
            if st.name in genes or st.name in PRIMS or st.name in CONSTANTS or st.name in keeps:
                raise GenomeError(f"line {st.lineno}: gene {st.name} redefined or shadows a builtin")
            a = st.args
            if a.vararg or a.kwarg or a.kwonlyargs or a.defaults or a.posonlyargs:
                raise GenomeError(f"line {st.lineno}: {st.name}: plain positional parameters only")
            params = [(p.arg, _ann(p.annotation, f"{st.name} parameter {p.arg}")) for p in a.args]
            ret = _ann(st.returns, f"{st.name} return")
            genes[st.name] = Gene(gid, st.name, desc, parents, params, ret, st)
        elif isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
            continue  # module docstring / comments-as-strings
        else:
            raise GenomeError(f"line {st.lineno}: only keep declarations (NAME: Type = value) and @gene functions at top level")
    ids = [g.id for g in genes.values()]
    if len(set(ids)) != len(ids):
        raise GenomeError("duplicate gene ids")
    if "score" not in genes:
        raise GenomeError("missing entry gene score(o: Option) -> Num")
    s = genes["score"]
    if [t for _, t in s.params] != ["Option"] or s.ret != "Num":
        raise GenomeError("score must be score(o: Option) -> Num")
    if "consider" in genes and ([t for _, t in genes["consider"].params] != ["Num"] or genes["consider"].ret != "Bool"):
        raise GenomeError("consider must be consider(kind: Num) -> Bool")
    if "after" in genes and (genes["after"].params or genes["after"].ret != "None"):
        raise GenomeError("after must be after() -> None")
    if "update" in genes and (genes["update"].params or genes["update"].ret != "None"):
        raise GenomeError("update must be update() -> None")
    if "reserve" in genes and (genes["reserve"].params or genes["reserve"].ret != "Num"):
        raise GenomeError("reserve must be reserve() -> Num")
    g = Genome(genes, keeps, source)
    Checker(g).run()
    return g


# ---------------------------------------------------------------- type check + codegen

class Checker:
    """Type-checks every gene and produces its C++ body. Expressions return (type, cpp, ops) where ops is
    the number of own operations (fuel accounting); primitive engine calls are priced by the Api."""

    def __init__(self, genome):
        self.g = genome
        self.cpp = {}

    def run(self):
        for gene in self.g.genes.values():
            self.cur = gene
            self.locals = dict(gene.params)
            self.decls = []           # (name, type): function-scoped locals, declared at the top in C++
            body = self.block(gene.node.body, 1)
            if gene.ret != "None" and not _returns(gene.node.body):
                raise GenomeError(f"{gene.name}: not every path returns a value")
            head = [f"\t{CPP[t]} {n} = {DEFAULT[t]};" for n, t in self.decls]
            self.cpp[gene.name] = head + body
        self._no_recursion()

    def _no_recursion(self):
        state = {}

        def visit(n, path):
            if state.get(n) == 1:
                raise GenomeError(f"recursion: {' -> '.join(path + [n])}")
            if state.get(n) == 2:
                return
            state[n] = 1
            for c in self.g.genes[n].calls:
                visit(c, path + [n])
            state[n] = 2

        for n in self.g.genes:
            visit(n, [])

    def err(self, node, msg):
        raise GenomeError(f"{self.cur.name} line {getattr(node, 'lineno', '?')}: {msg}")

    # ---- statements
    def block(self, stmts, ind):
        out = []
        for st in stmts:
            out.extend(self.stmt(st, ind))
        return out

    def stmt(self, st, ind):
        p = "\t" * ind
        if isinstance(st, ast.Pass):
            return []
        if isinstance(st, ast.Return):
            if st.value is None:
                if self.cur.ret != "None":
                    self.err(st, "return needs a value")
                return [f"{p}return;"]
            t, c, ops = self.expr(st.value)
            t = self.coerce(st, t, self.cur.ret)
            return [f"{p}F({ops + 1});", f"{p}return {c};"]
        if isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            return self.assign(st, ind)
        if isinstance(st, ast.If):
            t, c, ops = self.expr(st.test)
            self.need(st.test, t, "Bool")
            out = [f"{p}F({ops + 1});", f"{p}if ({c}) {{"] + self.block(st.body, ind + 1) + [f"{p}}}"]
            if st.orelse:
                out[-1] += " else {"
                out += self.block(st.orelse, ind + 1) + [f"{p}}}"]
            return out
        if isinstance(st, ast.For):
            if st.orelse or not isinstance(st.target, ast.Name):
                self.err(st, "for: single loop variable, no else")
            var = st.target.id
            if var in self.locals:
                self.err(st, f"loop variable {var} must be a new name")
            hdr, et = self.iter_header(st.iter, var)
            self.locals[var] = et
            body = self.block(st.body, ind + 1)
            del self.locals[var]  # the loop variable does not outlive the loop
            return [f"{p}{hdr} {{", f"{p}\t{_fl(et)}(1);"] + body + [f"{p}}}"]
        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
            t, c, ops = self.expr(st.value, effect_ok=True)
            return [f"{p}F({ops});", f"{p}{c};"]
        self.err(st, f"unsupported statement {type(st).__name__}")

    def assign(self, st, ind):
        p = "\t" * ind
        if isinstance(st, ast.Assign):
            if len(st.targets) != 1:
                self.err(st, "one target per assignment")
            target, value, op = st.targets[0], st.value, None
        elif isinstance(st, ast.AnnAssign):
            target, value, op = st.target, st.value, None
            if value is None:
                self.err(st, "declaration needs a value")
        else:
            target, value, op = st.target, st.value, st.op
        if not isinstance(target, ast.Name):
            self.err(st, "assign to a plain name only")
        name = target.id
        if name in CONSTANTS or name in PRIMS or name in self.g.genes:
            self.err(st, f"cannot assign to {name}")
        if name in dict(self.cur.params):
            self.err(st, f"cannot assign to parameter {name}")
        t, c, ops = self.expr(value)
        if name in self.g.keeps:
            if self.cur.name not in MEMORY_GENES:
                self.err(st, f"keep {name} can only be assigned in update() or after()")
            kt = self.g.keeps[name][0]
            t = self.coerce(st, t, kt)
            self.cur.keep_writes.add(name)
            lhs = f"K.{name}"
            cur_t = kt
        else:
            if name in self.locals:
                cur_t = self.locals[name]
                t = self.coerce(st, t, cur_t)
                lhs = name
            else:
                if op is not None:
                    self.err(st, f"{name} used before assignment")
                self.locals[name] = t
                self.decls.append((name, t))
                return [f"{p}F({ops + 1});", f"{p}{name} = {c};"]
        if op is not None:
            sym = _binop(op)
            if cur_t != "Num" or t != "Num" or sym is None:
                self.err(st, "augmented assignment on Num only (+= -= *= /=)")
            if sym in ("//", "%"):
                self.err(st, "use plain assignment for // and %")
            return [f"{p}F({ops + 2});", f"{p}{lhs} {sym}= {c};"]
        return [f"{p}F({ops + 1});", f"{p}{lhs} = {c};"]

    def iter_header(self, it, var):
        if isinstance(it, ast.Call) and getattr(it.func, "id", None) == "range":
            if len(it.args) != 1:
                self.err(it, "range(n) with one argument")
            t, c, _ = self.expr(it.args[0])
            self.need(it, t, "Num")
            return f"for (double {var} = 0, {var}_n = std::min(1e4, double({c})); {var} < {var}_n; {var} += 1)", "Num"
        t, c, _ = self.expr(it)
        if t not in ELEM:
            self.err(it, f"cannot iterate over {t}")
        if t == "Units":
            return f"for (const Unit& {var} : {c})", "Unit"
        return f"for (const Tile& {var} : X.tiles_of({c}))", "Tile"

    # ---- expressions
    def need(self, node, t, want):
        if t != want:
            self.err(node, f"expected {want}, got {t}")

    def coerce(self, node, t, want):
        if t == want:
            return t
        self.err(node, f"expected {want}, got {t}")

    def expr(self, e, effect_ok=False):
        if isinstance(e, ast.Constant):
            if isinstance(e.value, bool):
                return "Bool", "true" if e.value else "false", 0
            if isinstance(e.value, (int, float)):
                return "Num", repr(float(e.value)), 0
            self.err(e, f"unsupported constant {e.value!r}")
        if isinstance(e, ast.Name):
            n = e.id
            if n in self.locals:
                return self.locals[n], n, 0
            if n in self.g.keeps:
                self.cur.keep_reads.add(n)
                return self.g.keeps[n][0], f"K.{n}", 0
            if n in CONSTANTS:
                return "Num", repr(float(CONSTANTS[n])), 0
            if n in ("True", "False"):
                return "Bool", n.lower(), 0
            self.err(e, f"unknown name {n}")
        if isinstance(e, ast.BinOp):
            lt, lc, lo = self.expr(e.left)
            rt, rc, ro = self.expr(e.right)
            sym = _binop(e.op)
            if lt == rt == "Num" and sym:
                if sym == "/":
                    return "Num", f"div({lc}, {rc})", lo + ro + 1
                if sym == "//":
                    return "Num", f"std::floor(div({lc}, {rc}))", lo + ro + 2
                if sym == "%":
                    return "Num", f"fmod_pos({lc}, {rc})", lo + ro + 2
                return "Num", f"({lc} {sym} {rc})", lo + ro + 1
            if lt == rt == "Tiles" and sym in ("|", "&", "-"):
                fn = {"|": "tiles_or", "&": "tiles_and", "-": "tiles_minus"}[sym]
                return "Tiles", f"X.{fn}({lc}, {rc})", lo + ro + 1
            self.err(e, f"operator {sym} on {lt}, {rt}")
        if isinstance(e, ast.UnaryOp):
            t, c, o = self.expr(e.operand)
            if isinstance(e.op, ast.USub) and t == "Num":
                return "Num", f"(-{c})", o + 1
            if isinstance(e.op, ast.Not) and t == "Bool":
                return "Bool", f"(!{c})", o + 1
            self.err(e, "unary - on Num, not on Bool")
        if isinstance(e, ast.BoolOp):
            parts = [self.expr(v) for v in e.values]
            for (t, _, _), v in zip(parts, e.values):
                self.need(v, t, "Bool")
            sym = " && " if isinstance(e.op, ast.And) else " || "
            return "Bool", "(" + sym.join(c for _, c, _ in parts) + ")", sum(o for _, _, o in parts) + len(parts) - 1
        if isinstance(e, ast.Compare):
            terms = [self.expr(e.left)] + [self.expr(c) for c in e.comparators]
            out, ops = [], sum(o for _, _, o in terms)
            for i, op in enumerate(e.ops):
                (at, ac, _), (bt, bc, _) = terms[i], terms[i + 1]
                if isinstance(op, (ast.In, ast.NotIn)):
                    if at != "Tile" or bt != "Tiles":
                        self.err(e, "`in` tests a Tile in Tiles")
                    s = f"X.contains({bc}, {ac})"
                    out.append(s if isinstance(op, ast.In) else f"(!{s})")
                    ops += 1
                    continue
                sym = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!="}.get(type(op))
                if sym is None or at != bt:
                    self.err(e, f"cannot compare {at} and {bt}")
                if at != "Num" and sym not in ("==", "!="):
                    self.err(e, f"{sym} needs Num")
                if at in ("Tiles", "Units", "Field", "Option"):
                    self.err(e, f"cannot compare {at}")
                out.append(f"({ac} {sym} {bc})")
                ops += 1
            return "Bool", "(" + " && ".join(out) + ")", ops
        if isinstance(e, ast.IfExp):
            tt, tc, to = self.expr(e.test)
            self.need(e.test, tt, "Bool")
            at, ac, ao = self.expr(e.body)
            bt, bc, bo = self.expr(e.orelse)
            if at != bt:
                self.err(e, f"branches differ: {at} vs {bt}")
            return at, f"({tc} ? {ac} : {bc})", to + max(ao, bo) + 1
        if isinstance(e, ast.Attribute):
            t, c, o = self.expr(e.value)
            f = FIELDS.get(t, {}).get(e.attr)
            if f is None:
                self.err(e, f"{t} has no field {e.attr}")
            return f[0], f[1].format(c), o + 1
        if isinstance(e, ast.Call):
            return self.call(e, effect_ok)
        self.err(e, f"unsupported expression {type(e).__name__}")

    def call(self, e, effect_ok):
        if not isinstance(e.func, ast.Name):
            self.err(e, "call a gene or primitive by name")
        n = e.func.id
        if e.keywords and n not in ("max", "min"):
            self.err(e, f"{n}: no keyword arguments")
        if n in ("sum", "count", "any", "all", "max", "min") and len(e.args) == 1 and isinstance(e.args[0], ast.GeneratorExp):
            return self.reduce(n, e)
        if n in ("max", "min") and len(e.args) == 2 and not e.keywords:
            (at, ac, ao), (bt, bc, bo) = self.expr(e.args[0]), self.expr(e.args[1])
            self.need(e, at, "Num"), self.need(e, bt, "Num")
            return "Num", f"std::{n}({ac}, {bc})", ao + bo + 1
        if n == "best":
            return self.best(e)
        args = [self.expr(a) for a in e.args]
        ops = sum(o for _, _, o in args)
        if n in self.g.genes:
            gene = self.g.genes[n]
            if [t for _, t in gene.params] != [t for t, _, _ in args]:
                self.err(e, f"{n} takes ({', '.join(t for _, t in gene.params)})")
            if n in ("score", "update", "consider", "after", "reserve"):
                self.err(e, f"entry gene {n} cannot be called")
            self.cur.calls.add(n)
            return gene.ret, f"{n}(" + ", ".join(c for _, c, _ in args) + ")", ops + 1
        if n in PRIMS:
            if n in UNCALIBRATED and not os.environ.get("GENOME_UNCALIBRATED"):
                self.err(e, f"{n} is not calibrated yet (GENOME_UNCALIBRATED=1 for probes)")
            sig, ret, tpl = PRIMS[n]
            if list(sig) != [t for t, _, _ in args]:
                self.err(e, f"{n} takes ({', '.join(sig)})")
            if n in EFFECT_PRIMS:
                if not effect_ok or self.cur.name not in MEMORY_GENES:
                    self.err(e, f"{n} only as a statement in update() or after()")
            if n == "write_shared":
                off = e.args[0]
                self.cur.shared_writes.add(str(int(off.value)) if isinstance(off, ast.Constant) else "*")
            if n == "read_shared":
                off = e.args[0]
                self.cur.shared_reads.add(str(int(off.value)) if isinstance(off, ast.Constant) else "*")
            return ret, tpl.format(*[c for _, c, _ in args]), ops + 1
        self.err(e, f"unknown function {n}")

    def comp(self, gen):
        if len(gen.generators) != 1 or gen.generators[0].is_async or not isinstance(gen.generators[0].target, ast.Name):
            self.err(gen, "one `for x in S` per generator")
        c = gen.generators[0]
        var = c.target.id
        if var in self.locals:
            self.err(gen, f"generator variable {var} shadows a local")
        hdr, et = self.iter_header(c.iter, var)
        self.locals[var] = et
        conds = []
        cops = 0
        for cond in c.ifs:
            t, cc, o = self.expr(cond)
            self.need(cond, t, "Bool")
            conds.append(cc)
            cops += o
        return var, hdr, conds, cops

    def reduce(self, n, e):
        gen = e.args[0]
        var, hdr, conds, cops = self.comp(gen)
        et = self.locals[var]
        t, c, o = self.expr(gen.elt)
        del self.locals[var]
        guard = f"if (!({' && '.join(conds)})) continue; " if conds else ""
        per = 1 + cops + o
        if n == "sum":
            self.need(gen.elt, t, "Num")
            body = f"double acc = 0; {hdr} {{ {_fl(et)}({per}); {guard}acc += {c}; }} return acc;"
            rt = "Num"
        elif n == "count":
            self.need(gen.elt, t, "Bool")
            body = f"double acc = 0; {hdr} {{ {_fl(et)}({per}); {guard}if ({c}) acc += 1; }} return acc;"
            rt = "Num"
        elif n in ("any", "all"):
            self.need(gen.elt, t, "Bool")
            hit = "true" if n == "any" else "false"
            test = c if n == "any" else f"!({c})"
            body = f"{hdr} {{ {_fl(et)}({per}); {guard}if ({test}) return {hit}; }} return {'false' if n == 'any' else 'true'};"
            rt = "Bool"
        else:
            self.need(gen.elt, t, "Num")
            default = "0.0"
            for kw in e.keywords:
                if kw.arg != "default":
                    self.err(e, f"{n}: only default=")
                dt, dc, _ = self.expr(kw.value)
                self.need(kw.value, dt, "Num")
                default = dc
            cmp = ">" if n == "max" else "<"
            body = (f"bool seen = false; double acc = {default}; {hdr} {{ {_fl(et)}({per}); {guard}double v = {c}; "
                    f"if (!seen || v {cmp} acc) {{ acc = v; seen = true; }} }} return acc;")
            rt = "Num"
        return rt, f"[&]() {{ {body} }}()", 1

    def best(self, e):
        if len(e.args) != 2 or not isinstance(e.args[1], ast.Lambda) or len(e.args[1].args.args) != 1:
            self.err(e, "best(S, lambda x: score)")
        st, sc, so = self.expr(e.args[0])
        if st not in ELEM:
            self.err(e, f"best over {st}")
        et = ELEM[st]
        lam = e.args[1]
        var = lam.args.args[0].arg
        if var in self.locals:
            self.err(e, f"lambda variable {var} shadows a local")
        self.locals[var] = et
        t, c, o = self.expr(lam.body)
        del self.locals[var]
        self.need(lam.body, t, "Num")
        it = f"const Unit& {var} : {sc}" if et == "Unit" else f"const Tile& {var} : X.tiles_of({sc})"
        body = (f"{CPP[et]} arg{{}}; bool seen = false; double acc = 0; for ({it}) {{ {_fl(et)}({1 + o}); double v = {c}; "
                f"if (!seen || v > acc) {{ acc = v; arg = {var}; seen = true; }} }} return arg;")
        return et, f"[&]() {{ {body} }}()", so + 1


def _binop(op):
    return {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%",
            ast.BitOr: "|", ast.BitAnd: "&"}.get(type(op))


def _returns(stmts):
    """True if every path through stmts ends in a return."""
    for st in stmts:
        if isinstance(st, ast.Return):
            return True
        if isinstance(st, ast.If) and st.orelse and _returns(st.body) and _returns(st.orelse):
            return True
    return False


# ---------------------------------------------------------------- C++ output

def to_cpp(genome):
    ch = Checker(genome)
    ch.run()
    lines = ["// Generated by genome/lang.py; do not edit.", '#include "genome_rt.h"', "namespace genome_gen {",
             "using namespace genome;", "struct Keeps {"]
    for n, (t, v) in genome.keeps.items():
        init = DEFAULT[t]
        if v is not None:
            if t == "Num" and isinstance(v, (ast.Constant, ast.UnaryOp)):
                init = repr(float(ast.literal_eval(v)))
            elif t == "Bool" and isinstance(v, ast.Constant):
                init = "true" if v.value else "false"
            elif t in ("Tile", "Tiles", "Field") and not (isinstance(v, ast.Constant) and v.value is None):
                raise GenomeError(f"keep {n}: {t} keeps start empty (= None)")
        lines.append(f"\t{CPP[t]} {n} = {init};")
    lines += ["};", "struct Genes : GenesBase {", "\tKeeps K;", "\tusing GenesBase::GenesBase;"]
    order = list(genome.genes)
    # declarations first so genes can call each other in any order
    for n in order:
        g = genome.genes[n]
        params = ", ".join(_param(p, t) for p, t in g.params)
        lines.append(f"\t{CPP[g.ret]} {n}({params});")
    for n in order:
        g = genome.genes[n]
        if not g.params and g.ret != "None" and n not in ("update", "after"):
            lines.append(f"\tstd::uint64_t stamp_{n} = ~0ull; {CPP[g.ret]} val_{n}{{}};")
    lines += ["\tdouble score_option(const Option& o) override { return score(o); }",
              f"\tvoid run_update() override {{ {'update();' if 'update' in genome.genes else ''} }}",
              f"\tvoid run_after() override {{ {'after();' if 'after' in genome.genes else ''} }}"]
    if "reserve" in genome.genes:
        lines += ["\tdouble reserve_fuel() override { return reserve(); }"]
    if "consider" in genome.genes:
        p = genome.genes["consider"].params[0][0]
        lines += ["\tbool consider_kind(int k) override { return consider(double(k)); }",
                  "\tbool has_consider() const override { return true; }"]
    lines += ["};"]
    for n in order:
        g = genome.genes[n]
        params = ", ".join(_param(p, t) for p, t in g.params)
        lines.append(f"// gene {_comment(g.id)}: {_comment(g.desc)}")
        body = ch.cpp[n]
        memo = not g.params and g.ret not in ("None",) and n not in ("update", "after")
        lines.append(f"{CPP[g.ret]} Genes::{n}({params}) {{")
        lines.append(f"\tGENE_PROF({order.index(n)}, \"{n}\");")
        if memo:
            # zero-argument genes are pure within a pass: computed once per pass, cached on this instance
            # a hit costs ~73 fuel in the bot for a scalar, ~78 for a shared set or field (fitted per turn on identical games)
            hit = 78 if g.ret in ("Tiles", "Field", "Units") else 73
            lines += [f"\tif (stamp_{n} == X.pass_id) {{ FX({hit}); return val_{n}; }}",
                      f"\t{CPP[g.ret]} v = [&]() -> {CPP[g.ret]} {{"]
            lines += ["\t" + l for l in body]
            lines += ["\t}();", f"\tstamp_{n} = X.pass_id; val_{n} = v;", "\treturn v;"]
        else:
            lines += body
        lines.append("}")
    lines += ["} // namespace genome_gen", "", "extern \"C\" genome::GenesBase* genome_make(genome::Ctx& X) "
              "{ return new genome_gen::Genes(X); }",
              "// the runtime layout this genome was compiled against (genome_eval refuses a mismatch)",
              "extern \"C\" unsigned long genome_ctx_size() { return sizeof(genome::Ctx); }", ""]
    return "\n".join(lines)


def _fl(et):
    """Loop-iteration charge macro: iterating units costs ~11 more per step in the bot than a range or tiles."""
    return "FLU" if et == "Unit" else "FL"


def _param(name, t):
    """Scalars by value, everything else by const reference (copies cost ~1 fuel per byte in the bot)."""
    return f"{CPP[t]} {name}" if t in ("Num", "Bool", "Tile") else f"const {CPP[t]}& {name}"


def summary(genome):
    return {"genes": [{"id": g.id, "name": g.name, "desc": g.desc, "parents": g.parents,
                       "calls": sorted(g.calls)} for g in genome.genes.values()],
            "edges": genome.edges(), "keeps": sorted(genome.keeps)}


if __name__ == "__main__":
    import sys
    gm = parse(open(sys.argv[1]).read())
    if len(sys.argv) > 2:
        open(sys.argv[2], "w").write(to_cpp(gm))
    print(json.dumps(summary(gm), indent=1))
