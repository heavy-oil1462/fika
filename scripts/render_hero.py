#!/usr/bin/env python3
"""Render the photoreal hero image - media/hero.png.

    python3 scripts/render_hero.py [--draft] [--out FILE]

Pipeline: OpenSCAD exports the master assembly as a colored 3MF (the
color() tags in cad/ are the material tags), this script splits the
mesh into one PLY per material, and headless Blender (Cycles, CPU)
renders the scene defined in scripts/hero_scene.py.

The result goes to media/, not outputs/: Cycles output is not byte
deterministic across machines, so it cannot live under the byte drift
gate. media/ is still a build product - regenerate it in the same
change that alters the CAD it depicts, never edit it by hand.

--draft renders small and fast for iterating on the scene; the default
is the committed quality.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design_params import scad_overrides  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / "scripts" / "render_scad.sh"
SCENE = ROOT / "scripts" / "hero_scene.py"
CHANNEL = (ROOT / "scripts" / "nixpkgs_channel").read_text().strip()

# 3MF displaycolor (from the color() tags in cad/) -> material name.
# hero_scene.py owns the PBR definition for each name; if a new color
# appears in cad/, add it here and there in the same change.
MATERIALS = {
    "C8A165": "oak",
    "C0C0C0": "aluminum",
    "B87333": "copper",
    "B5A642": "brass",
    "555555": "steel",
    "333333": "printed",
    "999999": "loadcell",
    "8899AA": "tank",
}

M3MF = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}


def export_3mf(out: Path) -> None:
    proc = subprocess.run(
        [str(RENDER), str(ROOT / "cad" / "main_assembly.scad"), str(out),
         *scad_overrides()],
        capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0 or "WARNING" in proc.stdout + proc.stderr:
        sys.exit(f"[FAIL] 3MF export:\n{proc.stdout}{proc.stderr}")


def split_by_material(threemf: Path, mesh_dir: Path) -> list[Path]:
    """One ascii PLY per material color; die on untagged geometry."""
    root = ET.fromstring(zipfile.ZipFile(threemf).read("3D/3dmodel.model"))
    colors = [b.get("displaycolor").lstrip("#")[:6]
              for b in root.findall(".//m:basematerials/m:base", M3MF)]
    verts = [(float(v.get("x")), float(v.get("y")), float(v.get("z")))
             for v in root.findall(".//m:vertices/m:vertex", M3MF)]
    groups: dict[int, list] = defaultdict(list)
    for t in root.findall(".//m:triangles/m:triangle", M3MF):
        groups[int(t.get("p1"))].append(
            (int(t.get("v1")), int(t.get("v2")), int(t.get("v3"))))

    plys = []
    for idx, tris in sorted(groups.items()):
        color = colors[idx]
        name = MATERIALS.get(color)
        if name is None:
            sys.exit(f"[FAIL] untagged geometry: color #{color} in the 3MF "
                     f"has no entry in MATERIALS - every member gets a "
                     f"color() material tag in cad/")
        remap: dict[int, int] = {}
        for tri in tris:
            for i in tri:
                remap.setdefault(i, len(remap))
        local = sorted(remap, key=remap.get)
        out = mesh_dir / f"{name}.ply"
        with out.open("w") as f:
            f.write("ply\nformat ascii 1.0\n"
                    f"element vertex {len(local)}\n"
                    "property float x\nproperty float y\nproperty float z\n"
                    f"element face {len(tris)}\n"
                    "property list uchar int vertex_indices\nend_header\n")
            for i in local:
                f.write("%.4f %.4f %.4f\n" % verts[i])
            for a, b, c in tris:
                f.write(f"3 {remap[a]} {remap[b]} {remap[c]}\n")
        plys.append(out)
        print(f"ok: {name}.ply ({len(tris)} triangles)")
    return plys


def blender_bin() -> str:
    # $BLENDER, then blender on PATH, then nix (same resolution idea as
    # scripts/render_scad.sh; any Blender 4.x works)
    if os.environ.get("BLENDER"):
        return os.environ["BLENDER"]
    on_path = shutil.which("blender")
    if on_path:
        return on_path
    store = subprocess.run(
        ["nix-build", "-I", f"nixpkgs={CHANNEL}", "<nixpkgs>", "-A",
         "blender", "--no-out-link"],
        capture_output=True, text=True, check=True).stdout.strip().splitlines()[-1]
    return f"{store}/bin/blender"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "media" / "hero.png")
    ap.add_argument("--draft", action="store_true",
                    help="640x480, few samples, for scene iteration")
    args = ap.parse_args()
    width, height, samples = (640, 480, 24) if args.draft else (1920, 1440, 128)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        mesh_dir = Path(tmp)
        export_3mf(mesh_dir / "assembly.3mf")
        split_by_material(mesh_dir / "assembly.3mf", mesh_dir)

        # the sandbox's LD_LIBRARY_PATH segfaults nix blender - drop it
        env = {k: v for k, v in os.environ.items() if k != "LD_LIBRARY_PATH"}
        proc = subprocess.run(
            [blender_bin(), "-b", "-noaudio", "--factory-startup",
             "--python", str(SCENE), "--",
             str(mesh_dir), str(args.out), str(width), str(height),
             str(samples)],
            env=env, capture_output=True, text=True)
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-12:])
        if proc.returncode != 0 or not args.out.exists():
            sys.exit(f"[FAIL] blender render:\n{tail}")
        print(tail)
    shown = args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) \
        else args.out
    print(f"\nok: {shown} ({width}x{height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
