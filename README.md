# RCM_DishControllerBoard

A satellite dish motion controller with an on-board **Raspberry Pi Compute Module 4**.

This board carries the CM4 as the local host for the STM32-based two-axis motion
controller, replacing the external PC/Pi that previously commanded the design over a long
RS485 run.

## Provenance

Derived from the **Axis Commander** (`jrdish_axis_controller`).

| | |
|---|---|
| Source repo | `git@github.com:jrseti/pcbs.git` |
| Source path | `jrdish_axis_controller/` |
| Source commit | `5318ffa` — *"Updated parts"* |
| KiCad project renamed | `jrdish_axis_controller` → `rcm_dish_controller` |

The Axis Commander's own history stays in the `pcbs` monorepo; this repo starts fresh
rather than importing it. The baseline includes commit `9e2432b`, which corrected the
encoder input RC values that caused missed ticks at speed on V1.1.

## What changes from the Axis Commander

**Kept:** STM32G474RET6 motion layer, the full Modbus register map, isolated PWM outputs
and encoder inputs, limit switches, isolated I²C to per-axis sensors, MAX-M10S GPS with
1PPS, SPI flash, fan output, user switches.

**Removed:** the RS485 device/follower input port and its passthrough connector — the host
is now on-board.

**Changed:** the CM4 talks to the STM32 over a plain 3.3 V UART (no transceivers on either
end), carrying the same Modbus RTU framing. The isolated RS485 *leader* port remains for
driving servos or downstream equipment.

**New — CM4 carrier section:**

- 2× Hirose DF40C-100DS-0.4V mezzanine connectors
- microSD slot for the CM4 OS
- Gigabit Ethernet via an A70-112-331N126 magjack
- 2× USB 2.0 from a hub IC off the CM4's single USB 2.0 host
- 8-pin GPIO header
- 12 V → 5 V buck sized for the CM4 plus both USB ports

### Two hard constraints

**A CM4 Lite is required.** The mezzanine SD interface is only usable on Lite modules; on
any eMMC variant those lines are dedicated to the eMMC and the card slot will not work.

**The CM4 must use a PL011 UART for the STM32 link, not the default mini-UART.** The
mini-UART on GPIO14/15 derives its baud rate from the VPU core clock and drifts as that
clock scales — unsuitable for Modbus RTU timing.

## Layout

```
kicad/       KiCad project
               rcm_dish_controller.kicad_pro/.kicad_sch/.kicad_pcb/.kicad_dru
               RS485 · axis_control_1 · axis_control_2 · fan · gps_rs232
               i2c · notes · power · user_switches          subsheets
               fp-lib-table · sym-lib-table                 library tables
docs/        datasheets, board diagram, design notes, design plan
software/    STM32 firmware (Core, Drivers, CubeMX .ioc) + host Python
```

## External dependency

The symbol and footprint tables reference `${MYPARTS}`, a KiCad environment variable
pointing at the shared parts library that lives in the `pcbs` repo. KiCad must have
`MYPARTS` configured or symbols and footprints will not resolve. This is worth revisiting
before any open-source release, since it makes the project non-self-contained.

## Status

Schematic and layout are the Axis Commander's, unmodified, serving as the starting point.
The CM4 carrier section is not yet drawn. See `docs/design_plan.md`.

## License

MIT — see [LICENSE](LICENSE).
