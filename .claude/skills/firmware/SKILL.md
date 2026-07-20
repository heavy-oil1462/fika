---
name: firmware
description: Build, validate, flash and debug the fika ESPHome firmware.
  Use for esphome config/compile/run/logs, secrets provisioning, adding
  or editing firmware packages, or wiring a private fika-config node.
  Packages compose via substitutions and id contracts - never edit base
  or stock packages for one machine.
---

# Firmware workflow

All commands from the devshell (`nix develop`), in `esphome/`:

```bash
esphome config example-fika.yaml    # validate composition (fast)
esphome compile example-fika.yaml   # full C++ build
esphome run example-fika.yaml       # flash over USB / OTA
esphome logs example-fika.yaml
```

Secrets: `cp secrets.yaml.example secrets.yaml` and fill in
(tools/validate.py auto-provisions placeholders for config checks).

## Editing rules

- fika-base.yaml and packages/ are generic. Machine-specific values
  (pins, cup tares, credentials) belong in a private fika-config node
  config via substitutions (docs/EXTENDING.md).
- New hardware = new package with the boxed banner (Substitutions +
  Provides). Provides ids must appear in the docs/PROTOCOL.md table;
  `python3 tools/validate.py protocol` enforces both directions.
- The cup matching lambda in packages/cup_logic.yaml mirrors
  tools/cup_match.py line for line; change both together plus
  tools/test_cup_match.py (`validate cups` pins the tolerance).
- brew_temp_c / steam_temp_c / max_temp_c also live in
  cad/design_params.scad; `validate temps` owns that sweep.
- Actuators: default off at boot, never on a strapping pin, never
  retained commands (docs/PROTOCOL.md retention rules).

After any change: `python3 tools/validate.py yaml esphome protocol cups
temps`, then the verify skill before committing.

## Interpreting results

- `esphome config` failures print the last 30 lines via validate; run
  the raw command for full context.
- Cross-package id errors ("Couldn't find ID") mean a composition is
  missing the providing package - check the node's package list against
  docs/PROTOCOL.md's provided-by column.

## Notes (sandbox landmines)

- esphome comes from nixpkgs; `esphome compile` downloads the ESP-IDF
  toolchain into .esphome/ on first use (large, needs network).
- `nix develop` only sees git-tracked files; `git add` new packages
  before validating inside the devshell.

Shared engine: the esphome-skills package (flake input); repo side
is tools/project.py plus the thin entry points in tools/.
Canonical doc and cross-repo landmines: https://github.com/heavy-oil1462/esphome-skills/blob/main/skills/firmware.md
