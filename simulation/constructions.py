"""Exact checks of the two constructions in the text, in a free domain where a program's output is the
concatenation of its tokens' primitive expansions, so two programs are equivalent exactly when their
expansions are equal. Search is breadth-first in length-lexicographic order with unit cost per
candidate; compression and the discovery loop follow engine.py.
"""
from __future__ import annotations

from engine import gain, pattern_stats, rewrite

SIGMA = 4


def search(lib, targets, budget):
    """lib: list of expansions (tuples of primitives). Returns {target index: (cost, program)} for the
    targets reached within the budget (number of candidates)."""
    n = len(lib)
    want = {t: i for i, t in enumerate(targets)}
    found, count, level = {}, 0, [((), ())]
    while level and count < budget and len(found) < len(targets):
        nxt = []
        for prog, exp in level:
            for t in range(n):
                count += 1
                if count > budget:
                    break
                p, e = prog + (t,), exp + lib[t]
                i = want.get(e)
                if i is not None and i not in found:
                    found[i] = (count, p)
                nxt.append((p, e))
            if count > budget:
                break
        level = nxt
    return found


def compress(lib, progs, fams, picks=2, kmax=3, min_families=1):
    lib, progs, new, total = list(lib), [list(p) for p in progs], [], 0
    for _ in range(picks):
        counts, famset = pattern_stats(progs, fams, kmax)
        cands = sorted(((gain(p, c), len(p), p) for p, c in counts.items()
                        if c >= 2 and gain(p, c) > 0 and len(famset[p]) >= min_families), key=lambda z: (-z[0], -z[1], z[2]))
        chosen = None
        for g, _, pat in cands:
            exp = tuple(x for t in pat for x in lib[t])
            if exp not in lib:
                chosen = (g, pat, exp)
                break
        if chosen is None:
            break
        g, pat, exp = chosen
        lib.append(exp)
        progs = [rewrite(p, pat, len(lib) - 1) for p in progs]
        new.append(exp)
        total += g
    return new, total


def discover(lib, tasks, fams, budget, rounds=3):
    learned, first = [], None
    cur = list(lib)
    for r in range(rounds):
        f = search(cur, tasks, budget)
        progs = [f[i][1] for i in sorted(f)]
        pf = [fams[i] for i in sorted(f)]
        if r == 0:
            first = (set(f), progs, pf)
        new, _ = compress(cur, progs, pf)
        if not new:
            break
        cur += new
        learned += new
    return learned, first


def share(lib, tasks, budget):
    return len(search(lib, tasks, budget)) / len(tasks)


def evaluate(a, history, disc, dfam, test, budget_disc, budget_eval):
    base = [(i,) for i in range(SIGMA)]
    hist_tok = [list(h) for h in history]
    counts, _ = pattern_stats(hist_tok, [0] * len(hist_tok), len(a))
    comp = gain(a, counts.get(a, 0))
    K0, f0 = discover(base, disc, dfam, budget_disc)
    K1, f1 = discover(base + [a], disc, dfam, budget_disc)
    u_no = share(base + K0, test, budget_eval)
    u_late = share(base + [a] + K0, test, budget_eval)
    u_early = share(base + [a] + K1, test, budget_eval)
    _, fc = compress(base + [a], f1[1], f1[2], min_families=2)
    return {"comp": comp, "freq": counts.get(a, 0), "gain": len(f1[0] - f0[0]), "fc": fc,
            "v_direct": u_late - u_no, "v_disc": u_early - u_late, "K1": [list(k) for k in K1]}


def separation():
    """Two abstractions matched on compression, frequency, direct value, first-round frontier gain and
    frontier compression, whose discovery values differ: later demands reuse a pair of copies of a but
    not of a2."""
    a, a2 = (0, 1, 2), (3, 2, 1)
    flip = lambda s: tuple(3 - x for x in s)
    history = [a + (3,), a2 + (0,), a + a2, a2 + a]
    disc = [a + a + (y,) for y in range(4)] + [flip(a + a + (y,)) for y in range(4)]
    dfam = [0] * 4 + [1] * 4
    test = [(y,) + a + a for y in range(4)] + [flip((y,) + a + a) for y in range(4)] + [a * 4 + (y,) for y in range(4)]
    B = 500
    return {"budget": B, "a": evaluate(a, history, disc, dfam, test, B, B), "a2": evaluate(a2, history, disc, dfam, test, B, B),
            "n_test": len(test)}


def reversal():
    """Two abstractions whose order by discovery value reverses when the discovery budget falls from
    1000 to 200 candidates (a fivefold rise in verification cost at fixed compute). The evaluation
    budget is held at 300."""
    a, b = (0, 1, 2), (3, 2, 1, 0)
    history = [a + (3,) + b, b + (1,) + a, a + b]
    disc = [(y,) + a + a + (z,) for y, z in ((0, 1), (1, 2), (2, 3), (3, 0))]
    disc += [b + b + (y,) for y in range(4)]
    dfam = [0] * 4 + [1] * 4
    test = [a * 4 + (y,) for y in range(4)] + [b * 4 + (y,) for y in range(2)]
    out = {}
    for label, Bd in (("high", 1000), ("low", 200)):
        out[label] = {"budget_disc": Bd, "a": evaluate(a, history, disc, dfam, test, Bd, 300),
                      "b": evaluate(b, history, disc, dfam, test, Bd, 300)}
    out["n_test"] = len(test)
    return out
