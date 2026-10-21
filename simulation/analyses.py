"""All analyses reported in the paper. Worlds are generated from fixed seeds; every number in the text
comes from the dictionary returned by run()."""
from __future__ import annotations

import os
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations

import numpy as np
import scipy

import constructions
import experiment
import lists
import maze
import stats
from engine import reach

SEED = 20261021
WORKERS = 4
N_WORLDS = 300
COSTS = [1.0, 2.0, 4.0, 8.0]
COMMON = dict(n_disc_fam=24, n_test_fam=60, per_fam=4, n_history=30, budget_disc=15000.0, budget_eval=15000.0,
              cv_eval=1.0, rounds=3, picks=2, kmax_disc=3, kmax_hist=4, n_cand=8)
LISTS = dict(COMMON, w1=5, w2=4, c1_len=(2, 4), p_c2=0.45, p_c1=0.25)
MAZE = dict(COMMON, room_dist=2, min_dist=4, history_max=6)
SMALL_CURRICULUM = dict(LISTS, n_disc_fam=12)


def _world(domain, seed, P):
    rng = np.random.default_rng([SEED, seed])
    if domain == "lists":
        return lists.make_world(rng, P)
    return maze.make_world(rng, P)


def _job(args):
    domain, seed, cv, label = args
    P = {"lists": LISTS, "maze": MAZE, "lists12": SMALL_CURRICULUM}[label]
    w = _world(domain, seed, P)
    if domain == "lists":
        r = experiment.run_world(lists.BASE, w, P, cv, constituents={tuple(c) for c in w.concepts1},
                                 mechanism=lambda p, K0: lists.unlock_share(w, p, K0))
    else:
        r = experiment.run_world(w.base, w, P, cv)
    r["seed"] = seed
    return (label, cv, seed), r


def _collect(jobs):
    with ProcessPoolExecutor(WORKERS) as ex:
        out = dict(ex.map(_job, jobs, chunksize=4))
    return out


def _bm(x, rng):
    return stats.boot_mean(x, rng)


def _value_summary(worlds, rng):
    v = np.concatenate([stats.values(w) for w in worlds])
    cross = []
    opp = []
    for w in worlds:
        h = stats.halves(w)
        a, b = stats.values(w, h), stats.values(w, ~h)
        cross.append(np.nanmean([stats._rho(a[:, 0], b[:, 1]), stats._rho(b[:, 0], a[:, 1])]))
    nz = (np.abs(v[:, 0]) > 1e-9) & (np.abs(v[:, 1]) > 1e-9)
    return {
        "n_candidates": int(len(v)),
        "sd": {"direct": float(v[:, 0].std()), "disc": float(v[:, 1].std()), "total": float(v[:, 2].std())},
        "mean": {"direct": float(v[:, 0].mean()), "disc": float(v[:, 1].mean()), "total": float(v[:, 2].mean())},
        "share_abs_disc_gt_005": float((np.abs(v[:, 1]) > 0.05).mean()),
        "share_disc_pos": float((v[:, 1] > 0).mean()), "share_disc_neg": float((v[:, 1] < 0).mean()),
        "share_opposite_sign": float((np.sign(v[nz, 0]) != np.sign(v[nz, 1])).mean()),
        "share_disc_exceeds_direct": float((np.abs(v[:, 1]) > np.abs(v[:, 0])).mean()),
        "rho_direct_disc_crossfit": _bm(cross, rng),
        "quantiles_disc": [float(q) for q in np.quantile(v[:, 1], [0.05, 0.25, 0.5, 0.75, 0.95])],
        "u_no": float(np.mean([w["u_no"] for w in worlds])),
        "base_round1_solved": float(np.mean([w["yield0"] for w in worlds])),
        "base_final_solved": float(np.mean([w["disc_solved_no"][-1] for w in worlds])),
        "n_disc": int(worlds[0]["n_disc"]), "n_test": int(worlds[0]["n_test"]),
    }


def _reliability(worlds, rng):
    sh = stats.split_half(worlds)
    m = float(np.nanmean(sh))
    return {"split_half": _bm(sh, rng), "spearman_brown": 2 * m / (1 + m), "ceiling": float(np.sqrt(2 * m / (1 + m)))}


