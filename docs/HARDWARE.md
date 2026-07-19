# HARDWARE - electronics, pins and wiring

The mechanical and hydraulic BOM lives in MATERIALS.md. This file covers
the control electronics around the ESP32. Mains wiring is sketched here
for the contract only; SPECS.md section 5 and
concepts/safety-architecture.md define the safety chain that must exist
regardless of what the firmware does.

## Bill of materials (electronics)

| Qty | Part | Notes | ~Cost |
|---|---|---|---|
| 1 | ESP32 devkit (esp32dev) | the brain, 5 V USB supply | 5 EUR |
| 1 | Mean Well RS-15-5 or similar | 5 V PSU from mains | 10 EUR |
| 1 | SSR 25 A zero-crossing + heatsink | heater element switch | 10 EUR |
| 1 | Mechanical thermal cutoff, manual reset | on boiler shell, opens above max_temp_c | 5 EUR |
| 1 | Thermal fuse, one-shot | last resort, in series with the cutoff | 2 EUR |
| 1 | Relay/contactor, 230 V coil rating for motor load | pump motor switch | 8 EUR |
| 1 | Relay or MOSFET board | brew solenoid drive | 3 EUR |
| 1 | PT100 probe, M4 stud or pocket mount | boiler temperature | 8 EUR |
| 1 | MAX31865 breakout | PT100 amplifier, SPI | 5 EUR |
| 1 | TAL220 bar load cell, 1 kg | under the drip tray | 5 EUR |
| 1 | HX711 breakout | load cell amplifier | 3 EUR |
| 2 | Solid metal toggle switch | brew and steam controls | 8 EUR |
| 1 | Indicator lamp, 5 V | ready light | 2 EUR |
| 1 | Piezo buzzer, active | shot-finished beep | 1 EUR |

## Default pin map

Every pin is a substitution so a private fika-config can rewire without
touching the packages. Constraint column rules are hard: actuators must
never sit on strapping pins (GPIO0/2/12/15) that glitch at boot, and
GPIO34-39 are input only with no internal pulls.

| Function | GPIO | Substitution | Constraint |
|---|---|---|---|
| Heater SSR | GPIO25 | heater_pin | never a strapping pin |
| Pump relay | GPIO26 | pump_pin | never a strapping pin |
| Brew solenoid | GPIO27 | valve_pin | never a strapping pin |
| SPI clock | GPIO18 | spi_clk_pin | - |
| SPI MISO | GPIO19 | spi_miso_pin | - |
| SPI MOSI | GPIO23 | spi_mosi_pin | - |
| MAX31865 CS | GPIO5 | max31865_cs_pin | strapping pin, input at boot is fine for CS |
| HX711 DOUT | GPIO32 | hx711_dout_pin | - |
| HX711 SCK | GPIO33 | hx711_clk_pin | - |
| Brew switch | GPIO34 | brew_switch_pin | input only, external pull-down |
| Steam switch | GPIO35 | steam_switch_pin | input only, external pull-down |
| Ready lamp | GPIO21 | lamp_pin | - |
| Buzzer | GPIO22 | buzzer_pin | - |

## Wiring overview

    mains 230 V ---+--- 5 V PSU --- ESP32
                   |
                   +--- thermal cutoff --- thermal fuse --- SSR --- heater element
                   |                                         ^
                   |                                         | GPIO25
                   +--- contactor --- pump motor             |
                             ^                             ESP32
                             | GPIO26 (coil via driver)
                             |
                   +--- solenoid valve (via relay, GPIO27)

    ESP32 SPI (18/19/23/5) --- MAX31865 --- PT100 in boiler well
    ESP32 (32/33) --- HX711 --- load cell under drip tray
    GPIO34/35 --- brew / steam toggles (to 3V3 via switch, 10k pull-down)
    GPIO21/22 --- lamp / buzzer

The ESP32 side stays extra-low-voltage everywhere: it drives coils and
gates, never a mains conductor. Heater power flows through the
mechanical cutoff and the thermal fuse before the SSR, so two
independent hardware links open even if the SSR welds shut and the
firmware is gone.

## Calibration

Scale, two point: with the tray empty read the raw HX711 value into
`scale_raw_zero`; place a known 1000 g mass and read `scale_raw_1kg`.
Set both in your fika-config substitutions.

Cup table: weigh each cup empty on the calibrated tray, note the grams
into `cupN_tare_g`, pick `cupN_target_g` for the drink. Cups must differ
by more than 2 x cup_tolerance_g (10 g) or recognition refuses to guess
(by design, see concepts/cup-recognition.md).
