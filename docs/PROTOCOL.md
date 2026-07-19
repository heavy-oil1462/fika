# PROTOCOL - the MQTT and entity id contract

This file is the contract between the firmware packages, the simulator,
Home Assistant, and any future consumer. If you change a semantic here,
change every producer and consumer in the same commit. tools/validate.py
(`protocol` check) asserts that the id table below exactly matches the
`Provides:` declarations in `esphome/packages/*.yaml`.

## Naming chain

One name flows through the whole stack. Rename only with a sweep across
all of them:

    entity name "Boiler Temperature"
      -> object_id boiler_temp
      -> MQTT topic fika/<node>/sensor/boiler_temp/state
      -> Home Assistant entity sensor.<node>_boiler_temperature

Topic tree: `<mqtt_root>/<node>/<component>/<object_id>/{state,command}`
with `mqtt_root` = `fika`. Text sensors pin their `state_topic`
explicitly so they never land in `sensor/` (see fika-base.yaml).

The temperature setpoints (`brew_temp_c`, `steam_temp_c`, `max_temp_c`)
also span `cad/design_params.scad` and the packages; tools/validate.py
(`temps` check) owns that sweep set.

## Retention rules

- Setpoints are retained (`brew_target_weight`): they must survive a
  restart or broker outage.
- Actuator commands are never retained (`pump`, `brew_valve`,
  `steam_mode`): a replayed command must not start a pump.
- `fika/<node>/status` is retained online/offline (broker LWT).
- Discovery messages are retained (`discovery_retain: true`).

All control loops run on the ESP32. MQTT and Home Assistant are
observation and setpoint adjustment only; the machine brews with the
network down.

## Entity id contract

| object_id | type | unit | retained command | provided by |
|---|---|---|---|---|
| boiler_temp | sensor | C | - | boiler_sensor, sim-sensors |
| boiler | climate | C | no | boiler_pid |
| heater_duty | sensor | % | - | boiler_pid |
| steam_mode | switch | - | no | steam_mode |
| pump | switch | - | no | pump |
| brew_valve | switch | - | no | brew_valve |
| cup_weight | sensor | g | - | cup_scale, sim-sensors |
| scale_tare | button | - | no | cup_scale |
| detected_cup | text_sensor | - | - | cup_logic |
| brew_target_weight | number | g | yes | cup_logic |
| beverage_weight | sensor | g | - | cup_logic |
| brewing | binary_sensor | - | - | cup_logic |
| brew_switch | binary_sensor | - | - | switches, sim-sensors |
| steam_switch | binary_sensor | - | - | switches, sim-sensors |
| machine_status | text_sensor | - | - | status |
| fault | binary_sensor | - | - | safety |

Interoperability rule: swapping hardware means writing a package that
provides the same object_id with the same unit. Nothing else may need to
change.

`machine_status` values: `heating`, `ready`, `brewing`, `steam`,
`fault`. `detected_cup` values: a calibrated cup name or `none`.

## Simulator injection topics

The simulator (docs/SIMULATION.md) feeds sensors through retained
topics of the form `fika/<node>/sim/<key>`:

    fika/sim-fika/sim/boiler_temp     float C
    fika/sim-fika/sim/cup_weight      float g
    fika/sim-fika/sim/brew_switch     0/1
    fika/sim-fika/sim/steam_switch    0/1

tools/validate.py (`sim` check) asserts these keys equal the web UI's
INJECTIONS and the mqtt_subscribe topics in packages/sim-sensors.yaml.
