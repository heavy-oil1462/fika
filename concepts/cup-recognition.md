# Cup recognition

**Purpose:** the machine's controls should mostly be what the user
already does. Placing a cup on the tray is the order: the machine
recognizes which cup it is by weight and prepares that cup's drink, and
the shot stops itself at the right beverage weight.

## How

A bar load cell under the drip tray (cup_scale.yaml) weighs the tray
continuously. While idle, a stable weight within cup_tolerance_g of
exactly one calibrated cup tare selects that cup: the target beverage
weight is set and the detected cup is published. Flip the brew toggle
and the machine opens the valve, runs the pump, and stops
gravimetrically when beverage weight (current minus tare) reaches the
target.

## Rules that keep it honest

- Ambiguity selects nothing. Two cups within tolerance of the reading
  means no program is chosen; the machine never guesses. Calibrated
  tares must therefore differ by more than twice the tolerance.
- The matching rule exists once, in tools/cup_match.py, and the ESPHome
  lambda mirrors it line for line; tools/validate.py pins the shared
  tolerance and tools/test_cup_match.py pins the behavior.
- The brew toggle is still the commitment. Recognition arms a program,
  the human starts it; nothing pours because a cup appeared.
- No cup, no brew: the toggle logs a refusal if nothing was recognized.
