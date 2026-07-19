/*
 * fika - hydraulic path layout.
 * Purpose: the exposed copper runs in machine coordinates: tank down to
 *          the pump, pump pressure line forward of the rails and in to
 *          the boiler inlet, boiler brew outlet up through the deck bore
 *          to the group, and the steam line from the boiler top out to
 *          the wand over the tray. Four separate runs, so the STL has
 *          four shells. With no panels these runs are the visible part
 *          of the machine, so they are routed to be seen.
 * Material: copper tube, brass compression fittings at the ports
 * Fabrication: cots
 */

include <design_params.scad>
use <lib/tube.scad>

$fn = 40;

head_x = pump_x + (motor_l + pump_head_l) / 2 + 12;  // pump port face
tank_cy = tank_y + tank_d / 2;
inlet_x = boiler_x - boiler_od / 4;                  // boiler feed port
group_top_z = tray_z + tray_h + cup_clearance_h + group_h;
// the brew riser leaves the boiler outlet and climbs through its own
// deck bore (cad/frame.scad drills the same y)
riser_y = boiler_y - boiler_od / 2 - 15;
// clear of the pump when crossing the machine, clear of the deck when
// dropping past it
cross_z = pump_z + motor_d / 2 + 25;
wand_out_x = rail_inset + frame_plate_t + 20;
wand_tip_x = tray_w / 2 - 30;

// tank outlet down through its deck bore, across above the pump, then
// down outboard of the motor to the inlet boss
suction_pts = [
    [0, tank_cy, tank_z - 10],
    [0, tank_cy, cross_z],
    [head_x, tank_cy, cross_z],
    [head_x, pump_y + 12, pump_z],
];

// pump outlet up, across behind the rails, then forward between them
// to the boiler feed port
pressure_pts = [
    [head_x, pump_y - 12, pump_z],
    [head_x, pump_y - 12, boiler_z - 5],
    [inlet_x, pump_y - 12, boiler_z - 5],
    [inlet_x, boiler_y, boiler_z - 5],
];

// boiler brew outlet, up through the deck, forward to the group nipple
brew_pts = [
    [boiler_x, riser_y, boiler_z + 20],
    [boiler_x, riser_y, group_top_z + 12],
    [group_x, group_y, group_top_z + 12],
];

// steam from the boiler crown, out past the deck edge and down to the
// wand tip over the tray
steam_pts = [
    [boiler_x, boiler_y, boiler_z + boiler_h + 8],
    [boiler_x, boiler_y, boiler_z + boiler_h + 40],
    [-wand_out_x, boiler_y - 40, boiler_z + boiler_h + 40],
    [-wand_out_x, group_y, group_top_z + 30],
    [-wand_tip_x, group_y - 20, tray_z + tray_h + 55],
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
