/*
 * fika - brew group envelope.
 * Purpose: layout placeholder for the brew group with portafilter.
 *          Origin at the spout tip center, +Z up into the machine; the
 *          body top carries the inlet nipple that pokes through the group
 *          mount plate hole.
 * Material: brass group and portafilter (pressure path, never printed)
 * Fabrication: cots
 */

include <design_params.scad>

$fn = 60;

module group() {
    // spout
    color("#b5a642") cylinder(d1 = 8, d2 = 30, h = 20);
    // portafilter body and handle
    color("#b5a642") translate([0, 0, 20]) cylinder(d = group_od + 20, h = 15);
    color("#222222") translate([0, -group_od / 2 - 10, 27])
        rotate([90, 0, 0]) cylinder(d = 25, h = 80);
    // group body
    color("#b5a642") translate([0, 0, 20]) cylinder(d = group_od, h = group_h - 20);
    // inlet nipple, through the mount plate hole
    color("#b5a642") translate([0, 0, group_h]) cylinder(d = 10, h = 12);
}

group();
