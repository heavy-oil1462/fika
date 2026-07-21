# TODO

## Phase 1 - foundation (this PR)

- [x] Repo conventions: params single source of truth, guards, flake
- [x] Layout CAD: frame, envelopes, hydraulic path, assembly, DXF/STL/PNG
- [x] Pipeline: regen_all + read-only verify gate + drift check
- [x] Firmware skeleton: base, packages, contracts, example + sim nodes
- [x] QEMU simulator with injection web page
- [x] Docs: SPECS, MATERIALS, PROTOCOL, HARDWARE, EXTENDING, concepts
- [x] CI running the verify gate (.github/workflows/: validate on every
      change, the full design gate and the firmware build path-filtered;
      no nix in CI - pip plus the OpenSCAD snapshot AppImage, byte drift
      self-skips unless the version matches outputs/)

## Phase 2 - mechanical detail

- [ ] Rail stiffness: the deck is a balanced beam on two slender rails,
      so size the rails properly or add gussets at the slab and deck
- [ ] Frame joinery: threaded inserts in the oak, real hole patterns
- [ ] Boiler seat detail: a collar in the deck bore, not a bare hole
- [ ] Boiler sourcing decision and exact port layout
- [ ] Pump/motor mounts, vibration isolation into the oak
- [ ] Group mount detail, portafilter clearance check against a real group
- [ ] Stainless drip tray, load cell mount detail
- [ ] Steam wand articulation and an oak grip on the wand
- [ ] Copper routing detail with real bend radii, mesh interference check

## Phase 3 - electronics bring-up

- [ ] Bench: ESP32 + MAX31865 + HX711 + relays on a board
- [ ] Scale calibration procedure validated, cup table for real cups
- [ ] Mains box: SSR heatsinking, contactor, safety chain wiring

## Phase 4 - firmware maturation

- [ ] PID tuning against the real boiler
- [ ] Pre-infusion and shot timing, pressure sensing decision
- [ ] MQTT protocol integration test (port frodas test_protocol.py)
- [ ] HA dashboard package

## Phase 5 - full build

- [ ] Assembly, plumbing, first shots
- [ ] Steam wand articulation
- [ ] Documentation photos, build guide
