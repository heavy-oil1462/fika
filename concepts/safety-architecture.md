# Safety architecture

**Purpose:** define the layered protection around 230 V mains, a
pressurized boiler and a 125 C surface, such that no single failure,
including a complete firmware failure, leaves the machine dangerous.

## Three layers, weakest last

1. Mechanical, always live. The heater circuit passes through a
   manual-reset thermal cutoff mounted on the boiler shell and a
   one-shot thermal fuse in series, before the SSR. The boiler carries a
   mechanical relief valve (relief_bar, 12 bar) that vents over the
   drip tray. The pump has an OPV (opv_bar, 9 bar) bypassing back to the
   tank. None of these know the ESP32 exists.
2. Electrical topology. The ESP32 side is extra-low-voltage everywhere;
   it drives the SSR input, a contactor coil and a solenoid driver.
   Actuator GPIOs avoid boot-glitching strapping pins and every actuator
   defaults off at boot (docs/HARDWARE.md).
3. Firmware interlocks (packages/safety.yaml). Over-temperature above
   max_temp_c or a dead boiler sensor latches a fault: heater off, pump
   off, valve closed, until the machine is power cycled. Steam mode and
   brewing exclude each other. This layer improves behavior; it is
   explicitly not the protection.

## Rules

- Pressure and thermal parts are cots brass/copper, never printed
  (MATERIALS.md marks them).
- The relief valve and OPV setpoints live in cad/design_params.scad;
  max_temp_c spans CAD and firmware and is swept by tools/validate.py.
- Any new actuator package must default off at boot and state its
  interlocks in the banner.
