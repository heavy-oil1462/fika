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
before EVERY commit, and after `scripts/regen_all.py`. This script is
the CI contract: .github/workflows/design.yml runs it in full on
CAD-side changes (pip toolchain plus the OpenSCAD snapshot AppImage, no
nix), and validate.yml runs the software gate on every change. CI
confirms the local run, it does not replace it.

What it checks:

1. Python byte-compile (scripts/ tools/)
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
   (only compared when the resolved OpenSCAD version equals
   outputs/openscad_version.txt; otherwise it self-skips with a notice)

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

- Nix is optional. Steps 1 and 3 need esphome, yamllint and the
  esphome_skills package: from PATH (pip install -r requirements.txt)
  or, as fallback, `nix develop` automatically (first run downloads the
  toolchain, needs network). A missing toolchain is a FAILURE, not a
  skip.
- OpenSCAD resolves as $OPENSCAD, then a 2024+ openscad on PATH, then
  nix (openscad-unstable + Mesa, EGL surfaceless, works headless; first
  render fetches them). Byte drift (step 8) only compares when the
  resolved version equals outputs/openscad_version.txt; otherwise it
  self-skips with a notice while steps 4-7 still run at full strength.
- `nix develop` requires the repo files to be tracked by git (nix flakes
  ignore untracked files; `git add` new files first).

Shared engine: the esphome-skills package (flake input); repo side
is tools/project.py plus the thin entry points in tools/.
Canonical doc and cross-repo landmines: https://github.com/heavy-oil1462/esphome-skills/blob/main/skills/verify.md
