"""Claude proposer: asks for an improved policy; tracks spend against a hard budget."""
import os
import re
import threading

import anthropic

from policygen.blocks import REGISTRY

from .catalog import DOCS, GAME, GAME_BASE, GRAMMAR, block_catalog

# $ per million tokens (input, output). Cache reads/writes priced relative to input.
PRICES = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-opus-5-5": (4.00, 20.00),
}
CACHE_READ, CACHE_WRITE = 0.1, 1.25

SYSTEM = f"""You improve bot policies for a programming competition, written in a small typed language.

# The game
{GAME}
# The policy language
{GRAMMAR}
# Blocks (signature -> return type)
{block_catalog()}

# Already in the current best (do not re-add; improve on them only with a new idea)
Retreat toward spawn below 30% health while in_danger() and recall once clear; skip monoliths and
golems; Treasure then Jungle shards; a fixed draft order; tribute with 25+ gem bags (or when hurt or
late); walk off dead camps of uncleared groups; ability-type-aware casting; monolith fallback only on
maps whose only gems are monoliths. Constant tuning around these is exhausted (see Observations).

# Your task
You are shown earlier policy versions, worst first, with their scores (win rate against the
reference bots, plus a small bonus for gem margin; higher is better), its win rate and gems against
each reference bot (weak matchups show where to improve) and, if any, how many turns per game its
champions ran out of fuel (each one is a lost turn). Write one new version that
should score higher. Make a focused, meaningful change: a better rule, a missing behaviour, a
better threshold, or a cheaper way to do the same thing. Keep everything that already works.
Reply with the complete new policy in a single ```policy code block, then nothing else."""


# ---- exploration mode (--explore): the prompt varies per call; each child logs its variant ----
_EXPLORE_HEAD = "You write bot policies for a programming competition, in a small typed language.\n\n# The game\n"
_EXPLORE_TAIL = f"""
# The policy language
{GRAMMAR}
# Blocks (signature -> return type)
{block_catalog()}
"""
EXPLORE_SYSTEM = {"full": _EXPLORE_HEAD + GAME + _EXPLORE_TAIL, "lean": _EXPLORE_HEAD + GAME_BASE + _EXPLORE_TAIL}

