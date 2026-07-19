# Open frame

**Purpose:** there is no case. The machine is held by three kinds of
member and nothing else, so every part you can see is a part that does
something.

## The rule

A member exists only if it carries a component. That leaves:

- the oak base slab: the mass that stands on the counter, damps the
  pump, and gives every other part something to bolt to,
- two aluminum rails: they carry the deck, flank the boiler on the way
  up, and touch nothing else (scripts/check_layout.py enforces the
  clearance),
- one aluminum deck: it seats the boiler and the group in bored seats,
  carries the tank, and passes the tank outlet and the brew riser
  through two more bores.

Panels, covers and a back wall carry nothing, so they are not in the
design. The consequence is that the copper is the visible surface of
the machine, which is why the runs are routed to be looked at rather
than hidden: shortest sensible path, right angles, no crossings.

## What follows from it

- Every layout number has to be honest, because nothing is concealed.
  The layout checks grew accordingly: rails clear all components, the
  deck leaves material around each bore, the tank sits on the deck, and
  nothing overhangs the slab.
- The tank stands on the deck rather than hanging in a cabinet, which
  puts its outlet well above the pump inlet and keeps the suction line
  flooded (concepts/single-boiler-thermal.md covers the thermal side).
- Hot parts are reachable by design, so the safety chain is mechanical
  and independent of firmware (concepts/safety-architecture.md), and
  the parts you touch are oak: the base and the portafilter handle.
- Stiffness has to come from the members themselves. The deck is a
  balanced beam, loaded by the group forward of the rails and the tank
  behind them; rail gussets are a phase 2 detail (TODO.md).
