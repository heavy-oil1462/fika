"""fika project declaration.

Single source of truth for the names the shared esphome-skills tools need:
topic root, node names, compositions, sim injections and presets. Injection
keys are the sim/<key> topics of esphome/packages/sim-sensors.yaml
(validate's sim check enforces the match). Switches are 0/1 floats:
sim-sensors.yaml mirrors them into template binary_sensors.
"""

from pathlib import Path

from esphome_skills import Project

PROJECT = Project(
    name="fika",
    device="espresso machine",
    mqtt_root="fika",
    sim_node="sim-fika",
    sim_yaml="sim-fika.yaml",
    compositions=("example-fika.yaml", "sim-fika.yaml"),
    injections={
        "boiler_temp": ("Boiler Temperature", "°C", 15.0, 150.0, 0.5, 25.0),
        "cup_weight": ("Cup Weight", "g", 0.0, 1000.0, 1.0, 0.0),
        "brew_switch": ("Brew Switch", "", 0.0, 1.0, 1.0, 0.0),
        "steam_switch": ("Steam Switch", "", 0.0, 1.0, 1.0, 0.0),
    },
    presets={
        "Cold start": {"boiler_temp": 20, "cup_weight": 0,
                       "brew_switch": 0, "steam_switch": 0},
        "Ready with cup": {"boiler_temp": 93, "cup_weight": 210},
        "Brewing": {"boiler_temp": 93, "cup_weight": 210, "brew_switch": 1},
    },
    repo_root=Path(__file__).resolve().parent.parent,
    python_dirs=("scripts", "tools"),
)
