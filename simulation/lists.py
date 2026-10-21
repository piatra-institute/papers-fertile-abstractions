"""Domain 1: transformations of length-5 lists over {0, 1, 2}, with hierarchical task worlds.

A world draws level-1 concepts (short primitive sequences), level-2 concepts (sequences of level-1
concepts and primitives) and task families. A family fixes some slots to concepts and leaves others
free; its tasks fill the free slots with primitives. Every task is specified exactly by its behaviour
on all 243 lists. The learner's history is a corpus of solved programs built from level-1 concepts.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np

from engine import Library, Token, TaskSet, compose, search

LEN, Q = 5, 3
STATES = list(itertools.product(range(Q), repeat=LEN))
INDEX = {s: i for i, s in enumerate(STATES)}
X = len(STATES)


def _table(f):
    return np.array([INDEX[tuple(f(list(s)))] for s in STATES], dtype=np.uint8)


PRIMS = {
    "rot": lambda x: x[1:] + x[:1],
    "rev": lambda x: x[::-1],
    "swp": lambda x: [x[1], x[0]] + x[2:],
    "inc": lambda x: [(x[0] + 1) % Q] + x[1:],
    "cpy": lambda x: [x[0], x[0]] + x[2:],
    "add": lambda x: [(x[0] + x[1]) % Q] + x[1:],
}
NAMES = list(PRIMS)
B = len(NAMES)


def base_library() -> Library:
    return Library([Token(nm, (i,), _table(f)) for i, (nm, f) in enumerate(PRIMS.items())])


BASE = base_library()
TABLES = BASE.tables()


def behaviour(prims):
    return compose(TABLES, prims, X)


def _shortest_lengths(maxlen):
    """Behaviour -> primitive description length, by exhaustive enumeration up to maxlen."""
    seen = {}
    prev = [np.arange(X, dtype=np.uint8)]
    seen[prev[0].tobytes()] = 0
    for d in range(1, maxlen + 1):
        cur = []
        for row in prev:
            for t in range(B):
                r = TABLES[t][row]
                k = r.tobytes()
                if k not in seen:
                    seen[k] = d
                    cur.append(r)
        prev = cur
    return seen


_SHORT = None


def short_table():
    global _SHORT
    if _SHORT is None:
        _SHORT = _shortest_lengths(4)
    return _SHORT


@dataclass
class World:
    concepts1: list        # primitive sequences
    concepts2: list        # sequences over ('c', i) / ('p', j) units
    history: list          # primitive programs (solved earlier)
    disc: TaskSet
    test: TaskSet
    disc_families: list
    test_families: list


def _expand(unit, concepts1):
    kind, i = unit
    return tuple(concepts1[i]) if kind == 'c' else (i,)


def make_world(rng, P) -> World:
    short = short_table()
    c1, beh = [], set()
    while len(c1) < P["w1"]:
        k = int(rng.integers(P["c1_len"][0], P["c1_len"][1] + 1))
        seq = tuple(int(v) for v in rng.integers(0, B, k))
        b = behaviour(seq).tobytes()
        if short.get(b, 99) < k or b in beh:      # must not have a shorter primitive description
            continue
        c1.append(seq)
        beh.add(b)
    c2 = []
    while len(c2) < P["w2"]:
        k = int(rng.integers(2, 4))
        units = [('c', int(rng.integers(len(c1)))) if rng.random() < 0.75 else ('p', int(rng.integers(B))) for _ in range(k)]
        if sum(u[0] == 'c' for u in units) < 2:
            continue
        c2.append(units)

    def family(fid):
        while True:
            k = int(rng.integers(2, 4))
            slots = []
            for _ in range(k):
                u = rng.random()
                if u < P["p_c2"]:
                    slots.append(('C', int(rng.integers(len(c2)))))
                elif u < P["p_c2"] + P["p_c1"]:
                    slots.append(('c', int(rng.integers(len(c1)))))
                else:
                    slots.append(('free', None))
            if any(s[0] == 'free' for s in slots) and any(s[0] != 'free' for s in slots):
                return slots

    def realize(slots):
        out = []
        for kind, i in slots:
            if kind == 'C':
                for u in c2[i]:
                    out += _expand(u, c1)
            elif kind == 'c':
                out += list(c1[i])
            else:
                out.append(int(rng.integers(B)))
        return tuple(out)

    def taskset(nfam, per, fid0):
        specs, fam, templates = [], [], []
        seen = set()
        f = 0
        while f < nfam:
            slots = family(fid0 + f)
            got = []
            for _ in range(per * 6):
                prog = realize(slots)
                tab = behaviour(prog)
                kb = tab.tobytes()
                if kb in seen or short.get(kb, 99) <= 2:
                    continue
                seen.add(kb)
                got.append(tab)
                if len(got) == per:
                    break
            if len(got) < per:
                continue
            for tab in got:
                specs.append(('exact', tab))
                fam.append(fid0 + f)
            templates.append(slots)
            f += 1
        return TaskSet(specs, np.array(fam)), templates

    disc, dt = taskset(P["n_disc_fam"], P["per_fam"], 0)
    test, tt = taskset(P["n_test_fam"], P["per_fam"], 1000)
    hist = []
    for _ in range(P["n_history"]):
        k = int(rng.integers(2, 4))
        prog = []
        for _ in range(k):
            prog += list(c1[int(rng.integers(len(c1)))])
            if rng.random() < 0.4:
                prog.append(int(rng.integers(B)))
        hist.append(tuple(prog))
    return World(c1, c2, hist, disc, test, dt, tt)


def _contains(seq, sub):
    k = len(sub)
    return any(tuple(seq[i:i + k]) == tuple(sub) for i in range(len(seq) - k + 1))


def unlock_share(world: World, pattern, learned):
    """Ground-truth mechanism score (not available to the learner): the share of test tasks whose
    family uses a level-1 concept that contains the candidate's primitive sequence and that no token
    learned without the candidate contains."""
    def used(slots):
        out = set()
        for kind, i in slots:
            if kind == 'c':
                out.add(i)
            elif kind == 'C':
                out |= {u[1] for u in world.concepts2[i] if u[0] == 'c'}
        return out
    missing = [i for i, c in enumerate(world.concepts1)
               if _contains(c, pattern) and not any(_contains(t.prims, c) for t in learned)]
    if not missing:
        return 0.0
    per = len(world.test) / len(world.test_families)
    hit = sum(per for slots in world.test_families if used(slots) & set(missing))
    return hit / len(world.test)
