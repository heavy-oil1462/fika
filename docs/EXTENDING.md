# EXTENDING - adapt fika without forking it

The core rule from frodas applies unchanged: base and the stock packages
are never edited for a specific machine. Your configuration is a package
list plus substitutions.

## Your private fika-config

Keep your node config (pins, cup table, secrets) in a private repo
cloned inside your fika checkout; fika gitignores `fika-config/`:

    cd fika
    git clone <your-private-config-repo> fika-config
    esphome run fika-config/fika.yaml

Start it by copying `esphome/example-fika.yaml` and
`esphome/secrets.yaml.example`, keep the packages your build has
hardware for, and override substitutions:

    substitutions:
      cup1_name: lungo
      cup1_tare_g: "138.0"
      cup1_target_g: "90.0"
      heater_pin: GPIO25

    packages:
      base: !include ../esphome/fika-base.yaml
      radio: !include ../esphome/packages/radio-wifi.yaml
      # ... the stock list from example-fika.yaml

Alternatively use ESPHome remote packages pinned by ref against
github.com/heavy-oil1462/fika.

## Adding hardware

New hardware means a new package, not an edit. Write
`packages/sensor-<thing>.yaml` with the boxed banner (Substitutions and
Provides sections; the Provides ids are parsed by tools/validate.py) and
provide existing object_ids where you replace stock hardware: a package
that publishes `boiler_temp` in C is a drop-in boiler sensor whatever
the silicon (docs/PROTOCOL.md, interoperability rule).

## Adding a cup

The stock table has two cups as substitutions (cup_logic.yaml). More
cups currently means extending cup_logic.yaml's lambda and the mirror in
tools/cup_match.py together, plus tools/test_cup_match.py; the table is
deliberately substitutions-only until someone needs more than a few
cups. Keep tares at least 2 x cup_tolerance_g apart.

## Checks

Whatever you change: `python3 tools/validate.py`, and before any commit
`scripts/verify_design.sh` (the verify skill). CI runs exactly the same
gate.
