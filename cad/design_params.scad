/*
 * fika - shared design parameters, the single source of truth.
 *
 * Read by every cad/*.scad (include <design_params.scad>) and re-parsed by
 * scripts/design_params.py for scripts/check_layout.py and
 * tools/energy_budget.py, so a value changed here flips the whole pipeline
 * at once. scripts/check_params.py fails the build if any other .scad
 * shadows a name defined here.
 *
 * Keep every line a plain literal: name = value; (numbers, booleans, flat
 * vectors). No arithmetic - derived values are computed by the consumers.
 *
 * Units: mm, deg C, W, V, A, bar, g unless noted.
 * Coordinates: origin at the center of the base plate top surface.
 * X right, Y toward the back, Z up. Positions are component reference
 * points noted per name.
 */

// open frame: an oak base slab carrying two aluminum rails and one deck
// plate that holds the boiler and the group through bored seats. There is
// no enclosure - every member carries a component, and everything else is
// left exposed. Heights are derived from the components they hold.
frame_w = 330;          // base slab width (clears the pump and its ports)
frame_d = 320;          // base slab depth
base_t = 24;            // oak slab thickness (mass and damping; z -base_t..0)
frame_plate_t = 10;     // aluminum rails and deck
rail_inset = 66;        // rail inner face from center (flanks the boiler)
rail_front = 135;       // rail front edge (clears the drip tray)
rail_back = 195;        // rail back edge (clears the pump)
deck_front = 20;        // deck front edge (leaves plate around the group bore)
deck_back = 305;        // deck back edge (carries the tank behind the boiler)

// boiler (single, dual use, copper shell; position = bottom center)
boiler_od = 102;
boiler_h = 160;
boiler_wall = 2;
boiler_x = 0;
boiler_y = 180;
boiler_z = 150;
boiler_volume_l = 1.0;  // nominal fill, used by the energy budget

// heater and mains
heater_power_w = 1400;
mains_voltage = 230;
mains_breaker_a = 10;
brew_temp_c = 93;
steam_temp_c = 125;
max_temp_c = 135;       // firmware hard cutoff; mechanical cutoff above this

// pump: rotary vane head + mains motor, axis along X at the rear base
// (position = axis center; assembly centered on pump_x)
pump_head_d = 42;
pump_head_l = 105;
motor_d = 100;
motor_l = 160;
pump_x = 0;
pump_y = 255;
pump_z = 55;
opv_bar = 9;            // pump bypass back to reservoir
relief_bar = 12;        // boiler mechanical safety relief valve

// brew group and cup zone (position = group axis at tray center)
group_od = 70;
group_h = 90;
group_x = 0;
group_y = 65;
cup_clearance_h = 95;   // spout height above the tray top
cup_max_d = 90;

// drip tray with load cell scale (tray_z = top of load cell + gap)
tray_w = 200;
tray_d = 110;
tray_h = 30;
tray_y = 15;            // tray front edge
tray_z = 13;
loadcell_l = 55;        // TAL220-class bar load cell
loadcell_w = 12.7;
loadcell_h = 12.7;
scale_capacity_g = 1000;

// water tank: stands on the deck behind the boiler, so the outlet sits
// well above the pump inlet and the suction line stays flooded.
// tank_z must equal the deck top (scripts/check_layout.py asserts it).
tank_w = 140;           // stays within the deck it stands on
tank_d = 60;
tank_h = 150;
tank_y = 241;
tank_z = 228;

// plumbing, copper lines (suction from the tank is larger bore)
brew_line_od = 6;
brew_line_wall = 1;
steam_line_od = 6;
suction_line_od = 8;

// fasteners (one bolt size for every frame joint, M5 with clearance)
bolt_hole_d = 5.3;

// layout rules (scripts/check_layout.py)
clearance = 10;         // minimum gap between component envelopes, and
                        // between the rails and anything they do not carry
