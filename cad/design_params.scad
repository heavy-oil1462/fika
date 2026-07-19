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

// frame envelope (outer dimensions, CNC aluminum plates)
frame_w = 310;
frame_d = 320;
frame_h = 400;          // side plate height; sides run z -8..392
frame_plate_t = 8;      // structural plates: sides, base, rear, top
mount_plate_t = 6;      // group mount plate
mount_plate_d = 90;     // group mount plate depth (y extent)
mount_plate_y = 20;     // group mount plate front edge

// boiler (single, dual use, copper shell; position = bottom center)
boiler_od = 102;
boiler_h = 160;
boiler_wall = 2;
boiler_x = -50;
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
tray_d = 130;
tray_h = 30;
tray_y = 15;            // tray front edge
tray_z = 13;
loadcell_l = 55;        // TAL220-class bar load cell
loadcell_w = 12.7;
loadcell_h = 12.7;
scale_capacity_g = 1000;

// water tank (position = front face / bottom)
tank_w = 200;
tank_d = 55;
tank_h = 200;
tank_y = 245;
tank_z = 150;

// plumbing, copper lines (suction from the tank is larger bore)
brew_line_od = 6;
brew_line_wall = 1;
steam_line_od = 6;
suction_line_od = 8;

// fasteners (one bolt size for every frame joint, M5 with clearance)
bolt_hole_d = 5.3;

// layout rules (scripts/check_layout.py)
clearance = 10;         // minimum gap between component envelopes
clearance_wall = 5;     // minimum gap between components and frame plates
