/*
 * fika - shared plate helpers.
 * Purpose: rounded plates and hole patterns for the CNC aluminum parts.
 * Material: n/a (pure modules, no top-level geometry)
 * Fabrication: lib
 */

// 2D rectangle with rounded corners, centered.
module rounded_rect(w, d, r = 6) {
    offset(r = r) offset(r = -r) square([w, d], center = true);
}

// 2D circles at the given [x, y] points, for difference() in profiles.
module hole_pattern(points, d) {
    for (p = points)
        translate(p) circle(d = d);
}

// 3D plate extruded from a 2D profile passed as a child.
module plate(t) {
    linear_extrude(height = t) children();
}