def _predictors(worlds, rng):
    pa = stats.predictor_agreement(worlds)
    out = {k: _bm(v, rng) for k, v in pa.items()}
    cg = {k: _bm(stats.choice_gain(worlds, k), rng) for k in stats.PREDICTORS + ["oracle"]}
    return {"rho": out, "choice_gain": cg}


def _matched_pairs(worlds, comp_tol=1, direct_tol_tasks=1):
    """Candidate pairs in the same world matched on history compression and on direct value (first half
    of the test families). Their difference in discovery value is measured on the two halves of the
    remaining families; agreement between those halves shows the difference is not test noise."""
    d1, d2, absd = [], [], []
    for w in worlds:
        h = stats.halves(w)
        f = np.array(w["test_family"])
        rest = np.unique(f[~h])
        qa = np.isin(f, rest[::2])
        qb = (~h) & ~qa
        vT1 = stats.values(w, h)
        va, vb, vr = stats.values(w, qa), stats.values(w, qb), stats.values(w, ~h)
        tol = direct_tol_tasks / h.sum() + 1e-9
        C = w["cands"]
        for i, j in combinations(range(len(C)), 2):
            if abs(C[i]["comp"] - C[j]["comp"]) <= comp_tol and abs(vT1[i, 0] - vT1[j, 0]) <= tol:
                d1.append(va[i, 1] - va[j, 1])
                d2.append(vb[i, 1] - vb[j, 1])
                absd.append(abs(vr[i, 1] - vr[j, 1]))
    d1, d2 = np.array(d1), np.array(d2)
    return {"n_pairs": int(len(d1)), "rho_halves": stats._rho(d1, d2), "mean_abs_diff": float(np.mean(absd)),
            "share_abs_diff_gt_005": float(np.mean(np.array(absd) > 0.05))}


def _budget(res, label, rng):
    """Rank agreement of discovery value across verification costs, on disjoint test halves, against
    the within-cost split-half agreement; and frontier predictors at matched and mismatched costs."""
    seeds = sorted({s for (lb, cv, s) in res if lb == label})
    W = {cv: [res[(label, cv, s)] for s in seeds] for cv in COSTS}
    within = {cv: float(np.nanmean(stats.split_half(W[cv]))) for cv in COSTS}
    cross = {}
    for c2 in COSTS[1:]:
        r = []
        for a, b in zip(W[COSTS[0]], W[c2]):
            h = stats.halves(a)
            r.append(np.nanmean([stats._rho(stats.values(a, h)[:, 1], stats.values(b, ~h)[:, 1]),
                                 stats._rho(stats.values(a, ~h)[:, 1], stats.values(b, h)[:, 1])]))
        m = float(np.nanmean(r))
        cross[str(c2)] = {"rho": _bm(r, rng), "disattenuated": m / np.sqrt(within[COSTS[0]] * within[c2])}
    mm = {}
    lo, hi = COSTS[0], COSTS[2]
    for k in ["yield", "gain", "fc", "lookahead"]:
        matched, mismatched = [], []
        for a, b in zip(W[lo], W[hi]):
            va, vb = stats.values(a)[:, 1], stats.values(b)[:, 1]
            pa_, pb_ = [c[k] for c in a["cands"]], [c[k] for c in b["cands"]]
            matched.append(np.nanmean([stats._rho(pa_, va), stats._rho(pb_, vb)]))
            mismatched.append(np.nanmean([stats._rho(pa_, vb), stats._rho(pb_, va)]))
        mm[k] = {"matched": _bm(matched, rng), "mismatched": _bm(mismatched, rng),
                 "difference": _bm(np.array(matched) - np.array(mismatched), rng)}
    comp_same = []
    for a, b in zip(W[lo], W[hi]):
        comp_same.append(stats._rho([c["comp"] for c in a["cands"]], [c["comp"] for c in b["cands"]]))
    return {"within_split_half": {str(k): v for k, v in within.items()}, "cross_vs_cost1": cross,
            "matched_vs_mismatched_cost1_cost4": mm, "comp_rank_identical": bool(np.nanmin(comp_same) > 0.999)}


