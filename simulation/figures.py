"""Figures for Fertile Abstractions."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, GRID, AMBER, GREEN, BLUE, GRAY, RED = "#1a1a1a", "#d9d9d9", "#b45309", "#15803d", "#2563eb", "#78716c", "#b3202c"
DOMAIN = {"lists": "list programs", "maze": "navigation"}
LABELS = {"comp": "history compression", "freq": "history frequency", "direct": "direct value (other test half)",
          "yield": "frontier yield (net)", "gain": "frontier gain (gross)", "fc": "frontier compression",
          "lookahead": "look-ahead (cross-fitted)"}


def _style(ax):
    ax.grid(True, color=GRID, lw=0.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=10.5)


def _title(ax, t):
    ax.set_title(t, fontsize=12.5, loc="left")


def _table(r, domain, cv):
    cols = r["candidates"]["columns"]
    rows = [x for x in r["candidates"]["rows"] if x[0] == domain and x[1] == cv]
    return {c: np.array([x[i] for x in rows]) for i, c in enumerate(cols)}


def plot_accessibility(r, path):
    acc = r["accessibility"]
    rows = acc["rows"]
    b = np.array([x["budget"] for x in rows])
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.3))
    ax = axes[0]
    ax.plot(b, [x["base"] for x in rows], "o-", color=INK, ms=3.5, lw=1.4, label="primitives only")
    ax.plot(b, [x["with"] for x in rows], "s-", color=BLUE, ms=3.5, lw=1.4, label="primitives and one abstraction")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("search budget (compute units)", fontsize=12)
    ax.set_ylabel("distinct behaviours reached", fontsize=12)
    ax.axvline(r["config"]["lists"]["budget_eval"], color=GRAY, lw=0.8, ls=":")
    ax.legend(fontsize=10, frameon=False, loc="upper left")
    _title(ax, "a. reachable behaviours")
    _style(ax)
    ax = axes[1]
    base = np.array([x["base"] for x in rows], float)
    ax.plot(b, np.array([x["gained"] for x in rows]) / base, "o-", color=GREEN, ms=3.5, lw=1.4, label="gained with the abstraction")
    ax.plot(b, np.array([x["lost"] for x in rows]) / base, "o-", color=RED, ms=3.5, lw=1.4, label="lost with the abstraction")
    ax.set_xscale("log")
    ax.set_ylim(0, 0.75)
    ax.set_xlabel("search budget (compute units)", fontsize=12)
    ax.set_ylabel("share of behaviours reached without it", fontsize=12)
    ax.axvline(r["config"]["lists"]["budget_eval"], color=GRAY, lw=0.8, ls=":")
    ax.legend(fontsize=10, frameon=False, loc="upper left")
    _title(ax, "b. what one definable token changes")
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_values(r, path):
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.8))
    rng = np.random.default_rng(1)
    for ax, (d, lab) in zip(axes, (("lists", "a."), ("maze", "b."))):
        t = _table(r, d, 1.0)
        n = len(t["v_direct"])
        jx, jy = rng.uniform(-0.002, 0.002, n), rng.uniform(-0.002, 0.002, n)
        ax.scatter(t["v_direct"] + jx, t["v_disc"] + jy, s=7, color=BLUE, alpha=0.25, lw=0)
        ax.axhline(0, color=INK, lw=0.7)
        ax.axvline(0, color=INK, lw=0.7)
        lim = max(np.abs(t["v_disc"]).max(), np.abs(t["v_direct"]).max()) * 1.05
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        sd = r[d]["1.0"]["values"]["sd"]
        ax.text(0.03, 0.97, f"sd direct {sd['direct']:.3f}\nsd discovery {sd['disc']:.3f}", transform=ax.transAxes,
                va="top", fontsize=10, color=INK)
        ax.set_xlabel("direct value (late minus no access)", fontsize=12)
        ax.set_ylabel("discovery value (early minus late access)", fontsize=12)
        _title(ax, f"{lab} {DOMAIN[d]}, {r['config']['n_worlds']} worlds")
        _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_predictors(r, path):
    keys = list(LABELS)
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 5.4), sharey=True)
    y = np.arange(len(keys))[::-1]
    for ax, (d, lab) in zip(axes, (("lists", "a."), ("maze", "b."))):
        for off, cv, col, nm in ((0.18, "1.0", BLUE, "verification cost 1"), (-0.18, "4.0", AMBER, "verification cost 4")):
            P = r[d][cv]["predictors"]["rho"]
            m = np.array([P[k]["mean"] for k in keys])
            lo = np.array([P[k]["lo"] for k in keys])
            hi = np.array([P[k]["hi"] for k in keys])
            ax.barh(y + off, m, height=0.34, color=col, alpha=0.85, label=nm)
            ax.errorbar(m, y + off, xerr=[m - lo, hi - m], fmt="none", ecolor=INK, lw=0.9, capsize=2)
        ax.axvline(0, color=INK, lw=0.8)
        ax.axvline(r[d]["1.0"]["reliability"]["ceiling"], color=GRAY, lw=1.0, ls="--", label="expected for a perfect predictor")
        ax.set_yticks(y)
        ax.set_yticklabels([LABELS[k] for k in keys], fontsize=10.5)
        ax.set_xlim(-0.35, 1.0)
        ax.set_xlabel("rank correlation with discovery value", fontsize=11.5)
        _title(ax, f"{lab} {DOMAIN[d]}")
        _style(ax)
    h, l = axes[1].get_legend_handles_labels()
    fig.legend(h, l, fontsize=10.5, frameon=False, loc="lower center", ncol=3)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_budget(r, path):
    fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.5))
    ax = axes[0]
    for d, col in (("lists", BLUE), ("maze", AMBER)):
        B = r[d]["budget"]["cross_vs_cost1"]
        xs = [1.0] + [float(k) for k in B]
        ys = [1.0] + [B[k]["disattenuated"] for k in B]
        ax.plot(xs, ys, "o-", color=col, ms=4, lw=1.5, label=DOMAIN[d])
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 2, 4, 8])
    ax.set_xticklabels(["1", "2", "4", "8"])
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("verification cost during discovery", fontsize=12)
    ax.set_ylabel("agreement with ranking at cost 1", fontsize=12)
    ax.legend(fontsize=10, frameon=False, loc="lower left")
    _title(ax, "a. rankings of discovery value across costs")
    _style(ax)
    ax = axes[1]
    pos, data, cols = [], [], []
    for i, d in enumerate(("lists", "maze")):
        t = _table(r, d, 1.0)
        changed = t["same_library"] == 0
        g1 = t["v_disc"][changed & (t["n_desc"] == 0)]
        g2 = t["v_disc"][t["n_desc"] > 0]
        data += [g1, g2]
        pos += [3 * i + 0.6, 3 * i + 1.4]
        cols += [GRAY, BLUE]
    bp = ax.boxplot(data, positions=pos, widths=0.6, patch_artist=True, showfliers=True,
                    flierprops=dict(marker=".", ms=2, alpha=0.4), medianprops=dict(color=INK))
    for p, c in zip(bp["boxes"], cols):
        p.set_facecolor(c)
        p.set_alpha(0.6)
    ax.axhline(0, color=INK, lw=0.7)
    ax.set_xticks([1.0, 4.0])
    ax.set_xticklabels([DOMAIN["lists"], DOMAIN["maze"]], fontsize=11)
    ax.set_ylabel("discovery value", fontsize=12)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=GRAY, alpha=0.6, label="library changed, no descendant"),
                       Patch(color=BLUE, alpha=0.6, label="at least one descendant")], fontsize=10, frameon=False, loc="upper right")
    _title(ax, "b. how early access acts")
    _style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def make_all(r, out):
    out = Path(out)
    plot_accessibility(r, out / "accessibility.png")
    plot_values(r, out / "values.png")
    plot_predictors(r, out / "predictors.png")
    plot_budget(r, out / "budget.png")
