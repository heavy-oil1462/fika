---
name: verify
description: Verify the fika design end-to-end before committing - python
  byte-compile, params guard, software gate (yamllint, esphome config,
  fabrication tags, protocol table, cup logic mirror, temperature sweep,
  sim contract), full CAD regeneration with warnings as errors, STL
  watertightness and shell counts, layout clearances, energy budget
  assertions, and byte-for-byte drift of committed outputs/. One command,
  read-only. Use before every commit, after any cad/esphome/tools change,
  or when asked to check, validate or verify the repo.
---

# Verify the design

```bash
scripts/verify_design.sh
```

Read-only (writes only to a temp dir), exits non-zero on failure. Run it
before EVERY commit, and after `scripts/regen_all.py`. CI runs exactly
this script.

What it checks:

1. Python byte-compile (scripts/ tools/ sim/)
2. Params guard: no .scad shadows a cad/design_params.scad name
3. Software gate `tools/validate.py`: yamllint strict, `esphome config`
   on example + sim nodes, cad fabrication tags, PROTOCOL.md id table vs
   package Provides, cup logic mirror + unit tests, temperature
   substitutions vs design params, sim injection contract
4. Full regeneration into a temp dir; any OpenSCAD error or WARNING fails
5. STL watertightness and expected shell counts (manifest in
   scripts/regen_all.py)
6. Layout clearances and frame containment (scripts/check_layout.py)
7. Energy budget assertions (breaker margin, heat-up under 6 min)
8. Drift: the temp regeneration must byte-match committed outputs/

## Interpreting results

- Step 8 drift: run `python3 scripts/regen_all.py` and commit the new
  outputs/ together with your source change.
- Step 3 failures print the failing sub-check; run
  `python3 tools/validate.py <name>` to iterate on one check.
- Probe that the gate bites without editing files using env overrides:
  `FIKA_BOILER_OD=300 scripts/verify_design.sh` must fail step 6 (drift
  is skipped under overrides on purpose).
- Never fix a failing step by loosening its threshold.

## Notes (sandbox landmines)

- Steps 3 and 4 need the devshell toolchain. The script falls back to
  `nix develop` automatically; the first run downloads the toolchain and
  needs network. A missing toolchain is a FAILURE, not a skip.
- OpenSCAD and Mesa come from nix via scripts/render_scad.sh (EGL
  surfaceless, works headless). First render fetches them.
- `nix develop` requires the repo files to be tracked by git (nix flakes
  ignore untracked files; `git add` new files first).
