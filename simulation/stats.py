"""Statistics over worlds: values on disjoint test families, predictor agreement and reliability."""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr

PREDICTORS = ["comp", "freq", "direct", "yield", "gain", "fc", "lookahead"]


def halves(w):
    f = np.array(w["test_family"])
    fams = np.unique(f)
    return np.isin(f, fams[::2])


def values(w, mask=None):
    """Per-candidate direct, discovery and total value on the test tasks selected by mask."""
    no = np.array(w["s_no"])
    m = np.ones(len(no), bool) if mask is None else mask
    out = []
    for c in w["cands"]:
        e, l = np.array(c["s_early"]), np.array(c["s_late"])
        out.append((l[m].mean() - no[m].mean(), e[m].mean() - l[m].mean(), e[m].mean() - no[m].mean()))
    return np.array(out)


def _rho(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.std() == 0 or y.std() == 0:
        return np.nan
    return float(spearmanr(x, y).statistic)


def predictor_agreement(worlds):
    """Within-world Spearman correlation between each predictor and discovery value. Direct value is
    measured on one half of the test families and discovery value on the other, then the halves are
    swapped and the two correlations averaged, so that no test task enters both sides."""
    res = {k: [] for k in PREDICTORS}
    for w in worlds:
        h = halves(w)
        v1, v2 = values(w, h), values(w, ~h)
        vfull = values(w)
        for k in PREDICTORS:
            if k == "direct":
                r = np.nanmean([_rho(v1[:, 0], v2[:, 1]), _rho(v2[:, 0], v1[:, 1])])
            else:
                r = _rho([c[k] for c in w["cands"]], vfull[:, 1])
            res[k].append(r)
    return {k: np.array(v) for k, v in res.items()}


def split_half(worlds):
    r = []
    for w in worlds:
        h = halves(w)
        r.append(_rho(values(w, h)[:, 1], values(w, ~h)[:, 1]))
    return np.array(r)


def boot_mean(x, rng, n=4000):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return {"mean": None, "lo": None, "hi": None, "n": 0}
    bs = rng.choice(x, size=(n, len(x)), replace=True).mean(1)
    return {"mean": float(x.mean()), "lo": float(np.quantile(bs, 0.025)), "hi": float(np.quantile(bs, 0.975)), "n": int(len(x))}


def choice_gain(worlds, key):
    """Mean discovery value of the candidate a predictor ranks first, minus the mean over candidates.
    Ties are broken by averaging over the tied candidates. Direct value is cross-fitted as above."""
    g = []
    for w in worlds:
        h = halves(w)
        for sel, ev in ((h, ~h), (~h, h)):
            vd = values(w, ev)[:, 1]
            if key == "direct":
                x = values(w, sel)[:, 0]
            elif key == "oracle":
                x = vd
            else:
                x = np.array([c[key] for c in w["cands"]], float)
            top = np.isclose(x, x.max())
            g.append(vd[top].mean() - vd.mean())
    return np.array(g)
