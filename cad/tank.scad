/*
 * fika - water tank envelope.
 * Purpose: layout placeholder for the reservoir at the rear, feeding the
 *          pump by gravity. Origin at the bottom center of the footprint.
 *          Stub marks the bottom outlet to the suction line.
 * Material: glass or stainless container (off the shelf)
 * Fabrication: cots
 */

include <design_params.scad>

$fn = 60;

module tank() {
    color("#8899aa") {
        difference() {
            translate([-tank_w / 2, -tank_d / 2, 0])
                cube([tank_w, tank_d, tank_h]);
            translate([-tank_w / 2 + 3, -tank_d / 2 + 3, 3])
                cube([tank_w - 6, tank_d - 6, tank_h]);
        }
        // bottom outlet to the pump suction line
        translate([0, 0, -10]) cylinder(d = 12, h = 13);
    }
}

tank();
