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

**Nothing is removed.** Every Axis Commander capability is retained: the STM32G474RET6
motion layer, the full Modbus register map, isolated PWM outputs and encoder inputs, limit
switches, isolated I²C to per-axis sensors, MAX-M10S GPS with 1PPS, SPI flash, fan output,
user switches, and **both** RS485 ports — the device/follower input with its passthrough,
and the isolated leader port.

**The CM4 is additive**, giving the board an on-board host option alongside the external
RS485 host it already supports.

**Host link — the CM4 is muxed onto USART1.** All three of the STM32's usable UARTs are
already allocated (USART1 = RS485 device, USART3 = RS485 leader, LPUART1 = GPS NMEA), and
~46 of roughly 50 available I/O are assigned, so there is no spare port for a dedicated CM4
link. A 2:1 mux on PB6/PB7 selects between the RS485 device transceiver and the CM4. The
CM4 and an external host are therefore **mutually exclusive** — one Modbus leader at a time.
In exchange the STM32 needs **no pin or firmware change at all**: same USART1, same Modbus
RTU framing, same register map.

**New — CM4 carrier section:**

- 2× Hirose DF40C-100DS-0.4V mezzanine connectors
- Gigabit Ethernet via an A70-112-331N126 magjack
- 2× USB 2.0 from a USB2514B hub behind an FSUSB42MUX host/device mux
- micro-USB OTG receptacle for eMMC programming via `rpiboot`
- CM4 I²C and SPI broken out to plain 3.3 V pin headers
- USART1 mux selecting CM4 vs. the external RS485 host
- `nRPIBOOT` / `EEPROM_nWP` / `GLOBAL_EN` boot-control jumpers
- 12 V → 5 V buck sized for the CM4 plus both USB ports

**USB 2.0 only — no USB 3.0.** USB 3.0 on a CM4 requires a VL805 PCIe→USB3 controller,
which would consume the board's only PCIe lane to solve a bandwidth problem this design
does not have. It would also be purely additive: rpiboot can never run through VL805
ports, so the USB 2.0 mux and micro-USB path below are required either way.

The module is a **CM4 with eMMC** (not Lite). There is no SD card slot — the eMMC is
programmed over USB with `rpiboot`.

### eMMC programming

All pin numbers are from the CM4 datasheet's continuous 1–200 numbering across the two
mezzanine connectors; pins ≥ 101 are on the second connector.

| Signal | Pin | Purpose | Internal state |
|---|---|---|---|
| `nRPIBOOT` | 93 | Short to GND to force USB boot. **Required.** | 10 kΩ pull-up to +3.3 V |
| `EEPROM_nWP` | 20 | Ground to write-protect the bootloader EEPROM | 100 kΩ pull-up to CM4_3.3V |
| `GLOBAL_EN` | 99 | Drive low to power off — power-cycle into rpiboot | 100 kΩ pull-up to +5 V |
| `RUN_PG` | 92 | Drive low via 220 Ω to reset the CPU | 10 kΩ pull-up to +3.3 V |
| `USB_OTG_ID` | 101 | Host/device select — **input**, driven by the micro-USB ID pin | Internally pulled up |
| `USB_N` / `USB_P` | 103 / 105 | The single USB 2.0 interface | — |

Keep `EEPROM_nWP` on a jumper rather than hard-grounding it: the CM4 cannot run
`recovery.bin` from eMMC, so usbboot is the only way to update the bootloader EEPROM.

`nRPIBOOT` is sampled by the boot ROM **at reset**. The sequence is: fit the jumper, then
power-cycle, then run `rpiboot` on the host. Fitting it on a running board does nothing —
which is why `GLOBAL_EN` is worth bringing out to a header on a dish-mounted board.

### USB topology

Copied from Raspberry Pi's CM4IO reference design (`USB2-HUB.kicad_sch`, doc RP-008173):

```
CM4 USB_N/USB_P (pins 103/105)
        │
   FSUSB42MUX                      2:1 analog USB mux
    ├── USBD_N/P ──→ micro-USB OTG receptacle    (rpiboot, device)
    └── USBH_N/P ──→ USB2514B 4-port hub         (host)
                        ├── HD1 ┐
                        ├── HD2 ┴→ 2× USB-A
                        ├── HD3 ┐
                        └── HD4 ┴→ internal header (optional)
   mux select ←── micro-USB ID pin, also feeding CM4 USB_OTG_ID (pin 101)
   nEXTRST (pin 100) ──→ hub reset
```

Supporting parts from the same sheet: **AP2553W6 / AP22653W6** current-limited port power
switches with overcurrent sense, **TPD4EUSB30** ESD arrays on every external pair, hub
strap resistors, and the hub crystal.

Fit the 4-port hub even though only two ports are needed — the die cost is identical, and
the spare two can be left as unpopulated internal headers.

### Hard constraints

**`GPIO_VREF` must be tied to +3.3 V.** The BCM2711 GPIO bank is powered from this pin;
leave it unpowered and the CM4 will not operate correctly. Note also that GPIO2 and GPIO3
carry 1.8 kΩ pull-ups on the module, so an I²C bus on those pins needs no external
pull-ups, and total GPIO load should stay under 50 mA.

**The single USB 2.0 interface is shared between the hub and rpiboot.** `USB_N`/`USB_P` are
the CM4's only USB interface. rpiboot needs them presented to a host PC as a *device* while
the hub uses them as a *host*, so they cannot both be permanently wired — hence the mux
above. Note `USB_OTG_ID` is an **input** on the CM4: the micro-USB ID pin is the signal
source, and it drives both the mux select and the CM4 input from one node.

**The CM4's USB interface is disabled by default** to save power. Host mode needs
`otg_mode=1` in `config.txt`, or the USB-A ports are simply dead with no hardware fault.

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
