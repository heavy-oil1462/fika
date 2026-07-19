/*
 * fika - drip tray and load cell.
 * Purpose: layout placeholder for the drip tray that doubles as the cup
 *          scale platform. Tray origin at the center of its footprint,
 *          bottom at z 0. loadcell_bar() is the TAL220-class bar the tray
 *          sits on, placed by the assembly between base plate and tray.
 * Material: printed tray for the foundation, load cell off the shelf
 * Fabrication: print
 */

include <design_params.scad>

$fn = 60;

module drip_tray() {
    color("#333333") difference() {
        translate([-tray_w / 2, -tray_d / 2, 0])
            cube([tray_w, tray_d, tray_h]);
        translate([-tray_w / 2 + 3, -tray_d / 2 + 3, 4])
            cube([tray_w - 6, tray_d - 6, tray_h]);
    }
}

// cots: bar load cell under the tray center
module loadcell_bar() {
    color("#999999") translate([-loadcell_l / 2, -loadcell_w / 2, 0])
        cube([loadcell_l, loadcell_w, loadcell_h]);
}

drip_tray();
