#!/usr/bin/env python3
"""Layout checks over the component and frame envelopes.

Mirrors the placement math in cad/main_assembly.scad and cad/frame.scad
as axis-aligned bounding boxes computed from cad/design_params.scad,
then asserts:

  1. every component pair keeps at least `clearance` air between
     envelopes (pairs that meet by design are skipped and listed),
  2. the tray-to-group gap equals the cup zone (cup_clearance_h),
  3. the rails clear every component by `clearance` - they carry the
     deck and must touch nothing else on the way up,
  4. the deck seats what it is supposed to: the boiler and group bores
     fall inside the plate with material left around them, and the tank
     stands on the deck top and inside its outline,
  5. every component stands over the base slab, so nothing overhangs
     the oak.

There is no enclosure to contain anything: the frame is open on every
side by design, which is why the old containment check is gone rather
than relaxed.

Honest at layout level: envelopes ignore port stubs and the copper
runs. Mesh-level interference checking is deferred (TODO.md).

Exit 1 on any violation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design_params import PARAMS  # noqa: E402


def deck_top(p):
    """Deck top surface. Mirrors deck_top in cad/frame.scad."""
    return p["tray_z"] + p["tray_h"] + p["cup_clearance_h"] + p["group_h"]


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


def rails(p):
    """The two rail AABBs. Must match frame() in cad/frame.scad."""
    top = deck_top(p) - p["frame_plate_t"]
    return {
        f"rail {side}": (
            (sx * p["rail_inset"] - (p["frame_plate_t"] if sx < 0 else 0),
             sx * p["rail_inset"] + (p["frame_plate_t"] if sx > 0 else 0)),
            (p["rail_front"], p["rail_back"]),
            (0, top),
        )
        for side, sx in (("left", -1), ("right", 1))
    }


# pairs that meet or nest by design; everything else must clear
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
    rl = rails(p)
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

    # the rails carry the deck and must touch nothing else
    rail_hits = 0
    for rail_name, rail_box in rl.items():
        for name, box in bx.items():
            g = gap(rail_box, box)
            if g < p["clearance"]:
                print(f"[FAIL] {rail_name} to {name}: gap {g:.1f} mm < "
                      f"clearance {p['clearance']} mm")
                rail_hits += 1
    failures += rail_hits
    if not rail_hits:
        print(f"ok: rails clear every component by {p['clearance']} mm")

    # the deck seats the boiler and the group, and carries the tank
    deck_halfw = p["rail_inset"] + p["frame_plate_t"]
    deck_x = (-deck_halfw, deck_halfw)
    deck_y = (p["deck_front"], p["deck_back"])
    for name, bore_d in (("boiler", p["boiler_od"]), ("group", p["group_od"])):
        cx = p[f"{name}_x"]
        cy = p[f"{name}_y"]
        margin = min(deck_x[1] - (cx + bore_d / 2), (cx - bore_d / 2) - deck_x[0],
                     deck_y[1] - (cy + bore_d / 2), (cy - bore_d / 2) - deck_y[0])
        if margin < p["clearance"]:
            print(f"[FAIL] deck seat for the {name}: only {margin:.1f} mm of "
                  f"plate around the bore (need {p['clearance']} mm)")
            failures += 1
        else:
            print(f"ok: deck seats the {name}, {margin:.1f} mm of plate around it")

    if abs(p["tank_z"] - deck_top(p)) > 0.001:
        print(f"[FAIL] tank_z {p['tank_z']} does not stand on the deck top "
              f"{deck_top(p):.1f} - the tank must sit on the deck so the "
              "suction line stays flooded")
        failures += 1
    else:
        print(f"ok: tank stands on the deck at z {p['tank_z']}")

    tank_x = bx["tank"][0]
    tank_y = bx["tank"][1]
    if (tank_x[0] < deck_x[0] or tank_x[1] > deck_x[1]
            or tank_y[0] < deck_y[0] or tank_y[1] > deck_y[1]):
        print("[FAIL] tank overhangs the deck it stands on")
        failures += 1
    else:
        print("ok: tank footprint sits within the deck")

    # nothing overhangs the oak slab
    base_x = (-p["frame_w"] / 2, p["frame_w"] / 2)
    base_y = (0, p["frame_d"])
    for name, (x, y, _z) in bx.items():
        if x[0] < base_x[0] or x[1] > base_x[1] or y[0] < base_y[0] or y[1] > base_y[1]:
            print(f"[FAIL] {name} overhangs the base slab")
            failures += 1
        else:
            print(f"ok: {name} stands over the base slab")

    if failures:
        print(f"\n{failures} layout violation(s)")
        return 1
    print("\nlayout ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
