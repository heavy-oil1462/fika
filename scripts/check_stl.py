#!/usr/bin/env python3
"""Watertightness and shell count check for the exported STLs.

Stdlib STL parser (ASCII and binary). A healthy part is watertight
(every edge shared by exactly two facets) and has exactly the number of
shells the manifest in scripts/regen_all.py expects (the hydraulic path
is four separate copper runs on purpose).

Usage:
    scripts/check_stl.py <file.stl> <expected_shells>
    scripts/check_stl.py --all <stl_dir>     # every part in the manifest

Exit 1 on any violation.
"""

import struct
import sys
from collections import Counter
from pathlib import Path


def read_triangles(path: Path):
    data = path.read_bytes()
    if data[:6].lstrip().startswith(b"solid"):
        text = data.decode(errors="replace")
        if "facet" in text:
            tris, cur = [], []
            for line in text.splitlines():
                parts = line.split()
                if parts[:1] == ["vertex"]:
                    cur.append(tuple(parts[1:4]))
                    if len(cur) == 3:
                        tris.append(tuple(cur))
                        cur = []
            return tris
    count = struct.unpack_from("<I", data, 80)[0]
    tris = []
    for i in range(count):
        off = 84 + i * 50 + 12
        vs = struct.unpack_from("<9f", data, off)
        tris.append((vs[0:3], vs[3:6], vs[6:9]))
    return tris


def analyze(path: Path):
    tris = read_triangles(path)
    parent = {}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    edges = Counter()
    for tri in tris:
        for v in tri:
            parent.setdefault(v, v)
        union(tri[0], tri[1])
        union(tri[1], tri[2])
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            edges[frozenset((a, b))] += 1

    shells = len({find(v) for v in parent})
    open_edges = sum(1 for n in edges.values() if n != 2)
    return len(tris), shells, open_edges


def check(path: Path, expected_shells: int) -> bool:
    ntris, shells, open_edges = analyze(path)
    problems = []
    if open_edges:
        problems.append(f"{open_edges} non-manifold edges")
    if shells != expected_shells:
        problems.append(f"{shells} shells, expected {expected_shells}")
    if problems:
        print(f"[FAIL] {path.name}: {', '.join(problems)} ({ntris} facets)")
        return False
    print(f"ok: {path.name}: watertight, {shells} shell(s), {ntris} facets")
    return True


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--all":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from regen_all import PARTS
        stl_dir = Path(sys.argv[2])
        good = all(check(stl_dir / f"{p['name']}.stl", p["shells"])
                   for p in PARTS)
        return 0 if good else 1
    if len(sys.argv) == 3:
        return 0 if check(Path(sys.argv[1]), int(sys.argv[2])) else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
