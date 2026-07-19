---
name: openscad-review
description: Render and review the OpenSCAD models in cad/ headlessly
  (via nix, no GUI needed). Use after any .scad change, or when asked to
  verify or review the CAD. Checks compile warnings, manifold geometry,
  visual correctness against the layout, and fika's design rules. Never
  approve a .scad edit from source reading alone - render it and look.
---

# Review the CAD

Gate first, then render what changed and LOOK at the image:

```bash
python3 scripts/check_params.py
scripts/render_scad.sh cad/main_assembly.scad /tmp/review.png \
    --camera=0,160,190,70,0,25,1200
scripts/render_scad.sh cad/<part>.scad /tmp/part.stl   # manifold check
```

Then Read the PNG. For STL exports the log must end with
`Status: NoError`; `python3 scripts/check_stl.py <file.stl> <shells>`
checks watertightness and shell count (expected counts live in the
scripts/regen_all.py manifest).

DXF profiles for CNC parts:

```bash
scripts/render_scad.sh cad/frame.scad /tmp/side.dxf -D 'export_profile="side"'
```

Assembly display toggles (show_frame, show_boiler, show_pump,
show_group, show_tray, show_tank, show_plumbing, show_cup) are
assembly-local; flip them with -D to isolate a subsystem.

## Project design rules to verify

- Every shared dimension comes from cad/design_params.scad; part files
  never declare their own copy (check_params enforces).
- Every part header: Purpose, Material, Fabrication: cnc|print|cots|
  lib|assembly. Pressure/thermal parts are cots, never print.
- The frame is open (concepts/open-frame.md): a member exists only if
  it carries a component, and no panel, cover or back wall is allowed
  back in. Copper is a visible surface, so route it to be looked at.
- One bolt size (bolt_hole_d) for every frame joint.
- Library files (cad/lib/) are pure modules with no top-level geometry.
- Positions in main_assembly.scad must mirror scripts/check_layout.py
  (they both derive from design params; a divergence is a bug).
- The cup zone under the group stays cup_clearance_h tall; the front of
  the frame is open by design (handle and wand poke out).

## Notes (sandbox landmines)

- Library files render empty on their own; review them through a
  consumer part or the assembly.
- render_scad.sh pins nixpkgs and renders through EGL surfaceless
  software GL; first use downloads OpenSCAD + Mesa.
