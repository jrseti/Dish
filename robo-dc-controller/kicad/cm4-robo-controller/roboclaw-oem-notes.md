# RoboClaw OEM 2x15A — KiCad symbol & footprint

Created from `docs/oem_roboclaw_datasheet_2x15A.pdf` (Basicmicro, © 2016).

| Asset | Location |
|---|---|
| Symbol | `MyParts:ROBOCLAW-2X15A-OEM` → `parts/myparts.kicad_sym` |
| Footprint | `MyParts:MOD-TH_ROBOCLAW-OEM-2X15A` → `parts/myparts.pretty/` |

Both parse and plot cleanly under kicad-cli 10.0.1. Library backup:
`parts/myparts.kicad_sym.bak-20260906-204201`.

## How the geometry was derived

The datasheet dimensions **only** the board outline, the mounting-hole pattern and
the module thickness. It does **not** dimension the header positions. To get those,
the drawing pages were exported as vector art (`pdftocairo -svg`) and the pin
rectangles measured directly, with the scale calibrated against the two dimensions
that *are* given.

Calibration and cross-checks:

- Scale from the M3 hole pattern (41.50 × 47.25 mm): **0.22469 mm/pt on both axes**
  (agreement to 5 decimal places).
- Extracted pin pitch came out **2.540 mm** on every row of both headers — an
  independent confirmation the scaling is right.
- The same artwork appears on p.5, p.7 and p.15 at three different scales and two
  rotations. All three give the same header offsets to within **0.03 mm**.
- Board 47.50 × 53.25 with holes 3.00 mm in from each edge is self-consistent:
  47.50 − 2(3.00) = 41.50, 53.25 − 2(3.00) = 47.25.

## Extracted geometry

Origin = board centre, viewed from the component (top) side. This is the same view
you get looking down at the module plugged into the carrier, so coordinates map
straight onto a top-layer footprint with **no mirroring**.

- Board 47.50 (X) × 53.25 (Y) mm, ~1 mm corner radius
- 4 × M3 mounting holes at (±20.75, ±23.625) — 3.2 mm NPTH in the footprint
- Body 9.28 mm tall; pins protrude 5.06 mm below the module PCB (14.34 − 9.28)

**Control header — 2×9, near the −Y edge**

- Outer row (board edge, pin 1) Y = −19.81; inner row Y = −17.27
- Position 1 at X = +9.17, running toward −X in 2.54 mm steps
- Header centre X = −0.99 (i.e. offset ~1 mm from board centre)

| Pos | X | Outer (board edge) | Inner (heatsink side) |
|---|---|---|---|
| 1 | +9.17 | LB_IN | 5VDC |
| 2 | +6.63 | GND | GND |
| 3 | +4.09 | 1A | 1B |
| 4 | +1.55 | 2A | 2B |
| 5 | −0.99 | S1 | GND |
| 6 | −3.53 | S2 | VBUS |
| 7 | −6.07 | S3 | DP |
| 8 | −8.61 | S4 | DM |
| 9 | −11.15 | S5 | GND |

Outer/inner assignment is fixed by the datasheet text: *"Channel A of both EN1 and
EN2 are located at the board edge… Channel B pins are located near the heatsink."*

**Motor / battery header — 2×12, near the +Y edge**

- Outer row (board edge, pin 1) Y = +21.34; inner row Y = +18.80
- Position 1 at X = −13.98, running toward +X in 2.54 mm steps
- Header centre X = −0.01 (essentially centred)

Each signal occupies a 2×2 block of four pins, left to right:

| Signal | X positions |
|---|---|
| M1A | −13.98, −11.44 |
| M1B | −8.90, −6.36 |
| BAT+ | −3.82, −1.28 |
| BAT− | +1.26, +3.80 |
| M2B | +6.34, +8.88 |
| M2A | +11.42, +13.96 |

## ⚠ The one thing to verify before fabrication

**The header positions are scaled from the drawing, not read off a dimension.**
Pitch (2.54) and the hole pattern are solid. What carries residual risk is the
*absolute* placement of each header relative to the mounting holes — in particular
the **control header's ~1 mm X offset from board centre**, which shows up
consistently in all three views but is never dimensioned.

Before ordering boards, check with calipers on the physical module:

1. Control-header pin 1 → nearest mounting-hole centre, in X and Y.
2. Motor-header pin 1 → nearest mounting-hole centre, in X and Y.
3. Centre-to-centre distance between the two headers' pin-1 pads.

Expected from the extraction: control pin 1 at (+9.17, −19.81), motor pin 1 at
(−13.98, +21.34), with holes at (±20.75, ±23.625).

Holes are 1.1 mm for 0.64 mm square posts, which absorbs roughly ±0.2 mm of error.
A 1 mm systematic offset would still bind, so the check is worth doing.

## Pad naming

Pads are named by **function**, not by sequential number, because each
motor/battery signal is four physically separate pins that are one net on the
module. Naming all four `M1A` lets KiCad treat them as a single net, so the symbol
needs one pin per signal instead of you shorting four pins by hand in the
schematic. Same for the four `GND` pads on the control header.

`BAT−` and `GND` are deliberately **kept as separate symbol pins** even though they
are common on the module — that lets the high-current return be routed separately
and joined to logic ground at a single star point, per the layout plan.

## Carrier-board notes

- Datasheet asks for **multi-layer copper pour** on the motor/battery pins. At
  15 A/channel continuous (30 A peak) each of the 4 pins carries ~3.75 A, so pour
  on more than one layer and stitch generously.
- Min copper gap between different nets in this footprint is **0.54 mm** (verified).
  BAT+ to BAT− sits at that gap and can see 34 V — fine for clearance, but keep
  the pour necking in mind.
- If the module is soldered flush its body sits on the carrier, leaving no room for
  components underneath. Female sockets raise it ~8 mm. The courtyard covers the
  full 47.50 × 53.25 outline either way — treat it as a keepout unless you socket it.

### Isolation caveat

The plan is to galvanically isolate the UART (S1/S2 + GND) between CM4 and
RoboClaw. Note that **VBUS/DP/DM/GND on the control header share the RoboClaw's
ground**. Wiring the USB service port straight to the CM4 shorts across the
isolation barrier and defeats it. Options:

- Bring USB out to its own receptacle for a *host* PC (Motion Studio setup), not to
  the CM4 — keeps the barrier intact during normal operation.
- Or use an isolated USB bridge if the CM4 really needs the USB path.
