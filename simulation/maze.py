"""Domain 2: navigation in a building of 4 x 4 rooms joined by single-cell doors.

The state is the agent's cell; the primitives move one cell north, east, south or west and leave the
agent in place when a wall blocks the move. A task asks for a plan taking one start cell to one goal
cell, so many programs satisfy it and only the start cell is checked. A family is an ordered pair of
rooms; its tasks draw start and goal cells inside those rooms. The learner's history is the set of
shortest plans for short trips within a room or between neighbouring rooms.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from engine import Library, Token, TaskSet, search

ROOMS, SIZE = 4, 3
G = ROOMS * (SIZE + 1) + 1
MOVES = {"N": (-1, 0), "E": (0, 1), "S": (1, 0), "W": (0, -1)}


@dataclass
class World:
    cells: list
    room_of: np.ndarray
    base: Library
    history: list
    disc: TaskSet
    test: TaskSet
    disc_families: list
    test_families: list


def _building(rng):
    free = np.zeros((G, G), bool)
    for r in range(ROOMS):
        for c in range(ROOMS):
            y0, x0 = 1 + r * (SIZE + 1), 1 + c * (SIZE + 1)
            free[y0:y0 + SIZE, x0:x0 + SIZE] = True
    edges = [((r, c), (r, c + 1)) for r in range(ROOMS) for c in range(ROOMS - 1)]
    edges += [((r, c), (r + 1, c)) for r in range(ROOMS - 1) for c in range(ROOMS)]
    order = rng.permutation(len(edges))
    parent = {(r, c): (r, c) for r in range(ROOMS) for c in range(ROOMS)}

    def find(u):
        while parent[u] != u:
            parent[u] = parent[parent[u]]
            u = parent[u]
        return u
    doors = []
    for i in order:
        u, v = edges[i]
        if find(u) != find(v):
            parent[find(u)] = find(v)
            doors.append(edges[i])
        elif rng.random() < 0.35:
            doors.append(edges[i])
    for (r, c), (r2, c2) in doors:
        k = int(rng.integers(SIZE))
        if r2 == r:   # east-west neighbours: opening in the vertical wall
            free[1 + r * (SIZE + 1) + k, (c + 1) * (SIZE + 1)] = True
        else:
            free[(r + 1) * (SIZE + 1), 1 + c * (SIZE + 1) + k] = True
    return free


def make_world(rng, P) -> World:
    free = _building(rng)
    cells = [(y, x) for y in range(G) for x in range(G) if free[y, x]]
    idx = {c: i for i, c in enumerate(cells)}
    n = len(cells)
    room_of = np.full(n, -1)
    for i, (y, x) in enumerate(cells):
        if y % (SIZE + 1) and x % (SIZE + 1):
            room_of[i] = (y // (SIZE + 1)) * ROOMS + x // (SIZE + 1)
    toks = []
    for j, (nm, (dy, dx)) in enumerate(MOVES.items()):
        tab = np.array([idx.get((y + dy, x + dx), i) for i, (y, x) in enumerate(cells)], dtype=np.uint8)
        toks.append(Token(nm, (j,), tab))
    base = Library(toks)
    T = base.tables()

    def dist_from(s):
        d = np.full(n, -1)
        d[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for t in range(4):
                v = T[t][u]
                if d[v] < 0:
                    d[v] = d[u] + 1
                    q.append(v)
        return d
    D = np.stack([dist_from(s) for s in range(n)])
    rooms = [np.nonzero(room_of == k)[0] for k in range(ROOMS * ROOMS)]
    rc = lambda k: divmod(k, ROOMS)
    pairs = [(a, b) for a in range(ROOMS * ROOMS) for b in range(ROOMS * ROOMS)
             if a != b and 1 <= abs(rc(a)[0] - rc(b)[0]) + abs(rc(a)[1] - rc(b)[1]) <= P["room_dist"]]
    perm = rng.permutation(len(pairs))
    nd, nt = P["n_disc_fam"], P["n_test_fam"]
    chosen = [pairs[i] for i in perm[:nd + nt]]

    def taskset(fams, fid0):
        specs, fam = [], []
        for f, (ra, rb) in enumerate(fams):
            got, tries = set(), 0
            while len(got) < P["per_fam"] and tries < 200:
                tries += 1
                s, g = int(rng.choice(rooms[ra])), int(rng.choice(rooms[rb]))
                if D[s, g] >= P["min_dist"]:
                    got.add((s, g))
            for s, g in sorted(got):
                specs.append(('pairs', ((s, g),)))
                fam.append(fid0 + f)
        return TaskSet(specs, np.array(fam))
    disc = taskset(chosen[:nd], 0)
    test = taskset(chosen[nd:], 1000)
    # history: shortest plans for short trips, found by the same breadth-first search over primitives
    trips = []
    while len(trips) < P["n_history"]:
        s = int(rng.integers(n))
        g = int(rng.integers(n))
        if 3 <= D[s, g] <= P["history_max"] and room_of[s] >= 0 and room_of[g] >= 0:
            trips.append(('pairs', ((s, g),)))
    ts = TaskSet(trips, np.zeros(len(trips), int))
    solved, _, progs = search(base, ts, 1e9, 1.0)
    hist = [p for p, ok in zip(progs, solved) if ok]
    return World(cells, room_of, base, hist, disc, test, chosen[:nd], chosen[nd:])
