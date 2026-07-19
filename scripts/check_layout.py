#!/usr/bin/env python3
"""Layout clearance check over the component envelopes.

Mirrors the placement math in cad/main_assembly.scad as axis-aligned
bounding boxes computed from cad/design_params.scad, then asserts:

  1. every component pair keeps at least `clearance` air between
     envelopes (pairs that touch by design are skipped and listed),
  2. the tray-to-group gap equals the cup zone (cup_clearance_h),
  3. components stay inside the frame interior with `clearance_wall`
     margin on the sides, rear and top. The front is open by design
     (portafilter handle and steam wand poke out), so the front face
     is not checked.

Honest at layout level: envelopes ignore port stubs and the copper
runs. Mesh-level interference checking is deferred (TODO.md).

Exit 1 on any violation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design_params import PARAMS  # noqa: E402


def boxes(p):
    """AABBs per component. Must match main_assembly.scad translations."""
    pump_len = p["motor_l"] + p["pump_head_l"]
    spout_z = p["tray_z"] + p["tray_h"] + p["cup_clearance_h"]
    group_r = (p["group_od"] + 20) / 2  # portafilter body is the widest
    return {
        "boiler": (
            (p["boiler_x"] - p["boiler_od"] / 2, p["boiler_x"] + p["boiler_od"] / 2),
            (p["boiler_y"] - p["boiler_od"] / 2, p["boiler_y"] + p["boiler_od"] / 2),
            (p["boiler_z"], p["boiler_z"] + p["boiler_h"]),
        ),
        "pump": (
            (p["pump_x"] - pump_len / 2, p["pump_x"] + pump_len / 2),
            (p["pump_y"] - p["motor_d"] / 2, p["pump_y"] + p["motor_d"] / 2),
            (p["pump_z"] - p["motor_d"] / 2, p["pump_z"] + p["motor_d"] / 2),
        ),
        "group": (
            (p["group_x"] - group_r, p["group_x"] + group_r),
            (p["group_y"] - group_r, p["group_y"] + group_r),
            (spout_z, spout_z + p["group_h"]),
        ),
        "tray": (
            (-p["tray_w"] / 2, p["tray_w"] / 2),
            (p["tray_y"], p["tray_y"] + p["tray_d"]),
            (p["tray_z"], p["tray_z"] + p["tray_h"]),
        ),
        "tank": (
            (-p["tank_w"] / 2, p["tank_w"] / 2),
            (p["tank_y"], p["tank_y"] + p["tank_d"]),
            (p["tank_z"], p["tank_z"] + p["tank_h"]),
        ),
    }


# pairs that touch or nest by design; everything else must clear
SKIP_PAIRS = {
    frozenset(("tray", "group")),  # checked separately as the cup zone
}


def gap(a, b):
    """Largest axis separation between two AABBs (negative = overlap)."""
    return max(
        max(a[i][0] - b[i][1], b[i][0] - a[i][1]) for i in range(3)
    )


def main():
    p = PARAMS
    bx = boxes(p)
    failures = 0

    names = sorted(bx)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if frozenset((a, b)) in SKIP_PAIRS:
                continue
            g = gap(bx[a], bx[b])
            if g < p["clearance"]:
                print(f"[FAIL] {a} to {b}: gap {g:.1f} mm < clearance "
                      f"{p['clearance']} mm")
                failures += 1
            else:
                print(f"ok: {a} to {b}: {g:.1f} mm")

    # cup zone: air between tray top and the group spout
    cup_gap = bx["group"][2][0] - bx["tray"][2][1]
    if abs(cup_gap - p["cup_clearance_h"]) > 0.001:
        print(f"[FAIL] cup zone is {cup_gap:.1f} mm, expected "
              f"cup_clearance_h {p['cup_clearance_h']} mm")
        failures += 1
    else:
        print(f"ok: cup zone {cup_gap:.1f} mm")

    # containment: sides, rear, top, base; the front face is open
    ix = (-(p["frame_w"] / 2 - p["frame_plate_t"]),
          p["frame_w"] / 2 - p["frame_plate_t"])
    iy_max = p["frame_d"] - p["frame_plate_t"]
    iz = (0, p["frame_h"] - 2 * p["frame_plate_t"])
    m = p["clearance_wall"]
    for name, (x, y, z) in bx.items():
        problems = []
        if x[0] < ix[0] + m or x[1] > ix[1] - m:
            problems.append("sides")
        if y[1] > iy_max - m:
            problems.append("rear")
        if z[1] > iz[1] - m:
            problems.append("top")
        if z[0] < iz[0]:
            problems.append("base")
        if problems:
            print(f"[FAIL] {name} too close to frame: {', '.join(problems)}")
            failures += 1
        else:
            print(f"ok: {name} inside the frame envelope")

    if failures:
        print(f"\n{failures} layout violation(s)")
        return 1
    print("\nlayout ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
