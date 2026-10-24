"""Claude proposer: asks for an improved policy; tracks spend against a hard budget."""
import os
import re
import threading

import anthropic

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
    "draft": "the DRAFT: a different champion composition, including champions our bots never pick (prism, "
             "heart_of_ruin, marcella, cassi_issac, stellar, willow, varg), and play that suits it",
    "items": "ITEMS AND STATS: what each champion buys and when (other emblem families, focus vs strength vs "
             "health per champion, stacking one stat on a carry, teleport crystals, altar locks)",
    "vision": "VISION: wards (place_ward), bushes, fighting from or around fog, denying the enemy's vision. A "
              "measured start: the free ward on the nearest altar when within 3 (let a = first( filter( altars(), "
              "within(3, position()) ) ), then place_ward(a); it recharges over 10 turns) was +4 points vs a hunter",
    "teleport": "MOBILITY: teleport crystals (buy_teleport, teleport_to), dashes, recall timing",
    "team": "TEAM COORDINATION through shared memory (write_shared / read_shared byte 7, bits 2-7 only: bits 0-1 are the lock flags; claims, "
            "set_team_target): roles, grouping, calling targets, splitting the map",
    "roles": "PER-CHAMPION ROLES: give champions different jobs by i_am(champ_vesper_vale()) etc. (carry, farmer, hunter, "
             "altar guard, monolith taker) instead of one shared behaviour",
    "pairs": "PAIRS: keep farming but never alone (71% of our deaths are 2-vs-1). Make two-champion pairs: give "
             "each champion a partner by i_am(champ_vendetta()) etc. (e.g. vendetta with vesper_vale, tavi with ryth), have "
             "partners farm neighbouring camp groups (claim / claim_count / claimed_by_allies tell which groups "
             "your partner took), and converge when either sees an enemy. Vision is not shared, so signal it: "
             "shared memory has 8 bytes and only byte 7 is free (0-6 are claims and the team target), and bits 0-1 "
             "of byte 7 are the live bot's lock flags: keep them. Put a beacon in bits 2-7, e.g. let v = "
             "read_shared(7), beacon = floor(v / 4), write_shared(7, 4 * b + (v - 4 * floor(v / 4))) for a new "
             "beacon b (0-63), e.g. which pair is in a fight. Retreating "
             "to an ally instead of spawn doubled deaths and walking to allies when outnumbered cost 10 points in "
             "tests, so stay close WHILE farming rather than walking across the map to regroup",
    "conversion": "GEM CONVERSION (the biggest measured gap to the band above us, docs/GAP_LIST.md): we lose 184 "
                  "gems per game on death, 54% of our deaths happen while carrying gems (a median 7 tiles from an "
                  "altar), we submit 76% of the gems we capture (they 99%), and we bank 18 times a game (they 26). "
                  "Work on bank cadence, bag size against the distance to the nearest safe altar (gems(), "
                  "closest(safe altars), distance), carrying routes that avoid enemies (in_danger(), enemies_within), "
                  "tributing before a fight, and taking richer camp groups closer to altars",
    "disengage": "DISENGAGE, i.e. not being caught in losing fights at low HP: once one of our champions is "
                 "below 50% HP with an enemy within 5 it dies 88% of the time (the top team 6%, similar teams "
                 "13-20%). MEASURED: walking away mid-fight (HP below 0.4-0.6 with an enemy within 5-6) is strongly "
                 "NEGATIVE (18-34% vs the live bot, more deaths: a fleeing champion takes free hits). So avoid the "
                 "losing fight instead of fleeing it: engage only with local numbers or strength ahead "
                 "(enemies_within, allies_within, local_strength), keep range, back off BEFORE the first exchange "
                 "when outnumbered, never start a recall within reach of an enemy (damage cancels it), and let a "
                 "healthy ally peel for a hurt one",
    "macro": "MACRO ROUTE AND TIMING: which camps when, monolith takes with claim_count, when to bank, "
             "where to stand between fights, early vs late game plans",
    "abilities": "ABILITIES: AoE at tiles (cast_at_tile), stun before burst, reset after a basic, using "
                 "slot_stun / slot_range / slot_radius, shields and heals on allies",
    "combat": "COMBAT MICRO: landing the first hit, 2v1 focus on the same turn, kiting at max range, "
              "retreat and re-engage, never idling when hit",
}
TOP_RULES = [
    "Top teams engage healthy (HP 0.9+) and usually 2v1; they leave around 0.8 HP and die 1.6 times a game.",
    "Top teams target the closest visible enemy and open with an ability on the first-hit turn.",
    "Before round 150, 89% of our deaths are 2+ of theirs vs 1 of ours: they arrive together.",
    "34% of our dying champions were hitting a camp while the killer was visible for 5 rounds.",
    "A melee champion hit from range 2-4 must dash in or walk out that turn, never idle.",
    "Top teams stack one stat per carry: strength on Vesper Vale (235 per basic by round 192), focus on "
    "Heart of Ruin, Prism and Ryth.",
    "Top teams bank big bags (median 57) only when no enemy is within 8 tiles; tribute at once when one is.",
    "One top team casts recall after every action, every round (a free auto-escape when hit).",
]
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


def sample_variant(rng, n_parents, change_weights=(0.55, 0.3, 0.15), axes=None):
    """One prompt variant for an exploration call. change_weights: edit, plan, rewrite; axes: the axis menu, a
    list of names or {name: weight} (default all of AXES, equal weights)."""
    change = rng.choices(list(CHANGE_TYPES), change_weights)[0]
    menu = axes if isinstance(axes, dict) else {a: 1.0 for a in (axes or AXES)}
    return {
        "axis": rng.choices(list(menu), list(menu.values()))[0],
        "change": change,
        "framing": rng.choice(list(FRAMINGS)),
        "catalog": rng.choice(["full", "lean"]),
        "evidence": rng.choice(["worst", "rule", "block", "none"]),
        "parents": "crossover" if n_parents >= 2 and change != "rewrite" and rng.random() < 0.3 else "single",
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
                    f"{m['a_gems']:.0f}-{m['b_gems']:.0f}{extra}. Make the change help here.")
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
    def __init__(self, budget_usd, opus_every=10, max_tokens=16000, directive="", helpers=""):
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
        self.directive = directive  # per-run style directive, sent after the versions (system prompt stays cached)
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
        user = f"{shown}\n\n"
        if self.directive:
            user += f"## Style directive for this run (overrides the usual advice where they conflict)\n{self.directive.strip()}\n\n"
        user += f"## Version {len(parents)}\nWrite it."
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