AXES = {
    "draft": "the DRAFT. Measured: our bots have never picked prism, heart_of_ruin, marcella, cassi_issac, stellar, "
             "willow or varg; top teams draft heart_of_ruin, prism and ryth as focus carries. Levers: the pick order, "
             "the composition, and the play each champion gets",
    "items": "ITEMS AND STATS. Measured: top teams stack one stat per carry (strength on vesper_vale, 235 per basic "
             "by round 192; focus on heart_of_ruin, prism and ryth). Levers: what each champion buys and when, the "
             "emblem family, focus vs strength vs health, teleport crystals, altar locks",
    "vision": "VISION. Measured: the free ward on the nearest altar when within 3 (place_ward; it recharges over 10 "
              "turns) scored +4 points vs a hunter; vision is not shared between champions. Levers: wards, bushes, "
              "fog, the enemy's vision",
    "teleport": "MOBILITY. Levers: teleport crystals (buy_teleport, teleport_to), dashes, recall timing (damage "
                "cancels a recall)",
    "team": "TEAM COORDINATION. Measured: shared memory has 8 bytes; 0-6 hold claims and the team target, byte 7 "
            "bits 0-1 hold the lock flags and bits 2-7 are free (floor(v / 4)). Levers: write_shared / read_shared, "
            "claims, set_team_target, grouping, splitting the map",
    "roles": "PER-CHAMPION ROLES. Measured: the live bot runs one shared behaviour for all champions. Levers: "
             "i_am(champ_vesper_vale()) etc., the job each champion has (carry, farmer, hunter, altar guard, "
             "monolith taker)",
    "pairs": "PAIRS. Measured: 71% of our deaths are 2-vs-1; before round 150, 89% are 2+ of theirs vs 1 of ours. "
             "Measured hand rules: retreating to an ally instead of spawn doubled deaths; walking to allies when "
             "outnumbered cost 10 points. Ranked, v21 lost 0-5 to a pack team of similar rating (Ren, Stellar, Varg, Tavi, Ryth): "
             "80% of our deaths were outnumbered by 2+, 20.4 deaths a game to their 8.4. Vision is not shared; byte 7 bits 2-7 of shared memory are free for a "
             "beacon (bits 0-1 are the lock flags: v = read_shared(7), beacon = floor(v / 4), write_shared(7, 4 * b "
             "+ (v - 4 * floor(v / 4)))). Levers: partners (i_am), which camp groups each takes (claim, claim_count, "
             "claimed_by_allies), distance between allies while farming, signals",
    "conversion": "GEM CONVERSION, the biggest measured gap to the band above us (docs/GAP_LIST.md). Measured: we "
                  "lose 184 gems per game on death; 54% of our deaths happen while carrying gems, a median 7 tiles "
                  "from an altar; we submit 76% of the gems we capture (they 99%); we bank 18 times a game (they "
                  "26). Ranked, v21 is 30-35 and lost 0-5 to a lower-rated team in three close gem races: gems per capture 8.8 "
                  "vs their 12.9, tributes 17 vs 25 per game, and 4.4 of our deaths per game to camps. Close games are "
                  "decided by capture yield and conversion, blowouts by pack fights. Across all 75 ranked losses of the "
                  "live bot: low capture yield (our gems per capture under 70% of theirs) in 59%, fights in 51%, 250+ "
                  "gems lost on death in 35%, a slow start in 32%, monolith deaths in 19%, no bank in 13%. On "
                  "00lost_world the bot takes the nearest spawn (single gems, gold-only groups) instead of the gemx3 / "
                  "gemx2 groups: about 350 vs 1000 gems. Levers: when and where gems are banked, bag size, the distance to an altar, routes while "
                  "carrying, which camp groups are taken, what happens to the bag when a fight starts, which camps are hit and with how many champions (gems per capture), "
                  "camp HP vs our HP, group_rate(spawn tile) and group_gems when choosing a camp group",
    "disengage": "LOW-HP SURVIVAL. Measured: once one of our champions is below 50% HP with an enemy within 5 it "
                 "dies 88% of the time (the top team 6%, similar teams 13-20%), gaining ~1 tile in 5 rounds. "
                 "Measured hand rules: walking away mid-fight at HP below 0.4-0.6 with an enemy within 5-6 scored "
                 "18-34% vs the live bot, with more deaths. Ranked, v21 lost 0-5 to a pack team of similar rating "
                 "(Ren, Stellar, Varg, Tavi, Ryth): 89% of our deaths had 2+ of theirs within 5, 80% were outnumbered "
                 "by 2+, and we died 20.4 times a game to their 8.4. Levers: which fights are entered, local numbers and "
                 "strength, range, movement and dashes, recall timing (damage cancels a recall), allies' help",
    "fuel": "FUEL COST PER TURN. Measured on hyb5-g3 #76 and #82 (teleport crystal and altar dashes "
            "for gem carriers; fuel_turns --enforce --bot-seeds on 01big-world and 00ambush, both sides, vs v21): #76 6 "
            "suspensions and 43 turns at 90k or more per game, #82 10.8 and 91, v21 0 and 5 (a champion turn over 100k "
            "fuel suspends it). The most expensive blocks there: and/or chains, minus(TileSet), closest(TileSet), "
            "filter over unit lists and tile sets, respawning_visible_spawns and capturable_spawns. A suspended "
            "turn is a champion that does nothing that turn. Levers: keep (computed once a game), let (once a "
            "turn), fuel_remaining(), which branches call the costly blocks and how often, the size of the sets they scan",
    "macro": "MACRO ROUTE AND TIMING. Measured: we bank 18 times a game (top teams 26). 98% of our monolith deaths "
             "on great_wall are self-inflicted: the live bot's first(filter(camps, in_attack_range())) hits monoliths "
             "at the altar ring (01shortcut's altar-blocker branch does the same); monolith deaths are in 19% of our "
             "ranked losses. Levers: which camps when, "
             "monolith takes (claim_count), when to bank, where to stand between fights, early vs late game plans",
    "abilities": "ABILITIES. Measured: top teams open with an ability on the first-hit turn. Levers: AoE at tiles "
                 "(cast_at_tile), stuns, resets after a basic (slot_is_reset), slot_stun / slot_range / "
                 "slot_radius, shields and heals on allies",
    "combat": "COMBAT MICRO. Measured: top teams engage at HP 0.9+, usually 2v1, target the closest visible enemy, "
              "leave around 0.8 HP and die 1.6 times a game; 34% of our dying champions were hitting a camp while "
              "the killer was visible for 5 rounds. Levers: the first hit, focus on one target, range, kiting, "
              "dashes, what a champion does the turn it is hit",
}
TOP_RULES = [
    "Top teams engage healthy (HP 0.9+) and usually 2v1; they leave around 0.8 HP and die 1.6 times a game.",
    "Top teams target the closest visible enemy and open with an ability on the first-hit turn.",
    "Before round 150, 89% of our deaths are 2+ of theirs vs 1 of ours: they arrive together.",
    "34% of our dying champions were hitting a camp while the killer was visible for 5 rounds.",
    "Our melee champions hit from range 2-4 often stand still that turn; top teams dash in or walk out.",
    "Top teams stack one stat per carry: strength on Vesper Vale (235 per basic by round 192), focus on "
    "Heart of Ruin, Prism and Ryth.",
    "Top teams bank big bags (median 57) only when no enemy is within 8 tiles; they tribute at once when one is.",
    "One top team casts recall after every action, every round (a free auto-escape when hit).",
]
# Newest blocks, listed by the "new vocabulary" variant (only those in the registry are shown).
NEW_BLOCKS = ["unit_max_health", "unit_strength", "unit_focus", "enemies_near", "allies_near", "strength_at",
              "unit_tributing", "unit_is", "unit_shield", "slot_stun", "slot_range", "slot_radius",
              "threat_eta", "altar_eta", "retreat_eta", "enemy_between", "group_contested", "team_gems",
              "unseen_enemies_near", "bank_detour", "group_rate",
              "monolith_threat", "in_monolith_zone", "altar_safe_tiles", "camp_threat"]
