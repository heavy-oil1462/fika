/*
 * fika - hydraulic path layout.
 * Purpose: the exposed copper runs in machine coordinates: tank suction to
 *          the pump, pump pressure line through the OPV side to the boiler
 *          inlet, boiler brew outlet up and over to the group nipple, and
 *          the steam line from the boiler top out to the wand. Four
 *          separate runs, so the STL has four shells.
 * Material: copper tube, brass compression fittings at the ports
 * Fabrication: cots
 */

include <design_params.scad>
use <lib/tube.scad>

$fn = 40;

head_x = pump_x + (motor_l + pump_head_l) / 2 + 12;
tank_cy = tank_y + tank_d / 2;
inlet_x = boiler_x - boiler_od / 4;
group_top_z = tray_z + tray_h + cup_clearance_h + group_h;

suction_pts = [
    [0, tank_cy, tank_z - 10],
    [0, tank_cy, 90],
    [head_x, tank_cy, pump_z + 40],
    [head_x, pump_y + 12, pump_z],
];

pressure_pts = [
    [head_x, pump_y - 12, pump_z],
    [head_x, pump_y - 12, 35],
    [inlet_x, pump_y - 12, 35],
    [inlet_x, boiler_y, 35],
    [inlet_x, boiler_y, boiler_z - 5],
];

brew_pts = [
    [boiler_x, boiler_y - boiler_od / 2 - 12, boiler_z + 20],
    [boiler_x, group_y, boiler_z + 20],
    [boiler_x, group_y, 250],
    [group_x, group_y, 250],
    [group_x, group_y, group_top_z + 8],
];

steam_pts = [
    [boiler_x, boiler_y, boiler_z + boiler_h + 8],
    [boiler_x, boiler_y, 345],
    [95, 120, 345],
    [110, 20, 300],
    [110, -25, 170],
];

module hydraulic_path() {
    color("#b87333") {
        tube_run(suction_pts, suction_line_od);
        tube_run(pressure_pts, brew_line_od);
        tube_run(brew_pts, brew_line_od);
        tube_run(steam_pts, steam_line_od);
    }
}

hydraulic_path();
