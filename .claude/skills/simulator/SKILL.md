---
name: simulator
description: Run the REAL fika firmware under Espressif QEMU in a
  container, with a debug web page that injects sensor values (boiler
  temperature, cup weight, brew/steam switches) over MQTT and shows the
  machine react. Use to try control logic without hardware, rehearse HA
  automations against a protocol-faithful node, or run the automated
  sim test. Not a mock: the same C++ as the hardware.
---

# Run the simulator

```bash
python3 tools/sim_container.py build      # image with QEMU + toolchain (once)
python3 tools/sim_container.py run --broker <mqtt-host> \
    --username <user> --password <pass>
python3 tools/sim_container.py logs       # firmware serial console
python3 tools/sim_container.py stop
```

Web UI at http://localhost:8080: sliders for boiler_temp (C) and
cup_weight (g), brew/steam toggles, presets (cold start, ready with
cup, brewing), a time-of-day control backed by a fake SNTP server, and
a live entity view. Architecture and what to try: docs/SIMULATION.md.

Automated end-to-end test (compile + QEMU boot + injections):

```bash
sudo -E nix develop .#sim -c python3 tools/test_sim.py
```

## What it proves

- The composition boots and speaks the PROTOCOL.md contract (discovery,
  status, state topics).
- Cup recognition, gravimetric stop, steam interlock and fault latching
  behave as designed, in the real compiled firmware.
- It does NOT prove thermal behavior: nothing heats, boiler_temp is a
  slider. PID tuning happens on hardware (TODO phase 4).

## Interpreting results

- Injection has no effect: check the key spelling against
  docs/PROTOCOL.md sim topics; `python3 tools/validate.py sim` asserts
  the web UI and firmware agree.
- Entities missing in HA: the node publishes discovery retained; check
  the broker credentials passed to `run` and that HA uses the same
  broker.

## Notes (sandbox landmines)

- The sim composition needs the QEMU stability block in sim-fika.yaml
  (flash_write_interval 100000h, single-core sdkconfig, task WDT 60 s);
  QEMU asserts and crashloops without it. Never copy that block to
  hardware nodes.
- test_sim.py binds udp/123 for SNTP (needs root or
  CAP_NET_BIND_SERVICE) and tcp/1883 for the throwaway broker.
- qemu-esp32 lives in the `.#sim` devshell only; the first entry may
  build QEMU from source (~20 min).
- The entrypoint resolves the broker hostname to an IP before compiling
  (QEMU user-net cannot resolve container DNS names).
