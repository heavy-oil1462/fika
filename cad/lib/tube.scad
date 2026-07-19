/*
 * fika - shared tube helpers.
 * Purpose: render copper line runs as polylines of cylinders with sphere
 *          joints, for the hydraulic path layout model.
 * Material: n/a (pure modules, no top-level geometry)
 * Fabrication: lib
 */

// Solid segment from point a to point b. Coincident points are skipped:
// a run may collapse a leg when two components share a coordinate, and
// that must not produce a NaN rotation.
module tube_seg(a, b, od) {
    v = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    l = norm(v);
    if (l > 0.001)
        translate(a)
            rotate([0, acos(v[2] / l), atan2(v[1], v[0])])
                cylinder(h = l, d = od);
}

// Polyline run through the given points, sphere joints at the bends.
module tube_run(points, od) {
    for (i = [0 : len(points) - 2])
        tube_seg(points[i], points[i + 1], od);
    for (i = [1 : len(points) - 2])
        translate(points[i]) sphere(d = od);
}
