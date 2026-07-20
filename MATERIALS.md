# Material and component list (BOM)

Grouped by subsystem. CAD back-references point at the owning model.
The electronics detail table with costs lives in docs/HARDWARE.md.
Pressure and thermal parts are cots only: never printed, never
improvised. Status caveat: this is a concept-phase list; no part on it
has been bought or fitted (see Status in README.md).

## Frame and mechanics

The frame is open: three members, each carrying a component
(concepts/open-frame.md). DXF profiles for all of them are pipeline
outputs in outputs/dxf/.

- European oak slab, 24 mm, 330 x 320: the base everything bolts to
  (cad/frame.scad, profile `base`). Cut on the PrintNC like the metal.
  Oiled, not lacquered, so it can be re-oiled after spills.
- 6082-T6 aluminum plate, 10 mm: two rails (profile `rail`) and one
  deck (profile `deck`). The deck is bored to seat the boiler and the
  group and to pass the tank outlet and brew riser.
- M5 stainless bolts throughout, one bolt size for every frame joint
  (bolt_hole_d in cad/design_params.scad). Threaded inserts in the oak.
- Printed drip tray, PETG (cad/drip_tray.scad); replace with folded
  stainless later (TODO phase 2).

## Boiler and thermal (cots only)

- Copper boiler, ~102 mm OD x 160 mm, 1.0 l, brass ports
  (cad/boiler.scad envelope). Commissioned or salvaged; lead free
  brazing.
- Heating element 1400 W / 230 V, bottom entry.
- Mechanical relief valve, 12 bar.
- Thermal cutoff (manual reset) and one-shot thermal fuse, boiler
  shell mount.
- PT100 probe + MAX31865 (docs/HARDWARE.md).
- Insulation wrap for the shell (keeps the exposed-copper look on the
  pipes, not the vessel).

## Hydraulics (cots only)

- Rotary vane pump head, Procon/Fluid-o-Tech class (cad/pump.scad
  envelope), with 9 bar OPV.
- Mains induction motor, ~100 mm frame (cad/pump.scad envelope).
- Three-way brew solenoid valve, 230 V.
- 58 mm portafilter group (cad/group.scad envelope), with a turned oak
  handle: the one part of the group you hold, and the one that must not
  conduct boiler heat into your hand.
- Copper tube 6 mm OD (pressure and steam), 8 mm OD (suction), lead
  free brass compression fittings (cad/hydraulic_path.scad).
- Water tank ~1.3 l, glass or stainless, standing on the deck so the
  suction line stays flooded (cad/tank.scad envelope).

## Electronics

- See the table in docs/HARDWARE.md (ESP32, SSR, contactor, MAX31865,
  HX711 + TAL220 load cell, toggles, lamp, buzzer, 5 V PSU).