RARE_BLOCKS = ["place_ward", "bushes", "cast_at_tile", "teleport_to", "buy_teleport", "write_draft", "walls",
               "holes", "focus", "random_stat", "unit_health", "camp_count", "read_shared", "write_shared",
               "slot_is_reset", "stat_focus", "gold_cluster_tiles", "group_gems", "claim_count", "slot_stun",
               "slot_radius", "buy_altar_lock", "place_altar_lock", "set_priority"]
CHANGE_TYPES = {
    "edit": "Make one focused change on that axis to the latest version, keeping everything else.",
    "plan": "First write a short plan (3-6 lines, as # comments at the top of the policy) for how to "
            "exploit that axis, then implement it in the latest version.",
    "rewrite": "Write a NEW policy from scratch with a different overall plan built around that axis. "
               "You may reuse ideas from the versions shown, not their code. Start with a short plan as # "
               "comments.",
}
FRAMINGS = {
    "captain": "Think as the team captain: write per-champion roles (i_am(champ_heart_of_ruin()) etc.) that work together.",
    "champion": "Think as one champion: what should a single champion do turn by turn to win its fights and farm.",
}


def sample_variant(rng, n_parents, change_weights=(0.55, 0.3, 0.15), axes=None, vocab_share=0.2):
    """One prompt variant for an exploration call. change_weights: edit, plan, rewrite; axes: the axis menu, a
    list of names or {name: weight} (default all of AXES, equal weights); vocab_share: the share of calls that
    list the newest blocks (NEW_BLOCKS)."""
    change = rng.choices(list(CHANGE_TYPES), change_weights)[0]
    menu = axes if isinstance(axes, dict) else {a: 1.0 for a in (axes or AXES)}
    return {
        "axis": rng.choices(list(menu), list(menu.values()))[0],
        "change": change,
        "framing": rng.choice(list(FRAMINGS)),
        "catalog": rng.choice(["full", "lean"]),
        "evidence": rng.choice(["worst", "rule", "block", "none"]),
        "parents": "crossover" if n_parents >= 2 and change != "rewrite" and rng.random() < 0.3 else "single",
        "vocab": rng.random() < vocab_share,
    }


