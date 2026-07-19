# fika technical specification

Numbered so discussions can cite sections. Dimensions and setpoints live
in cad/design_params.scad; this file states the design intent around
them.

## 1. Thermal

- Single dual-use boiler: copper shell, nominal 1.0 l fill, brass
  ports, lead free brazing. Vertical cylinder, element through the
  bottom cap.
- 1400 W / 230 V element behind an SSR, PID controlled (ESPHome
  climate). Setpoints: brew 93 C, steam 125 C, firmware cutoff 135 C.
- Heat-up budget from cold: under 6 min (generated proof:
  outputs/budgets/energy_budget.md; gate: verify step 7).

## 2. Hydraulic

- Rotary vane pump on a mains induction motor, low in the chassis for
  noise and center of gravity. OPV at 9 bar bypassing to the tank.
- Path: tank (gravity, standing on the deck above the pump) -> pump ->
  OPV tee -> boiler bottom -> front outlet -> three-way brew valve ->
  group; steam from the boiler top to the wand over the tray. Exposed
  copper lines, brass compression fittings.
- Boiler mechanical relief valve at 12 bar, venting over the tray.
- Group: standard 58 mm E61-compatible portafilter group (cots), bolted
  under the group mount plate.

## 3. Electrical

- 230 V / 50 Hz, 10 A circuit. Heater current 6.1 A leaves margin
  within the 80 percent continuous rule (generated budget).
- Heater path: mechanical thermal cutoff -> thermal fuse -> SSR.
  Pump motor via contactor. ESP32 and sensors are extra-low-voltage
  only. Pin map and wiring: docs/HARDWARE.md.

## 4. Controls

- ESP32 (esp32dev) running ESPHome; Home Assistant over MQTT discovery.
  All control loops local; the machine works with no network
  (docs/PROTOCOL.md).
- Physical controls: two solid toggles (brew, steam), a ready lamp, a
  buzzer. No screens.
- Behavior-driven: drip tray load cell recognizes calibrated cups by
  weight and arms that cup's brew program; shots stop gravimetrically
  at target beverage weight (concepts/cup-recognition.md).

## 5. Safety

- Three layers, firmware last and weakest:
  concepts/safety-architecture.md. Pressure and thermal parts are
  purchased, never printed.
- Every actuator defaults off at boot; actuator commands are never
  retained on the broker.

## 6. Frame and fabrication

- Open frame, no enclosure: an oak base slab, two aluminum rails, one
  aluminum deck. A member exists only if it carries a component
  (concepts/open-frame.md), so the copper runs are the visible surface
  of the machine.
- The deck seats the boiler and the group in bored seats, carries the
  tank, and passes the tank outlet and brew riser through two bores.
- Oak where hands and the counter meet the machine: the base slab and
  the portafilter handle (which must not conduct boiler heat).
- All flat parts are CNC-milled on the PrintNC, oak included; one bolt
  size (M5) throughout. DXF profiles are pipeline outputs
  (outputs/dxf/).
- Every cad part header carries a fabrication tag: cnc, print, cots,
  lib or assembly (gate: validate `fabtags`).
