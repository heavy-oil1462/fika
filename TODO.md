# TODO

## Phase 1 - foundation (this PR)

- [x] Repo conventions: params single source of truth, guards, flake
- [x] Layout CAD: frame, envelopes, hydraulic path, assembly, DXF/STL/PNG
- [x] Pipeline: regen_all + read-only verify gate + drift check
- [x] Firmware skeleton: base, packages, contracts, example + sim nodes
- [x] QEMU simulator with injection web page
- [x] Docs: SPECS, MATERIALS, PROTOCOL, HARDWARE, EXTENDING, concepts
- [ ] CI running the verify gate (deferred: the push token lacks the
      workflow scope; until then the gate runs locally before every push)

## Phase 2 - mechanical detail

- [ ] Frame joinery: tapped edges vs corner blocks, real hole patterns
- [ ] Boiler sourcing decision and exact port layout
- [ ] Pump/motor mounts, vibration isolation
- [ ] Group mount detail, portafilter clearance check against a real group
- [ ] Stainless drip tray, load cell mount detail
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
