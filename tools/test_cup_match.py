#!/usr/bin/env python3
"""Pin the cup recognition and gravimetric stop contract."""

import unittest

from cup_match import TOLERANCE_G, brew_done, match_cup

CUPS = [
    {"name": "espresso", "tare_g": 92.0, "target_g": 36.0},
    {"name": "cappuccino", "tare_g": 210.0, "target_g": 150.0},
]


class TestMatchCup(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(match_cup(92.0, CUPS)["name"], "espresso")

    def test_within_tolerance(self):
        self.assertEqual(match_cup(92.0 + TOLERANCE_G, CUPS)["name"], "espresso")
        self.assertEqual(match_cup(210.0 - TOLERANCE_G, CUPS)["name"], "cappuccino")

    def test_outside_tolerance(self):
        self.assertIsNone(match_cup(92.0 + TOLERANCE_G + 0.1, CUPS))
        self.assertIsNone(match_cup(500.0, CUPS))

    def test_ambiguity_selects_nothing(self):
        close = [
            {"name": "a", "tare_g": 100.0, "target_g": 40.0},
            {"name": "b", "tare_g": 104.0, "target_g": 60.0},
        ]
        self.assertIsNone(match_cup(102.0, close))

    def test_empty_table(self):
        self.assertIsNone(match_cup(92.0, []))


class TestBrewDone(unittest.TestCase):
    def test_below_target(self):
        self.assertFalse(brew_done(92.0 + 35.9, 92.0, 36.0))

    def test_at_target(self):
        self.assertTrue(brew_done(92.0 + 36.0, 92.0, 36.0))

    def test_above_target(self):
        self.assertTrue(brew_done(92.0 + 50.0, 92.0, 36.0))


if __name__ == "__main__":
    unittest.main()
