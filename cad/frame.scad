/*
 * fika - aluminum plate frame.
 * Purpose: structural skeleton: two sides, base, rear, top and the group
 *          mount plate, all flat plates for the PrintNC. Positioned in
 *          machine coordinates so the assembly places frame() at origin.
 * Material: 6082-T6 aluminum, frame_plate_t structural / mount_plate_t mount
 * Fabrication: cnc (DXF profiles via -D export_profile=side|base|rear|top|mount)
 */

include <design_params.scad>
use <lib/plate.scad>

$fn = 60;
export_profile = "";

inner_w = frame_w - 2 * frame_plate_t;
group_top_z = tray_z + tray_h + cup_clearance_h + group_h;

function corner_holes(w, d, inset = 12) =
    [for (sx = [-1, 1], sy = [-1, 1]) [sx * (w / 2 - inset), sy * (d / 2 - inset)]];

// side plate, drawn with x = machine depth, y = machine height
module frame_side_profile() {
    difference() {
        rounded_rect(frame_d, frame_h);
        hole_pattern(corner_holes(frame_d, frame_h), bolt_hole_d);
        hole_pattern([[-frame_d / 2 + 12, 0], [frame_d / 2 - 12, 0]], bolt_hole_d);
    }
}

module frame_base_profile() {
    difference() {
        rounded_rect(inner_w, frame_d);
        hole_pattern(corner_holes(inner_w, frame_d), bolt_hole_d);
    }
}

module frame_rear_profile() {
    difference() {
        rounded_rect(inner_w, frame_h);
        hole_pattern(corner_holes(inner_w, frame_h), bolt_hole_d);
    }
}

module frame_top_profile() {
    difference() {
        rounded_rect(inner_w, frame_d - frame_plate_t);
        hole_pattern(corner_holes(inner_w, frame_d - frame_plate_t), bolt_hole_d);
    }
}

module group_mount_profile() {
    difference() {
        rounded_rect(inner_w, mount_plate_d);
        translate([group_x, 0]) circle(d = group_od);
        hole_pattern(corner_holes(inner_w, mount_plate_d), bolt_hole_d);
    }
}

module frame() {
    color("silver") {
        for (s = [-1, 1])
            translate([s == -1 ? -frame_w / 2 : frame_w / 2 - frame_plate_t,
                       frame_d / 2, frame_h / 2 - frame_plate_t])
                rotate([90, 0, 90]) plate(frame_plate_t) frame_side_profile();
        translate([0, frame_d / 2, -frame_plate_t])
            plate(frame_plate_t) frame_base_profile();
        translate([0, frame_d, frame_h / 2 - frame_plate_t])
            rotate([90, 0, 0]) plate(frame_plate_t) frame_rear_profile();
        translate([0, (frame_d - frame_plate_t) / 2, frame_h - 2 * frame_plate_t])
            plate(frame_plate_t) frame_top_profile();
        translate([0, mount_plate_y + mount_plate_d / 2, group_top_z])
            plate(mount_plate_t) group_mount_profile();
    }
}

if (export_profile == "side") frame_side_profile();
else if (export_profile == "base") frame_base_profile();
else if (export_profile == "rear") frame_rear_profile();
else if (export_profile == "top") frame_top_profile();
else if (export_profile == "mount") group_mount_profile();
else frame();
