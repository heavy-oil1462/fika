#!/usr/bin/env python3
"""fika simulation integration test - the REAL firmware, no hardware.

Compiles esphome/sim-fika.yaml (actual esp32 build), boots it under
Espressif QEMU against a throwaway authenticated mosquitto, drives it
through the web UI's HTTP API (harness: esphome_skills.sim_test), and
asserts that the on-device behavior holds:

    1. node comes up: retained status "online" + MQTT discovery
    2. injected sensor values surface under the real sensor ids
       (boiler_temp, cup_weight)
    3. moving the boiler_temp slider moves the boiler_temp state topic
    4. a 210 g cup on the scale changes the detected_cup text sensor
    5. brew/steam panel injections surface as the brew_switch/steam_switch
       binary sensors

Deliberately basic: it proves the injection -> firmware -> state-topic loop
end to end. Rule-level assertions (PID heater duty, gravimetric stop) can
grow here once those packages settle.

    sudo -E nix develop .#sim -c python3 tools/test_sim.py

Slow: one esp32 compile (cached in .esphome-sim/) plus a few minutes of
emulated boot and control-loop time. Not part of the default validation
gate. See the harness docstring for requirements (QEMU, udp/123,
mosquitto).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project import PROJECT  # noqa: E402

from esphome_skills.sim_test import run  # noqa: E402

# Retained injections published before the firmware boots: cold machine,
# empty tray, switches off.
BOOT = {"boiler_temp": 25, "cup_weight": 0,
        "brew_switch": 0, "steam_switch": 0}


def scenario(ctx) -> None:
    ctx.heading("2. injected sensors surface under real ids")
    boiler = ctx.wait_state("sensor/boiler_temp",
                            lambda v: v and abs(float(v) - 25) < 1)
    ctx.check(boiler is not None, "boiler_temp injection 25 C -> boiler_temp")
    cup = ctx.wait_state("sensor/cup_weight",
                         lambda v: v and abs(float(v)) < 1)
    ctx.check(cup is not None, "cup_weight injection 0 g -> cup_weight")

    ctx.heading("3. boiler_temp tracks the slider")
    ctx.inject(boiler_temp=93)
    boiler = ctx.wait_state("sensor/boiler_temp",
                            lambda v: v and abs(float(v) - 93) < 1,
                            timeout=120)
    ctx.check(boiler is not None, "boiler_temp state follows to 93 C")

    ctx.heading("4. cup recognition: 210 g on the scale")
    cup_topic = f"{ctx.prefix}/text_sensor/detected_cup/state"
    base = ctx.watcher.wait_for(cup_topic, timeout=90)
    ctx.check(base is not None, "detected_cup published a baseline state")
    baseline = base[0] if base else None
    ctx.inject(cup_weight=210)
    cup = ctx.wait_state("sensor/cup_weight",
                         lambda v: v and abs(float(v) - 210) < 1,
                         timeout=120)
    ctx.check(cup is not None, "cup_weight state follows to 210 g")
    detected = ctx.watcher.wait_for(
        cup_topic, lambda v: v and v != baseline, timeout=180)
    ctx.check(detected is not None,
              f"detected_cup changed from {baseline!r} "
              f"(now {ctx.watcher.messages.get(cup_topic, ('?',))[0]!r})")

    ctx.heading("5. panel switches surface as binary sensors")
    ctx.inject(brew_switch=1)
    brew = ctx.wait_state("binary_sensor/brew_switch", lambda v: v == "ON")
    ctx.check(brew is not None, "brew_switch 1 -> binary_sensor ON")
    ctx.inject(steam_switch=1)
    steam = ctx.wait_state("binary_sensor/steam_switch", lambda v: v == "ON")
    ctx.check(steam is not None, "steam_switch 1 -> binary_sensor ON")
    ctx.inject(brew_switch=0, steam_switch=0)
    brew = ctx.wait_state("binary_sensor/brew_switch", lambda v: v == "OFF")
    ctx.check(brew is not None, "brew_switch 0 -> binary_sensor OFF")


if __name__ == "__main__":
    sys.exit(run(PROJECT, scenario, boot_injections=BOOT))