def _constituents(worlds, rng):
    v = np.concatenate([stats.values(w) for w in worlds])
    con = np.array([c["constituent"] for w in worlds for c in w["cands"]])
    un = [stats._rho([c["unlock"] for c in w["cands"]], stats.values(w)[:, 1]) for w in worlds]
    return {"share_constituent": float(con.mean()), "disc_constituent": float(v[con, 1].mean()),
            "disc_other": float(v[~con, 1].mean()), "direct_constituent": float(v[con, 0].mean()),
            "direct_other": float(v[~con, 0].mean()), "rho_unlock": _bm(un, rng)}


def _mechanism(worlds, rng):
    """How early access changes what is learned. With canonical evaluation order, identical learned
    libraries give identical evaluations, so discovery value requires a change in the library."""
    v = np.concatenate([stats.values(w) for w in worlds])[:, 1]
    C = [c for w in worlds for c in w["cands"]]
    same = np.array([c["same_library"] for c in C])
    desc = np.array([c["n_desc"] for c in C])
    changed = ~same
    rho = [stats._rho([c["n_desc"] for c in w["cands"]], stats.values(w)[:, 1]) for w in worlds]
    swapped = np.array([max(c["n_K1"], w["n_K0"]) - c["n_shared"] for w in worlds for c in w["cands"]])
    return {
        "share_same_library": float(same.mean()),
        "same_library_zero": bool(np.all(v[same] == 0)),
        "share_with_descendant": float((desc > 0).mean()),
        "mean_abs_disc": {"same": float(np.abs(v[same]).mean()) if same.any() else 0.0,
                          "changed_no_descendant": float(np.abs(v[changed & (desc == 0)]).mean()),
                          "with_descendant": float(np.abs(v[desc > 0]).mean())},
        "mean_disc": {"changed_no_descendant": float(v[changed & (desc == 0)].mean()),
                      "with_descendant": float(v[desc > 0].mean())},
        "share_changed_no_descendant": float((changed & (desc == 0)).mean()),
        "share_abs_disc_from_no_descendant": float(np.abs(v[changed & (desc == 0)]).sum() / np.abs(v).sum()),
        "rho_desc_disc": _bm(rho, rng),
        "mean_tokens_changed": float(swapped[changed].mean()),
    }


def _accessibility():
    """Behaviours reachable within a budget with and without the history's most compressive pattern,
    in the first list world."""
    w = _world("lists", 0, LISTS)
    a = experiment.candidates(lists.BASE, w.history, 1, LISTS["kmax_hist"])[0]
    budgets = [int(b) for b in np.unique(np.round(np.logspace(2, np.log10(60000), 22)))]
    r0 = reach(lists.BASE, budgets[-1], 1.0)
    r1 = reach(lists.BASE.extended([a["token"]]), budgets[-1], 1.0)
    rows = []
    for b in budgets:
        s0 = {k for k, c in r0.items() if c <= b}
        s1 = {k for k, c in r1.items() if c <= b}
        rows.append({"budget": b, "base": len(s0), "with": len(s1), "gained": len(s1 - s0), "lost": len(s0 - s1)})
    tok = a["token"]
    return {"pattern": [lists.NAMES[i] for i in a["pattern"]], "rows": rows,
            "token_equals_expansion": bool(np.array_equal(lists.behaviour(tok.prims), tok.table))}


def predictor_free_checks(res):
    """Exactness checks: decomposition identity and determinism of a re-run world."""
    ok_decomp = True
    for r in res.values():
        v = stats.values(r)
        ok_decomp &= bool(np.allclose(v[:, 0] + v[:, 1], v[:, 2]))
    _, again = _job(("lists", 0, 1.0, "lists"))
    first = res[("lists", 1.0, 0)]
    same = again["cands"] == first["cands"] and again["s_no"] == first["s_no"]
    return ok_decomp, bool(same)