def _evidence(kind, parent_metrics, rng):
    if kind == "worst":
        per = {k: m for k, m in (parent_metrics or {}).items() if isinstance(m, dict) and "win_rate" in m}
        if per:
            k, m = min(per.items(), key=lambda kv: kv[1]["win_rate"])
            extra = ""
            if "kills" in m:
                extra = (f", kills {m['kills'][0]:.1f} vs {m['kills'][1]:.1f}, deaths {m['deaths'][0]:.1f} vs "
                         f"{m['deaths'][1]:.1f}, damage to champions {m['champ_damage'][0]:.0f} vs "
                         f"{m['champ_damage'][1]:.0f} per game")
            return (f"Weakest matchup of the latest version: vs {k}, win rate {m['win_rate']:.0%}, gems "
                    f"{m['a_gems']:.0f}-{m['b_gems']:.0f}{extra}.")
    if kind == "rule":
        return "Observed in the ladder's top teams: " + rng.choice(TOP_RULES)
    if kind == "block":
        b = rng.choice(RARE_BLOCKS)
        return f"Try something with the block {b} (almost never used so far): {DOCS.get(b, 'see the block list')}"
    return ""


def explore_user(parents, variant, rng):
    """User message for an exploration call. parents: (text, score, metrics), worst first."""
    def per_line(metrics):
        per = {k: m for k, m in (metrics or {}).items() if isinstance(m, dict) and "win_rate" in m}
        return ", ".join(f"vs {k} {m['win_rate']:.0%}" for k, m in per.items())
    shown = parents if variant["parents"] == "crossover" else parents[-1:]
    parts = []
    for i, (text, score, metrics) in enumerate(shown):
        code = "" if variant["change"] == "rewrite" else f"\n```policy\n{text.strip()}\n```"
        parts.append(f"## Version {i} (score {score:.3f}; {per_line(metrics)}){code}")
    task = [f"Your change must be about {AXES[variant['axis']]}.", CHANGE_TYPES[variant["change"]],
            FRAMINGS[variant["framing"]]]
    picks = list(dict.fromkeys(re.findall(r"pick\(\s*champ_(\w+)\(\)\s*\)", shown[-1][0])))
    if picks:
        task.append("The latest version drafts, in this order when available: " + ", ".join(picks[:5]) +
                    (" (then: " + ", ".join(picks[5:]) + ")" if picks[5:] else "") +
                    ". Code for other champions never runs, so don't spend the change on it.")
    task.append("Keep the existing comments. The # lines at the very top are the lineage header: keep them "
                "unchanged and add one line at their end describing your change.")
    if variant.get("vocab"):
        known = {b.name for b in REGISTRY}
        new = [b for b in NEW_BLOCKS if b in known and b in DOCS]
        if new:
            task.append("Newest blocks in the language:\n" +
                        "\n".join(f"- {b}: {DOCS[b]}" for b in new) +
                        "\nUse at least one of them where it informs a decision.")
    if variant["parents"] == "crossover":
        task.append("The versions above come from different lines of play: combine their strengths into one policy.")
    ev = _evidence(variant["evidence"], shown[-1][2], rng)
    if ev:
        task.append(ev)
    task.append("Scores are win rate against reference bots plus a small gem-margin bonus. A new idea may "
                "start weaker; that is fine, but the policy must be valid. Reply with the complete policy "
                "in a single ```policy code block, then nothing else.")
    return "\n\n".join(parts) + "\n\n## Your task\n" + "\n".join(task)


class BudgetExceeded(Exception):
    pass


