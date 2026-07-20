---
name: regen-outputs
description: Regenerate ALL derived artifacts (STL, DXF profiles, assembly
  PNGs, energy budget) in one command after any cad/ or budget-input
  change. Everything in outputs/ is a build product - regenerate and
  commit it with the source change, never edit or hand-render. Use after
  editing any .scad file, design_params.scad, or tools/energy_budget.py.
---

# Regenerate all derived outputs

```bash
python3 scripts/regen_all.py
```

Options: `--out-dir DIR` (used by the verify gate), or part names to
limit (`python3 scripts/regen_all.py group frame`; PNGs and budgets only
run on full runs).

What it does, in order:

1. Gates on scripts/check_params.py (shadowed dimensions fail)
2. Prints the effective parameters (FIKA_* env overrides marked)
3. STL per part from the manifest -> outputs/stl/
4. DXF per CNC profile -> outputs/dxf/ (feed these to PrintNC CAM)
5. Fixed-camera PNGs -> outputs/png/ (reference renders; the README
   hero is separate, see the hero-render skill)
6. Energy budget -> outputs/budgets/energy_budget.md

Any OpenSCAD WARNING fails the run. Adding a part is one line in the
PARTS manifest (scripts/regen_all.py): name, expected shell count,
optional DXF profile list.

## Interpreting results

- A render failure prints the OpenSCAD log; fix the .scad, rerun.
- After a successful run, `git status` should show only intended
  outputs/ changes; commit them with the source change so the verify
  gate's drift check stays green.
- Never hand-run individual openscad commands; this manifest is the
  contract for what exists.

## Notes (sandbox landmines)

- scripts/render_scad.sh fetches OpenSCAD + Mesa from nixpkgs on first
  use (network). It renders via EGL surfaceless with software GL, which
  is why no GUI or X server is needed.
- Committed PNGs are byte-compared by the verify gate. The camera args
  in the manifest are part of the contract; do not tweak them casually.
