/*
 * fika - master assembly.
 * Purpose: place every component in machine coordinates for review
 *          renders. Display toggles below are assembly-local; all
 *          dimensions and positions come from design_params.scad.
 * Material: n/a
 * Fabrication: assembly
 */

include <design_params.scad>
use <frame.scad>
use <boiler.scad>
use <pump.scad>
use <group.scad>
use <drip_tray.scad>
use <tank.scad>
use <hydraulic_path.scad>

$fn = 60;

// display toggles, not design parameters
show_frame = true;
show_boiler = true;
show_pump = true;
show_group = true;
show_tray = true;
show_tank = true;
show_plumbing = true;
show_cup = true;

spout_z = tray_z + tray_h + cup_clearance_h;

if (show_frame) frame();
if (show_boiler) translate([boiler_x, boiler_y, boiler_z]) boiler();
if (show_pump)
    translate([pump_x - (motor_l + pump_head_l) / 2, pump_y, pump_z]) pump();
if (show_group) translate([group_x, group_y, spout_z]) group();
if (show_tray) {
    translate([0, tray_y + tray_d / 2, tray_z]) drip_tray();
    translate([0, tray_y + tray_d / 2, 0]) loadcell_bar();
}
if (show_tank) translate([0, tank_y + tank_d / 2, tank_z]) tank();
if (show_plumbing) hydraulic_path();
// ghost cup on the tray, sized to the largest calibrated cup
if (show_cup)
    %translate([group_x, group_y, tray_z + tray_h])
        cylinder(d = cup_max_d * 0.85, h = 80);