class Proposer:
    def __init__(self, budget_usd, opus_every=10, max_tokens=16000, helpers=""):
        # The cloud environment reserves ANTHROPIC_API_KEY for Claude Code's own login and does not
        # pass it to processes, so the key is stored as FUNSEARCH_ANTHROPIC_KEY (or FUNSEARCH_API_KEY) there. It may also
        # point ANTHROPIC_BASE_URL at Claude Code's endpoint, so the API URL is pinned.
        self.client = anthropic.Anthropic(
            api_key=(os.environ.get("FUNSEARCH_ANTHROPIC_KEY") or os.environ.get("FUNSEARCH_API_KEY")
                     or os.environ.get("ANTHROPIC_API_KEY")),
            base_url=os.environ.get("FUNSEARCH_BASE_URL", "https://api.anthropic.com"))
        self.budget = budget_usd
        self.spent = 0.0
        self.calls = 0
        self.opus_every = opus_every
        self.max_tokens = max_tokens
        self.lock = threading.Lock()
        # shared helper library section (funsearch.helpers.prompt_section), appended to the cached system prompt
        self.helpers = helpers

    def _model(self):
        with self.lock:
            self.calls += 1
            n = self.calls
        return "claude-opus-5-5" if self.opus_every and n % self.opus_every == 0 else "claude-haiku-5-5"

    def _cost(self, model, usage):
        pin, pout = PRICES[model]
        tokens_in = (usage.input_tokens
                     + CACHE_READ * (usage.cache_read_input_tokens or 0)
                     + CACHE_WRITE * (usage.cache_creation_input_tokens or 0))
        return (tokens_in * pin + usage.output_tokens * pout) / 1e6

    def propose(self, parents, variant=None, rng=None):
        """parents: list of (text, score, metrics), worst first; metrics holds per-opponent stats. With a
        variant (exploration), the prompt follows it. Returns (policy text or None, model, cost, proposals)."""
        with self.lock:
            if self.spent >= self.budget:
                raise BudgetExceeded(f"spent ${self.spent:.2f} of ${self.budget:.2f}")
        model = self._model()
        if variant is not None and variant["change"] == "rewrite":
            model = "claude-opus-5-5"
        def header(i, score, metrics):
            per = {k: m for k, m in (metrics or {}).items() if isinstance(m, dict) and "win_rate" in m}
            lines = [f"## Version {i} (score {score:.3f})"]
            if per:
                lines.append("Win rate (your gems - their gems per game): " + ", ".join(
                    f"vs {k} {m['win_rate']:.0%} ({m['a_gems']:.0f}-{m['b_gems']:.0f})" for k, m in per.items()))
                susp = sum(m.get("a_suspensions", 0) for m in per.values()) / len(per)
                if susp >= 1:
                    lines.append(f"Out of fuel {susp:.0f} turns per game.")
            return "\n".join(lines)
        shown = "\n\n".join(
            f"{header(i, score, metrics)}\n```policy\n{text.strip()}\n```"
            for i, (text, score, metrics) in enumerate(parents))
        user = f"{shown}\n\n## Version {len(parents)}\nWrite it."
        system = SYSTEM
        if variant is not None:
            import random as _random
            user = explore_user(parents, variant, rng or _random.Random())
            system = EXPLORE_SYSTEM[variant["catalog"]]
        if self.helpers:
            system = system + "\n" + self.helpers
        kwargs = dict(
            model=model,
            max_tokens=self.max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        if model == "claude-opus-5-5":
            # server-side refusal fallback (opt-in default for this model)
            response = self.client.beta.messages.create(
                **kwargs, betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        else:
            response = self.client.messages.create(**kwargs)
        cost = self._cost(model, response.usage)
        with self.lock:
            self.spent += cost
        if response.stop_reason == "refusal":
            return None, model, cost, []
        text = "".join(b.text for b in response.content if b.type == "text")
        m = re.search(r"```policy\n(.*?)```", text, re.S)
        # block proposals may sit inside or outside the code block
        proposals = [x.strip() for x in re.findall(r"#\s*PROPOSE:\s*(.+)", text)]
        return (m.group(1) if m else None), model, cost, list(dict.fromkeys(proposals))
