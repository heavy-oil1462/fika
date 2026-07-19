/*
 * fika - open frame: oak base slab, two aluminum rails, one deck plate.
 * Purpose: hold the components and nothing else. The oak slab is the mass
 *          that stands on the counter and damps the pump; the rails carry
 *          the deck; the deck holds the boiler and the group through bored
 *          seats. There are no panels, so the machine is open on every
 *          side and every run of copper stays visible.
 * Material: European oak slab (base), 6082-T6 aluminum (rails, deck)
 * Fabrication: cnc (DXF profiles via -D export_profile=base|rail|deck)
 */

include <design_params.scad>
use <lib/plate.scad>

$fn = 60;
export_profile = "";

// heights follow the components: the deck sits under the group body top,
// and the rails run from the slab up to the deck.
deck_top = tray_z + tray_h + cup_clearance_h + group_h;
deck_z0 = deck_top - frame_plate_t;
rail_h = deck_z0;

deck_halfw = rail_inset + frame_plate_t;
deck_cy = (deck_front + deck_back) / 2;
rail_cy = (rail_front + rail_back) / 2;
rail_x = rail_inset + frame_plate_t / 2;   // rail mid-plane

// where the rails land, in base-slab and deck coordinates
function rail_bolts(cy) =
    [for (sx = [-1, 1], sy = [-1, 1])
        [sx * rail_x, cy + sy * (rail_back - rail_front) / 2 * 0.6]];

module frame_base_profile() {
    difference() {
        rounded_rect(frame_w, frame_d, 12);
        hole_pattern(rail_bolts(rail_cy - frame_d / 2), bolt_hole_d);
    }
}

module frame_rail_profile() {
    difference() {
        rounded_rect(rail_back - rail_front, rail_h, 8);
        // into the slab below and the deck above
        for (sy = [-1, 1])
            hole_pattern([[sy * (rail_back - rail_front) / 2 * 0.6,
                           -rail_h / 2 + 12],
                          [sy * (rail_back - rail_front) / 2 * 0.6,
                           rail_h / 2 - 12]], bolt_hole_d);
    }
}

// Four bores, four jobs: seat the group, seat the boiler, and pass the
// tank outlet and the brew riser through the plate.
module frame_deck_profile() {
    difference() {
        rounded_rect(2 * deck_halfw, deck_back - deck_front, 10);
        translate([group_x, group_y - deck_cy]) circle(d = group_od);
        translate([boiler_x, boiler_y - deck_cy]) circle(d = boiler_od);
        translate([0, tank_y + tank_d / 2 - deck_cy]) circle(d = 20);
        translate([boiler_x, boiler_y - boiler_od / 2 - 15 - deck_cy])
            circle(d = brew_line_od + 10);
        hole_pattern(rail_bolts(rail_cy - deck_cy), bolt_hole_d);
    }
}

module frame() {
    // oak slab, top face at z 0
    color("#c8a165") translate([0, frame_d / 2, -base_t])
        plate(base_t) frame_base_profile();
    color("silver") {
        for (s = [-1, 1])
            translate([s * rail_x - frame_plate_t / 2, rail_cy, rail_h / 2])
                rotate([90, 0, 90]) plate(frame_plate_t) frame_rail_profile();
        translate([0, deck_cy, deck_z0])
            plate(frame_plate_t) frame_deck_profile();
    }
}

if (export_profile == "base") frame_base_profile();
else if (export_profile == "rail") frame_rail_profile();
else if (export_profile == "deck") frame_deck_profile();
else frame();
