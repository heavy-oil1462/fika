# Single dual-use boiler

**Purpose:** one copper boiler serves both espresso water (~93 C) and
steam (~125 C), keeping the machine minimal: one vessel, one element,
one PID.

## Why single boiler

Dual boilers and heat exchangers buy simultaneous brew and steam at the
cost of a second vessel or muddier brew temperature control. fika's
aesthetic and philosophy is a small number of solid parts; waiting
half a minute between shot and milk is an accepted trade. The PID
retargets between two setpoints (steam_mode.yaml); brewing is
interlocked at steam temperature because 125 C water would scorch the
shot.

## Thermal notes

- 1.0 l fill, 1400 W element: about 4 min from cold to brew temperature
  (outputs/budgets/energy_budget.md is the generated truth; the verify
  gate keeps it under 6 min).
- The element enters the bottom cap; the PT100 sits in a well at mid
  height, away from the element so the PID sees water, not element skin.
- Steam is drawn from the top; brew water from low in the vessel via
  the front outlet. Fresh feed enters the bottom, which also tempers
  brew-temperature droop during a shot.
- The vessel is copper with brass ports, silver brazed with lead free
  alloy. Purchased or commissioned, never printed and never improvised
  (concepts/safety-architecture.md).
