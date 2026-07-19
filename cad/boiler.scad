/*
 * fika - boiler envelope.
 * Purpose: layout placeholder for the single dual-use copper boiler.
 *          Origin at the bottom cap center. Stubs mark the ports: element
 *          boss and feed inlet below, brew outlet on the front face low,
 *          steam outlet and safety relief valve on top.
 * Material: copper shell, brass ports (pressure vessel, never printed)
 * Fabrication: cots
 */

include <design_params.scad>

$fn = 60;

module boiler() {
    color("#b87333") {
        cylinder(d = boiler_od, h = boiler_h);
        // heating element boss, enters through the bottom cap
        translate([boiler_od / 4, 0, -12]) cylinder(d = 25, h = 14);
        // feed water inlet from the pump
        translate([-boiler_od / 4, 0, -12]) cylinder(d = 10, h = 14);
        // brew outlet to the group, front face, low
        translate([0, -boiler_od / 2 + 2, 20])
            rotate([90, 0, 0]) cylinder(d = 10, h = 15);
        // steam outlet, top center
        translate([0, 0, boiler_h]) cylinder(d = 10, h = 12);
        // safety relief valve port, top
        translate([25, 0, boiler_h]) cylinder(d = 14, h = 10);
    }
}

boiler();
