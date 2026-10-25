"""The A1 link mutation of prompt experiment 1 (arenaa/prompts/mutate_link_v1.md) as an arena operator (arenaZ-4).

One call link per child, drawn among links whose callee is not a trivial wrapper (promptexp.eligible_links; if a genome
has none, any link from the score gene); the mutation type T1-T5 drawn with equal probability; the minimal system and
typed explicit Task (promptexp.A1_SYSTEM / a1_user); the type's check with one retry (the check's message appended,
single-turn), then the child counts as rejected. The model is the arena's usual choice (Haiku, Opus every Nth call).
"""
from .. import lang
from . import edit, operators
from .promptexp import A1_SYSTEM, TYPES, a1_user, eligible_links, type_check


def links_for(src):
    links = eligible_links(src)
    if links:
        return links, "eligible"
    g = lang.parse(src)
    return sorted((a, b) for a, b, kind in g.edges() if kind == "call" and a == "score" and b != a), "score-fallback"


def mutate(parent_src, claude, rng, prefix):
    genome = lang.parse(parent_src)
    links, pool = links_for(parent_src)
    if not links:
        return operators.Child(None, "mutate", "no call link to mutate", {"a1": True, "link_pool": pool})
    a, b = rng.choice(links)
    t = rng.choice(TYPES)
    a_id, b_id = genome.genes[a].id, genome.genes[b].id
    log = {"a1": True, "edges": [[a, b, "call"]], "n_edges": 1, "editable": sorted({a_id, b_id}), "type": t,
           "link_pool": pool, "check": [], "llm": []}
    user = a1_user(parent_src, a, b, t)
    cost, model = 0.0, ""
    for attempt in range(2):
        text, model, c, info = claude.ask([A1_SYSTEM], user)
        cost += c
        log["llm"].append(info)
        log["retried"] = attempt > 0
        if text is None:
            return operators.Child(None, "mutate", "refusal", log, model, cost)
        try:
            child, stats = operators.apply_mutation(parent_src, text, {a_id, b_id}, prefix)
        except (edit.EditError, lang.GenomeError) as e:
            log["reply"] = text[-6000:]
            return operators.Child(None, "mutate", f"{type(e).__name__}: {e}", log, model, cost)
        why = type_check(t, parent_src, child, a_id, b_id)
        log["check"].append(why or "ok")
        if why is None:
            log.update(stats)
            log["b_changed"] = b_id in stats["genes_changed"]
            return operators.Child(child, "mutate", None, log, model, cost)
        log["reply"] = text[-6000:]
        user = f"{user}\n\n# Your previous reply\n{text.strip()}\n\nIt was rejected: {why}.\nReply again, following the rules above."
    return operators.Child(None, "mutate", f"type check: {why}", log, model, cost)
