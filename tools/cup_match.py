#!/usr/bin/env python3
"""Cup recognition and gravimetric stop - the pure-python contract mirror.

The drip tray load cell weighs whatever is placed on it. The firmware
matches a stable weight against the calibrated cup table and selects that
cup's brew profile, then stops the shot when the beverage weight reaches
the profile target. This module is the single statement of that logic:
the lambda in esphome/packages/cup_scale.yaml mirrors it line for line,
tools/validate.py asserts the shared tolerance stays identical, and
tools/test_cup_match.py pins the behavior.

Keep it tiny. If the rule grows beyond what a lambda can mirror honestly,
stop and rethink before extending either side.
"""

from __future__ import annotations

# Shared with the cup_tolerance_g substitution in packages/cup_scale.yaml
# (cross-checked by tools/validate.py). A stable weight must sit within
# this band of exactly one calibrated tare to select a cup.
TOLERANCE_G = 5.0


def match_cup(weight_g: float, cups: list[dict],
              tolerance_g: float = TOLERANCE_G) -> dict | None:
    """Return the single cup whose tare matches weight_g, else None.

    cups: [{"name": str, "tare_g": float, "target_g": float}, ...]
    Ambiguity (two cups within tolerance) returns None: never guess a
    brew program.
    """
    hits = [c for c in cups if abs(weight_g - c["tare_g"]) <= tolerance_g]
    return hits[0] if len(hits) == 1 else None


def beverage_weight(current_g: float, tare_g: float) -> float:
    """Beverage mass in the cup right now."""
    return current_g - tare_g


def brew_done(current_g: float, tare_g: float, target_g: float) -> bool:
    """Gravimetric stop: true once the beverage reaches the target."""
    return beverage_weight(current_g, tare_g) >= target_g
