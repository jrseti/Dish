# RoboClaw + CM4 Project Summary

## Project Goal
Design a new PCB where:
- One side is a Raspberry Pi CM4 carrier board.
- The other side accepts a RoboClaw OEM module.
- Two DC motors controlled by RoboClaw move a satellite dish.

## Key Decisions

1. Primary CM4 to RoboClaw communication:
- Use TTL UART in Packet Serial mode for runtime control.
- Packet Serial was preferred over Simple Serial due to CRC, acknowledgments, and richer telemetry.

2. USB role:
- Use USB mainly for Motion Studio setup, diagnostics, and firmware updates.
- Do not depend on USB as primary runtime control in motor-noisy environments.

3. RoboClaw OEM USB physical interface:
- Your OEM version is being treated as USB over header pins, not a populated micro-USB connector.
- Carrier board should host the USB receptacle and route to RoboClaw USB header pins.

4. Power and layout architecture:
- Keep a barrier between CM4 logic side and high-current RoboClaw/motor side.
- Use separate power domains for logic/computing and motors.
- Keep high-current return paths away from CM4 and sensitive signal routing.

5. Isolation direction:
- You requested galvanic isolation.
- Recommended structure: isolate UART between CM4 and RoboClaw using a dual-channel digital isolator, with independent supplies on each side.

## Communication and Wiring Guidance Discussed

1. TTL UART (recommended for control):
- CM4 TX to RoboClaw S1 (RX).
- RoboClaw S2 (TX) to CM4 RX.
- Packet Serial mode enabled on RoboClaw.

2. USB mapping (for service/config path on carrier board):
- VBUS to VBUS
- D+ to DP
- D- to DM
- GND to GND

3. USB implementation notes:
- Keep D+ and D- short and routed as a pair.
- Place ESD protection near USB connector.
- Optional common-mode choke if noise is expected.
- Avoid sharing one USB data pair between CM4 and RoboClaw without proper switching architecture.

## Bench Cable Discussion

Temporary bench cable options were discussed for a 4-pin USB header setup:
- Build from cut USB cable or USB pigtail.
- Map wires carefully to VBUS, DP, DM, GND.
- Continuity check and short-check before plugging in.
- Keep cable short and away from motor wiring.

## Module Integration Decision

RoboClaw OEM was treated as suitable for carrier-board integration:
- Insert/solder via 2.54 mm headers.
- Carrier board hosts surrounding interface and protection circuitry.

## Symbol and Footprint Work Status

Current status:
- Requested to create KiCad symbol and footprint for RoboClaw OEM.
- Library context was inspected to match your existing project setup and style.
- No symbol or footprint has been finalized yet.

Why not finalized yet:
- Exact OEM mechanical/header geometry must be locked per your specific board revision for a reliable footprint.
- Functional pin intent is known, but exact pad coordinates/orientation still need authoritative confirmation.

## Files and Environment Discussed

In workspace:
- sym-lib-table
- fp-lib-table
- cm4-robo-controller.kicad_sch
- cm4-robo-controller.kicad_pcb

External parts library (inspected for format/style compatibility):
- /Users/jonr/Projects/Dish/parts/myparts.kicad_sym
- /Users/jonr/Projects/Dish/parts/myparts.pretty

## Next Steps to Resume

1. Lock RoboClaw OEM mechanical truth source:
- Exact header coordinates
- Pin-1 orientation per header block
- Mounting hole coordinates
- Board-edge offsets

2. Create CAD assets:
- Add RoboClaw OEM symbol to your symbol library.
- Add RoboClaw OEM module footprint to your footprint library with:
  - Through-hole pad pattern
  - Mounting holes
  - Silkscreen outline and pin-1 marks
  - Courtyard and optional keepout

3. Integrate and verify:
- Place symbol in schematic and assign footprint.
- Place module on PCB and check fit/clearances.
- Run ERC/DRC.

4. Add interface circuitry:
- Isolated UART link between CM4 and RoboClaw.
- USB service connector path to RoboClaw USB header pins.
- ESD and optional filtering for USB.

## Resume Checklist

When resuming, provide one of:
- Official OEM mechanical drawing with exact pin and hole coordinates, or
- Caliper measurements from your physical board.

Then proceed directly to symbol and footprint generation and integration into the current project.
