"""The early-, late- and no-access design and the candidate predictors, for one world.

For a candidate abstraction a, with K1 the tokens discovered with a available and K0 those discovered
without it, and U the share of withheld test tasks a frozen solver reaches within its budget:
    direct value     V_direct = U(L + a + K0) - U(L + K0)
    discovery value  V_disc   = U(L + a + K1) - U(L + a + K0)
Both sides of V_disc contain a, so the contrast isolates what having a during discovery changed.
Per-task outcomes are stored so that analyses can evaluate predictors and outcomes on disjoint
test families.
"""
from __future__ import annotations

import numpy as np

from engine import Library, TaskSet, compress, discover, gain, make_token, pattern_stats, search


def subset(ts: TaskSet, keep) -> TaskSet:
    idx = np.nonzero(keep)[0]
    return TaskSet([ts.specs[i] for i in idx], ts.family[idx])


def candidates(base: Library, history, m, kmax):
    """The m patterns of the history corpus with the largest description-length saving, keeping one
    pattern per behaviour and skipping identities and duplicates of primitives."""
    counts, _ = pattern_stats(history, [0] * len(history), kmax)
    ranked = sorted(((gain(p, c), c, p) for p, c in counts.items() if c >= 2 and gain(p, c) > 0),
                    key=lambda z: (-z[0], -len(z[2]), z[2]))
    X = len(base.tokens[0].table)
    ident = np.arange(X)
    out, seen = [], set()
    for g, c, p in ranked:
        tok = make_token(base, p, name=f"a{len(out)}")
        b = tok.table.tobytes()
        if np.array_equal(tok.table, ident) or base.has_behaviour(tok.table) or b in seen:
            continue
        seen.add(b)
        out.append({"token": tok, "pattern": p, "comp": int(g), "freq": int(c)})
        if len(out) == m:
            break
    return out


def canonical(tokens):
    """Learned tokens in a fixed order (primitive length, then expansion), so that two runs that learn
    the same tokens are evaluated with identical libraries."""
    return sorted(tokens, key=lambda t: (t.plen, t.prims))


def lineage(a, learned):
    """Number of learned tokens defined, directly or through other learned tokens, in terms of a."""
    desc = {a.name}
    for t in learned:
        if any(p in desc for p in t.parts):
            desc.add(t.name)
    return len(desc) - 1


def frontier_compression(lib, first, picks, kmax):
    """Saving available to the learner's compressor in the solutions of the first discovery round,
    counting only patterns that recur in at least two task families."""
    solved, sp, sf = first
    _, g = compress(lib, sp, sf, picks, kmax=kmax, min_families=2, prefix="fc")
    return int(g)


def run_world(base: Library, world, P, cv_disc, constituents=None, mechanism=None):
    Bd, Be, cve = P["budget_disc"], P["budget_eval"], P["cv_eval"]
    R, J, km = P["rounds"], P["picks"], P["kmax_disc"]
    disc, test = world.disc, world.test
    fold = disc.family % 2 == 0
    dA, dB = subset(disc, fold), subset(disc, ~fold)

    def learn(lib, ts):
        return discover(lib, ts, Bd, cv_disc, R, J, km)

    def u(lib, ts):
        return search(lib, ts, Be, cve)[0]

    K0, log0, first0 = learn(base, disc)
    K0A, K0B = learn(base, dA)[0], learn(base, dB)[0]
    K0s, K0As, K0Bs = canonical(K0), canonical(K0A), canonical(K0B)
    exp0 = sorted(t.prims for t in K0)
    beh0 = {t.table.tobytes() for t in K0}
    s_no = u(base.extended(K0s), test)
    fc0 = frontier_compression(base, first0, J, km)
    out = {"u_no": float(s_no.mean()), "disc_solved_no": [l["solved"] for l in log0], "n_K0": len(K0),
           "fc0": fc0, "yield0": int(first0[0].sum()), "n_disc": len(disc), "n_test": len(test),
           "s_no": s_no.astype(int).tolist(), "test_family": [int(f) for f in test.family], "cands": []}
    for c in candidates(base, world.history, P["n_cand"], P["kmax_hist"]):
        a = c["token"]
        la = base.extended([a])
        K1, log1, first1 = learn(la, disc)
        s_early, s_late = u(la.extended(canonical(K1)), test), u(la.extended(K0s), test)
        K1A, K1B = learn(la, dA)[0], learn(la, dB)[0]
        look = 0.5 * ((u(la.extended(canonical(K1A)), dB).mean() - u(la.extended(K0As), dB).mean())
                      + (u(la.extended(canonical(K1B)), dA).mean() - u(la.extended(K0Bs), dA).mean()))
        out["cands"].append({
            "pattern": [int(v) for v in c["pattern"]], "plen": a.plen,
            "constituent": bool(constituents is not None and tuple(c["pattern"]) in constituents),
            "comp": c["comp"], "freq": c["freq"],
            "unlock": None if mechanism is None else float(mechanism(tuple(c["pattern"]), K0)),
            "yield": int(first1[0].sum()) - int(first0[0].sum()),
            "gain": int((first1[0] & ~first0[0]).sum()), "lost": int((first0[0] & ~first1[0]).sum()),
            "fc": frontier_compression(la, first1, J, km) - fc0,
            "lookahead": float(look),
            "n_K1": len(K1), "disc_solved": [l["solved"] for l in log1],
            "same_library": sorted(t.prims for t in K1) == exp0,
            "n_shared": len(beh0 & {t.table.tobytes() for t in K1}), "n_desc": lineage(a, K1),
            "s_early": s_early.astype(int).tolist(), "s_late": s_late.astype(int).tolist(),
        })
    return out
