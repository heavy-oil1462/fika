#!/usr/bin/env python3
"""Rebuild every derived artifact - the single regeneration entry point.

    python3 scripts/regen_all.py [--out-dir DIR] [part ...]

Stages, in order (all driven by the PARTS manifest below):
  1. gate on scripts/check_params.py (no shadowed dimensions)
  2. print the effective design parameters (env overrides marked)
  3. STL per part            -> outputs/stl/<name>.stl
  4. DXF per CNC profile     -> outputs/dxf/<file>_<profile>.dxf
  5. PNG reference renders   -> outputs/png/<name>.png (fixed cameras)
  6. energy budget           -> outputs/budgets/energy_budget.md

Everything under outputs/ is a committed build product: regenerate it in
the same change that alters cad/ or the budget inputs, never edit it by
hand. Any OpenSCAD WARNING fails the run. FIKA_* env overrides are
forwarded to OpenSCAD as -D, so one env var flips the whole pipeline.

Adding a part is one manifest line (name, expected STL shell count,
optional DXF profiles). Keep shells honest: the hydraulic path really is
four separate copper runs.
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design_params import scad_overrides  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / "scripts" / "render_scad.sh"

PARTS = [
    # base, rails and deck bolt face to face, so the frame unions into
    # one solid rather than four loose plates
    {"name": "frame", "shells": 1,
     "profiles": ["base", "rail", "deck"]},
    {"name": "boiler", "shells": 1},
    {"name": "pump", "shells": 1},
    {"name": "group", "shells": 1},
    {"name": "drip_tray", "shells": 1},
    {"name": "tank", "shells": 1},
    {"name": "hydraulic_path", "shells": 4},
]

# fixed cameras so the committed PNGs are reproducible
PNGS = [
    ("main_assembly", "--camera=0,160,190,70,0,25,1200"),
    ("hydraulic_path", "--camera=0,160,190,70,0,25,1200"),
]


def render(scad: Path, out: Path, extra: list[str]) -> bool:
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(RENDER), str(scad), str(out), *extra, *scad_overrides()],
        capture_output=True, text=True, cwd=ROOT)
    log = proc.stdout + proc.stderr
    if proc.returncode != 0:
        print(f"[FAIL] {scad.name} -> {out.name}:\n{log}")
        return False
    if "WARNING" in log:
        print(f"[FAIL] {scad.name} -> {out.name} rendered with warnings:")
        print("\n".join(l for l in log.splitlines() if "WARNING" in l))
        return False
    print(f"ok: {out.relative_to(out.parent.parent.parent)}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "outputs")
    ap.add_argument("parts", nargs="*",
                    help="limit to these part names (default: everything)")
    args = ap.parse_args()
    out = args.out_dir

    gate = subprocess.run([sys.executable, str(ROOT / "scripts/check_params.py")])
    if gate.returncode != 0:
        return 1
    subprocess.run([sys.executable, str(ROOT / "scripts/design_params.py")])
    print()

    selected = [p for p in PARTS if not args.parts or p["name"] in args.parts]
    good = True
    for part in selected:
        scad = ROOT / "cad" / f"{part['name']}.scad"
        good &= render(scad, out / "stl" / f"{part['name']}.stl", [])
        for profile in part.get("profiles", []):
            good &= render(scad, out / "dxf" / f"{part['name']}_{profile}.dxf",
                           ["-D", f'export_profile="{profile}"'])
    if not args.parts:
        for name, camera in PNGS:
            good &= render(ROOT / "cad" / f"{name}.scad",
                           out / "png" / f"{name}.png", [camera])
        budget = subprocess.run(
            [sys.executable, str(ROOT / "tools/energy_budget.py"),
             "--out", str(out / "budgets" / "energy_budget.md")],
            capture_output=True, text=True)
        if budget.returncode != 0:
            print(f"[FAIL] energy_budget.py:\n{budget.stdout}{budget.stderr}")
            good = False
        else:
            print("ok: budgets/energy_budget.md")

    if not good:
        print("\n[FAIL] regeneration incomplete - fix the items above")
        return 1
    print("\nall derived artifacts regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