def run():
    rng = np.random.default_rng(SEED)
    jobs = [(d, s, cv, d) for d in ("lists", "maze") for s in range(N_WORLDS) for cv in COSTS]
    jobs += [("lists", s, cv, "lists12") for s in range(N_WORLDS) for cv in (1.0, 4.0)]
    res = _collect(jobs)
    out = {"config": {"seed": SEED, "n_worlds": N_WORLDS, "costs": COSTS, "lists": {k: list(v) if isinstance(v, tuple) else v for k, v in LISTS.items()},
                      "maze": MAZE, "small_curriculum_families": SMALL_CURRICULUM["n_disc_fam"],
                      "python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__,
                      "platform": platform.platform()}}
    for label in ("lists", "maze"):
        sec = {}
        for cv in (1.0, 4.0):
            W = [res[(label, cv, s)] for s in range(N_WORLDS)]
            sec[str(cv)] = {"values": _value_summary(W, rng), "reliability": _reliability(W, rng),
                            "predictors": _predictors(W, rng), "matched": _matched_pairs(W)}
        sec["budget"] = _budget(res, label, rng)
        sec["mechanism"] = _mechanism([res[(label, 1.0, s)] for s in range(N_WORLDS)], rng)
        out[label] = sec
    out["lists"]["constituents"] = _constituents([res[("lists", 1.0, s)] for s in range(N_WORLDS)], rng)
    out["lists12"] = {}
    for cv in (1.0, 4.0):
        W = [res[("lists12", cv, s)] for s in range(N_WORLDS)]
        out["lists12"][str(cv)] = {"values": _value_summary(W, rng), "reliability": _reliability(W, rng),
                                   "predictors": _predictors(W, rng)}
    out["accessibility"] = _accessibility()
    sep, rev = constructions.separation(), constructions.reversal()
    out["constructions"] = {"separation": sep, "reversal": rev}
    acc = out["accessibility"]["rows"]
    ok_decomp, same = predictor_free_checks(res)
    keys_match = ["comp", "freq", "v_direct", "gain", "fc"]
    out["checks"] = {
        "separation_matched": all(sep["a"][k] == sep["a2"][k] for k in keys_match),
        "separation_differs": sep["a"]["v_disc"] > 0 and sep["a2"]["v_disc"] == 0,
        "reversal_high_order": rev["high"]["a"]["v_disc"] > rev["high"]["b"]["v_disc"],
        "reversal_low_order": rev["low"]["a"]["v_disc"] < rev["low"]["b"]["v_disc"],
        "accessibility_gains_and_losses": any(r["gained"] > 0 for r in acc) and any(r["lost"] > 0 for r in acc),
        "decomposition_identity": ok_decomp,
        "deterministic_rerun": same,
        "eight_candidates_per_world": all(len(r["cands"]) == COMMON["n_cand"] for r in res.values()),
        "compression_budget_independent": out["lists"]["budget"]["comp_rank_identical"] and out["maze"]["budget"]["comp_rank_identical"],
        "discovery_value_reliable_lists": out["lists"]["1.0"]["reliability"]["split_half"]["lo"] > 0,
        "discovery_value_reliable_maze": out["maze"]["1.0"]["reliability"]["split_half"]["lo"] > 0,
    }
    out["checks"]["token_equals_expansion"] = out["accessibility"]["token_equals_expansion"]
    out["checks"]["identical_library_zero_value"] = out["lists"]["mechanism"]["same_library_zero"] and out["maze"]["mechanism"]["same_library_zero"]
    table = []
    for (lb, cv, s), r in sorted(res.items()):
        if lb not in ("lists", "maze") or cv not in (1.0, 4.0):
            continue
        v = stats.values(r)
        for c, (vd, vs, vt) in zip(r["cands"], v):
            table.append([lb, cv, s, float(vd), float(vs), float(vt), c["comp"], c["freq"], c["yield"], c["gain"], c["fc"], c["lookahead"],
                          c["n_desc"], int(c["same_library"])])
    out["candidates"] = {"columns": ["domain", "cv", "world", "v_direct", "v_disc", "v_total", "comp", "freq", "yield", "gain", "fc", "lookahead",
                                     "n_desc", "same_library"],
                         "rows": table}
    return out
