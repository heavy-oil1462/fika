/*
 * fika - rotary pump and motor envelope.
 * Purpose: layout placeholder for the rotary vane pump head on its mains
 *          motor. Axis along +X, origin at the motor rear end face on the
 *          axis. Stubs mark the OPV tee and the head inlet/outlet.
 * Material: brass head, steel motor (both off the shelf)
 * Fabrication: cots
 */

include <design_params.scad>

$fn = 60;

module pump() {
    rotate([0, 90, 0]) {
        color("#555555") cylinder(d = motor_d, h = motor_l);
        color("#b5a642") translate([0, 0, motor_l])
            cylinder(d = pump_head_d, h = pump_head_l);
        // inlet and outlet bosses on the head end face
        color("#b5a642") translate([0, 12, motor_l + pump_head_l])
            cylinder(d = 8, h = 12);
        color("#b5a642") translate([0, -12, motor_l + pump_head_l])
            cylinder(d = 8, h = 12);
    }
    // OPV tee on the head, bypass back to the tank
    color("#b5a642") translate([motor_l + pump_head_l * 0.6, 0, 0])
        rotate([-90, 0, 0]) cylinder(d = 15, h = 24);
}

pump();
