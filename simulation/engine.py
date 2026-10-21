"""Bounded program search, library compression and discovery over finite transformation domains.

A domain is a finite state set X and a list of primitive transformations X -> X, each stored as a
lookup table. A program is a sequence of library tokens applied left to right; its behaviour is the
composed table. Every token is defined by a sequence of primitives, so adding a token never changes
which behaviours can be expressed, only how many candidates a bounded search must examine to reach them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Token:
    name: str
    prims: tuple          # definition as a primitive sequence
    table: np.ndarray     # behaviour, shape (|X|,)
    parts: tuple = ()     # definition in terms of earlier library tokens (for printing)

    @property
    def plen(self) -> int:
        return len(self.prims)


@dataclass
class Library:
    tokens: list = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.tokens)

    def tables(self) -> np.ndarray:
        return np.stack([t.table for t in self.tokens])

    def plens(self) -> np.ndarray:
        return np.array([t.plen for t in self.tokens], dtype=float)

    def extended(self, extra) -> "Library":
        return Library(list(self.tokens) + list(extra))

    def has_behaviour(self, table) -> bool:
        return any(np.array_equal(t.table, table) for t in self.tokens)


def compose(tables, seq, X):
    out = np.arange(X, dtype=tables.dtype)
    for t in seq:
        out = tables[t][out]
    return out


def make_token(lib: Library, seq, name=None) -> Token:
    prims = tuple(p for t in seq for p in lib.tokens[t].prims)
    tab = compose(lib.tables(), seq, len(lib.tokens[0].table))
    return Token(name or f"f{len(lib.tokens)}", prims, tab, tuple(lib.tokens[t].name for t in seq))


# ------------------------------------------------------------------ tasks
# A task is ('exact', table) or ('pairs', ((s, g), ...)): the program must map every s to its g.

@dataclass
class TaskSet:
    specs: list
    family: np.ndarray        # family id per task

    def __len__(self):
        return len(self.specs)


_POS = None


def _keypos(X):
    global _POS
    if _POS is None or _POS[0] != X:
        rng = np.random.default_rng(12345)
        _POS = (X, np.sort(rng.choice(X, size=8, replace=False)))
    return _POS[1]


def search(lib: Library, tasks: TaskSet, budget: float, cv: float, cx: float = 1.0):
    """Breadth-first enumeration of token sequences in length-lexicographic order.

    Each candidate costs cv (verification) plus cx times the primitive length of its last token
    (incremental execution, prefixes cached). A task is solved by the first candidate that meets its
    specification if the cumulative cost at that candidate is within the budget. Returns arrays
    solved (bool), cost (cumulative compute at solution, or budget) and the programs found.
    """
    T = lib.tables()
    n, X = T.shape
    kap = cv + cx * lib.plens()
    cumk = np.cumsum(kap)
    K = cumk[-1]
    m = len(tasks)
    solved = np.zeros(m, bool)
    cost = np.full(m, float(budget))
    progs = [None] * m
    exact = [i for i, s in enumerate(tasks.specs) if s[0] == 'exact']
    pairs = [i for i, s in enumerate(tasks.specs) if s[0] == 'pairs']
    pos = _keypos(X)
    if exact:
        tk = np.stack([tasks.specs[i][1] for i in exact])
        tkeys = np.ascontiguousarray(tk[:, pos]).view(np.uint64).ravel()
        key_to = {}
        for j, kk in enumerate(tkeys):
            key_to.setdefault(int(kk), []).append(exact[j])
        tkeyset = np.array(sorted(key_to), dtype=np.uint64)

    def check(rows, rcost, level, idx):
        if exact:
            keys = np.ascontiguousarray(rows[:, pos]).view(np.uint64).ravel()
            hit = np.nonzero(np.isin(keys, tkeyset))[0]
            for h in hit:
                for ti in key_to[int(keys[h])]:
                    if not solved[ti] and np.array_equal(rows[h], tasks.specs[ti][1]):
                        solved[ti] = True
                        cost[ti] = rcost[h]
                        progs[ti] = _decode(idx[h], level, n)
        for ti in pairs:
            if solved[ti]:
                continue
            ok = np.ones(len(rows), bool)
            for s, g in tasks.specs[ti][1]:
                ok &= rows[:, s] == g
            w = np.nonzero(ok)[0]
            if len(w):
                h = w[0]
                solved[ti] = True
                cost[ti] = rcost[h]
                progs[ti] = _decode(idx[h], level, n)

    keep = cumk <= budget
    if not keep.any():
        return solved, cost, progs
    check(T[keep], cumk[keep], 1, np.nonzero(keep)[0])
    if not keep.all():
        return solved, cost, progs
    prev = T
    C = K
    level = 1
    while not solved.all():
        pmax = min(len(prev), int(np.floor((budget - C - kap[0]) / K)) + 1)
        if pmax <= 0:
            break
        new = T[:, prev[:pmax]].transpose(1, 0, 2).reshape(-1, X)
        rc = C + np.repeat(np.arange(pmax) * K, n) + np.tile(cumk, pmax)
        ok = rc <= budget
        idx = np.arange(pmax * n)
        if ok.all():
            check(new, rc, level + 1, idx)
        else:
            check(new[ok], rc[ok], level + 1, idx[ok])
        if pmax < len(prev) or not ok.all():
            break
        C += len(prev) * K
        prev = new
        level += 1
    return solved, cost, progs


def _decode(i, level, n):
    out = []
    for _ in range(level):
        out.append(int(i % n))
        i //= n
    return tuple(reversed(out))


# ------------------------------------------------------------------ compression

def pattern_stats(progs, fams, kmax):
    """Non-overlapping occurrence counts (greedy, left to right) of every contiguous pattern of
    length 2..kmax, with the set of task families in which each occurs."""
    counts, famset = {}, {}
    for p, f in zip(progs, fams):
        for k in range(2, kmax + 1):
            last = {}
            for i in range(len(p) - k + 1):
                pat = tuple(p[i:i + k])
                if last.get(pat, -1) <= i:
                    counts[pat] = counts.get(pat, 0) + 1
                    famset.setdefault(pat, set()).add(f)
                    last[pat] = i + k
    return counts, famset


def gain(pat, count):
    """Description-length saving in tokens: occurrences shortened minus the definition."""
    return count * (len(pat) - 1) - len(pat)


def rewrite(p, pat, tok):
    out, i, k = [], 0, len(pat)
    while i < len(p):
        if tuple(p[i:i + k]) == pat:
            out.append(tok)
            i += k
        else:
            out.append(p[i])
            i += 1
    return out


def compress(lib: Library, progs, fams, picks, kmax=3, min_count=2, min_families=1, prefix="k"):
    """Greedy library learning: repeatedly add the pattern with the largest description-length
    saving on the corpus (ties: longer, then lexicographic), skipping patterns whose behaviour is
    the identity or duplicates a library token. Returns the new tokens and the total saving."""
    progs = [list(p) for p in progs]
    lib = Library(list(lib.tokens))
    X = len(lib.tokens[0].table)
    ident = np.arange(X)
    new, total = [], 0
    for _ in range(picks):
        counts, famset = pattern_stats(progs, fams, kmax)
        cands = sorted(((gain(p, c), len(p), p) for p, c in counts.items()
                        if c >= min_count and gain(p, c) > 0 and len(famset[p]) >= min_families),
                       key=lambda z: (-z[0], -z[1], z[2]))
        chosen = None
        for g, _, pat in cands:
            tok = make_token(lib, pat, name=f"{prefix}{len(new)}")
            if np.array_equal(tok.table, ident) or lib.has_behaviour(tok.table):
                continue
            chosen = (g, pat, tok)
            break
        if chosen is None:
            break
        g, pat, tok = chosen
        lib.tokens.append(tok)
        tid = lib.n - 1
        progs = [rewrite(p, pat, tid) for p in progs]
        new.append(tok)
        total += g
    return new, total


def discover(lib: Library, tasks: TaskSet, budget, cv, rounds, picks, kmax, cx=1.0, prefix="d"):
    """Rounds of search on the discovery tasks followed by compression of the solutions found.
    Returns the learned tokens and, per round, the number of tasks solved and the compute used."""
    learned, log = [], []
    cur = Library(list(lib.tokens))
    for r in range(rounds):
        solved, cost, progs = search(cur, tasks, budget, cv, cx)
        sp = [progs[i] for i in np.nonzero(solved)[0]]
        sf = [tasks.family[i] for i in np.nonzero(solved)[0]]
        new, g = compress(cur, sp, sf, picks, kmax=kmax, prefix=f"{prefix}{r}_")
        log.append({"solved": int(solved.sum()), "compute": float(cost.sum()), "learned": len(new), "gain": int(g)})
        if r == 0:
            first = (solved.copy(), sp, sf)
        cur = cur.extended(new)
        learned += new
        if not new:
            break
    return learned, log, first


def reach(lib: Library, budget: float, cv: float, cx: float = 1.0):
    """Every behaviour the search reaches within the budget, with the cumulative cost at which it is
    first produced (exact behaviour identity)."""
    T = lib.tables()
    n, X = T.shape
    kap = cv + cx * lib.plens()
    cumk = np.cumsum(kap)
    K = cumk[-1]
    first = {}

    def add(rows, rc):
        for r, c in zip(rows, rc):
            b = r.tobytes()
            if b not in first:
                first[b] = float(c)
    keep = cumk <= budget
    add(T[keep], cumk[keep])
    if not keep.all():
        return first
    prev, C = T, K
    while True:
        pmax = min(len(prev), int(np.floor((budget - C - kap[0]) / K)) + 1)
        if pmax <= 0:
            break
        new = T[:, prev[:pmax]].transpose(1, 0, 2).reshape(-1, X)
        rc = C + np.repeat(np.arange(pmax) * K, n) + np.tile(cumk, pmax)
        ok = rc <= budget
        add(new[ok], rc[ok])
        if pmax < len(prev) or not ok.all():
            break
        C += len(prev) * K
        prev = new
    return first
