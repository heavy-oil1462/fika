---
name: hero-render
description: Re-render the photoreal README hero image (media/hero.png)
  from the CAD with correct materials via headless Blender Cycles. Use
  after any cad/ change that alters what the machine looks like, when
  asked for a beauty or hero render, or when tuning the hero scene
  (materials, lights, camera) in scripts/hero_scene.py.
---

# Render the hero image

```bash
python3 scripts/render_hero.py            # full quality -> media/hero.png
python3 scripts/render_hero.py --draft --out /tmp/draft.png   # iterate
```

How it works: OpenSCAD exports cad/main_assembly.scad as a colored 3MF,
scripts/render_hero.py splits the mesh into one PLY per color() tag
(the MATERIALS table maps hex color to material name), and headless
Blender renders the studio scene in scripts/hero_scene.py with Cycles
on CPU. Full quality takes on the order of 10 minutes; drafts about a
minute.

Rules:

- media/hero.png is a build product of this command: regenerate it in
  the same change that alters the CAD it depicts, never edit or
  hand-render it. It lives in media/, not outputs/, because Cycles
  output is not byte deterministic across machines and outputs/ is
  byte-drift-checked by the verify gate.
- Judge scene changes by looking at a --draft render, never by reading
  hero_scene.py. Only render full quality once the draft is right.
- Keep-in-sync sweep for material colors: a color() tag in cad/, the
  MATERIALS table in scripts/render_hero.py, and the PBR() definitions
  in scripts/hero_scene.py. A color missing from MATERIALS fails the
  split on purpose.
- The pinned nixpkgs channel is read from scripts/nixpkgs_channel,
  shared with scripts/render_scad.sh. Change it in that one file only.

## Interpreting results

- "untagged geometry: color #XXXXXX": someone added uncolored or
  newly colored geometry in cad/. Tag it with an existing material
  color, or add the new color to MATERIALS and a PBR() entry.
- Blender segfault with no output: LD_LIBRARY_PATH leaked into the
  environment; render_hero.py strips it, so this means the strip
  broke or blender was run by hand. Run via the script.
- 3MF export failure prints the OpenSCAD log; fix the .scad and use
  the openscad-review skill.

## Notes (sandbox landmines)

- The sandbox exports LD_LIBRARY_PATH=/lib, which makes the nix
  Blender segfault instantly with no error message. render_hero.py
  runs Blender with that variable removed.
- First run fetches Blender 4.4 from the nixpkgs binary cache
  (network, about a minute). A missing toolchain is a failure, not a
  skip.
- The ghost cup in main_assembly.scad uses the % modifier, so it is
  excluded from the 3MF export and the hero render on purpose.
