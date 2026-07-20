# Simulating the machine - the real firmware, no hardware

fika ships a simulator that is not a re-implementation of the control
logic: it is the actual firmware, compiled for a stock esp32dev board
and executed under Espressif's QEMU fork, wired to your MQTT broker and
therefore your Home Assistant. The cup recognition, gravimetric stop,
PID retargeting and fault latching you observe are made by the same C++
that runs in the machine.

```
+------------------------- podman container --------------------------+
|                                                                     |
|  +-------------------------------+      +------------------------+  |
|  | QEMU (machine esp32)          | SNTP | webui.py               |  |
|  |  REAL firmware:               |----->|  simulated clock       |  |
|  |  sim-fika.yaml                | :123 |  sensor injections     |  |
|  |  = fika-base                  |      |  live entity view      |  |
|  |  + radio-openeth (emu eth)    |      +-----------^------------+  |
|  |  + sim-sensors (injectable)   |                  | http :8080    |
|  |  + REAL logic/actuators       |                  |               |
|  +---------------+---------------+                  |               |
+------------------+----------------------------------+---------------+
                   | MQTT (discovery, telemetry,      |
                   v        retained setpoints)     browser
            YOUR broker ---> YOUR Home Assistant
```

The simulator engine (container build, web UI, QEMU glue) lives in the
shared [esphome-skills](https://github.com/heavy-oil1462/esphome-skills)
package; the fika side is `tools/project.py` (injections, presets, node
names) and `tools/test_sim.py` (assertions).

## Quickstart

```bash
python3 tools/sim_container.py build                # once (~minutes)
python3 tools/sim_container.py run \
    --broker 192.168.1.10 --username fika --password ...
python3 tools/sim_container.py logs                 # firmware serial console
```

Open http://localhost:8080: sliders for the boiler temperature and cup
weight, toggles for the brew and steam switches, presets (cold start,
ready with cup, brewing), and a live view of everything the node
publishes. The node appears in Home Assistant via MQTT discovery as
`sim-fika`, indistinguishable from hardware.

The first `run` compiles the firmware inside the container against your
broker settings; the cache volume makes later starts fast. If the
broker runs on the container host, use `--broker
host.containers.internal` (the entrypoint resolves it to an IP before
baking it into the firmware; QEMU's user-mode network cannot see
container DNS).

## How each input reaches the real firmware

| Input | Mechanism |
|---|---|
| Sensor values | Retained MQTT topics `fika/<node>/sim/<key>`; packages/sim-sensors.yaml subscribes with the real entity ids (`boiler_temp`, `cup_weight`, `brew_switch`, `steam_switch`) so the stock logic packages run unmodified |
| Time of day | webui.py answers the firmware's SNTP queries (`sntp_server: 10.0.2.2`, re-sync every 15 s) with an offset clock |
| Setpoints | Nothing special: the standard retained command topics (PROTOCOL.md); edit `brew_target_weight` from HA or the UI like on hardware |

Until a value is injected a sensor has no state (NaN) and the
fail-safes behave exactly as with broken hardware: after
`sensor_grace_s` of NaN boiler readings, safety.yaml latches a fault.

Things worth trying: set the boiler to 93 and a cup of 210 g and watch
`detected_cup` flip to cappuccino and the lamp logic report ready; flip
brew and pour by raising cup_weight toward 360 g to see the gravimetric
stop; push the boiler past 135 to watch the fault latch kill the heater.

## The automated version: tools/test_sim.py

The same loop, CI-style: throwaway authenticated mosquitto, web UI
driven over HTTP, assertions on the broker:

```bash
sudo -E nix develop .#sim -c python3 tools/test_sim.py
```

Asserts boot + discovery, boiler_temp and cup_weight injection round
trips, cup recognition reacting to a 210 g cup, and switch injections
reaching their binary sensors. Requirements: an esphome that can
compile, `qemu-esp32` (in the `.#sim` devshell via the
nix-qemu-espressif flake input; kept out of the default shell because
it may build QEMU from source once), and the ability to bind udp/123
(root/CAP_NET_BIND_SERVICE; lwIP's SNTP port is not configurable).
Slow (a compile plus emulated boot time); deliberately not part of the
default validation gate.

## Limitations

- Not cycle-accurate: QEMU timing is roughly wall clock; good enough
  for second-scale brew logic, do not benchmark the PID on it.
- GPIO goes nowhere: the SSR, pump relay and valve drive emulated pins;
  observe actuators via their entities (which is what HA sees too).
- The PID heats nothing: boiler_temp only changes when you move the
  slider, so closed-loop thermal behavior cannot be studied, only the
  mode/setpoint/fault logic around it.
- OTA and safe mode exist but are pointless in a container that
  rebuilds from source each config change.
