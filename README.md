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

**One thing is removed.** Every other Axis Commander capability is retained: the
STM32G474RET6 motion layer, the full Modbus register map, isolated PWM outputs and encoder
inputs, limit switches, isolated I²C to per-axis sensors, MAX-M10S GPS with 1PPS, SPI
flash, fan output, user switches, and the isolated RS485 leader port.

**The RS485 device/follower port is gone.** The CM4 becomes the Modbus leader, so the board
no longer accepts an external host over RS485. `RS485.kicad_sch` now carries a single
ISOW1432 — the isolated leader — and the follower transceiver and its passthrough are gone.

**Host link — the CM4 drives USART1 directly.** All three of the STM32's usable UARTs were
already allocated (USART1 = RS485 device, USART3 = RS485 leader, LPUART1 = GPS NMEA), and
~46 of roughly 50 available I/O are assigned, so adding the CM4 meant taking one. An earlier
plan muxed the CM4 and the RS485 device transceiver onto PB6/PB7 with a 2:1 analog switch;
that was dropped in favour of removing the device port outright. USART1 is now a plain
3.3 V full-duplex link to the CM4 — no transceiver, no DE control, PB5 freed.

The STM32 keeps the same USART1, the same Modbus RTU framing and the same register map, but
the firmware did change: DE handling is gone from `modbus.c`, the node address is fixed at 1
(the link is point-to-point, so there is no bus to disambiguate), and the `ADDR0`–`ADDR2` /
`CONFIG_SW` DIP inputs are now general-purpose `SW1`–`SW4`.

**New — CM4 carrier section:**

- 2× Hirose DF40C-100DS-0.4V mezzanine connectors
- Gigabit Ethernet via an LPJG0926HENL magjack
- 2× USB 2.0 from a USB2514B hub behind an FSUSB42MUX host/device mux
- USB-C receptacle for eMMC programming via `rpiboot`
- CM4 I²C and SPI broken out to plain 3.3 V pin headers
- Boot console (GPIO14/15) on a 3-pin 3.3 V header
- `nRPIBOOT` / `EEPROM_nWP` / `GLOBAL_EN` boot-control jumpers
- 12 V → 5 V buck (AP64501) sized for the CM4 plus both USB ports

**USB 2.0 only — no USB 3.0.** USB 3.0 on a CM4 requires a VL805 PCIe→USB3 controller,
which would consume the board's only PCIe lane to solve a bandwidth problem this design
does not have. It would also be purely additive: rpiboot can never run through VL805
ports, so the USB 2.0 mux and USB-C path below are required either way.

The module is a **CM4 with eMMC and no wireless** (not Lite). There is no SD card slot —
the eMMC is programmed over USB with `rpiboot`. Dropping the radio frees UART0 for the boot
console and removes a 2.4/5 GHz transmitter from a board carrying a GPS receiver.

### eMMC programming

All pin numbers are from the CM4 datasheet's continuous 1–200 numbering across the two
mezzanine connectors; pins ≥ 101 are on the second connector.

| Signal | Pin | Purpose | Internal state |
|---|---|---|---|
| `nRPIBOOT` | 93 | Short to GND to force USB boot. **Required.** | 10 kΩ pull-up to +3.3 V |
| `EEPROM_nWP` | 20 | Ground to write-protect the bootloader EEPROM | 100 kΩ pull-up to CM4_3.3V |
| `GLOBAL_EN` | 99 | Drive low to power off — power-cycle into rpiboot | 100 kΩ pull-up to +5 V |
| `RUN_PG` | 92 | Drive low via 220 Ω to reset the CPU | 10 kΩ pull-up to +3.3 V |
| `USB_OTG_ID` | 101 | Host/device select — **input**, driven by a VBUS-sense divider on the USB-C port | Internally pulled up |
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
    ├── HSD2 ──→ USB-C receptacle               (rpiboot, device)
    └── HSD1 ──→ USB2514B 4-port hub            (host)
                        ├── HD1 ┐
                        ├── HD2 ┴→ 2× USB-A
                        ├── HD3 ┐
                        └── HD4 ┴→ internal header (optional)
   mux select ←── USB-C VBUS via a 2.2k/2.2k divider, the same
                  node feeding CM4 USB_OTG_ID (pin 101)
   nEXTRST (pin 100) ──→ hub reset
```

Supporting parts from the same sheet: **AP22653W6** current-limited port power
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
above. `USB_OTG_ID` is an **input** on the CM4, and one node drives both it and the mux
select — a 2.2 kΩ / 2.2 kΩ divider off the USB-C VBUS. Plug a host in and VBUS pulls that
node high, switching the mux to the USB-C port and telling the CM4 it is a device; unplug
and the lower resistor returns it to ground and the CM4's USB to the hub. CC1 and CC2 each
carry a 5.1 kΩ Rd to ground, so the port advertises itself as a device.

**The CM4's USB interface is disabled by default** to save power. Host mode needs
`otg_mode=1` in `config.txt`, or the USB-A ports are simply dead with no hardware fault.

**The STM32 link is UART3 on GPIO4/GPIO5; the boot console keeps UART0 on GPIO14/15.** Both
are PL011s, not the mini-UART — the mini-UART's baud derives from the VPU core clock and
drifts as that clock scales, and Modbus RTU delimits frames by 3.5 character-times of
silence, so drift produces intermittent framing failures under load rather than clean
errors. On wireless CM4s UART0 belongs to Bluetooth and the mini-UART lands on GPIO14/15 —
but this design uses a **non-wireless** module, so UART0 is free, is the default primary
UART (`/dev/ttyAMA0`), and is left for the console header. The STM32 link needs
`dtoverlay=uart3` in `config.txt`; the console needs `enable_uart=1`.

The `CM4_TX` / `CM4_RX` net names are from the **STM32's** point of view: `CM4_TX` is the
STM32's PB6 output driving CM4 GPIO5 (RXD3), and `CM4_RX` is PB7 listening to CM4 GPIO4
(TXD3). Each has a 100 Ω series resistor at the CM4 end.

## Layout

```
kicad/       KiCad project
               rcm_dish_controller.kicad_pro/.kicad_sch/.kicad_pcb/.kicad_dru
               RS485 · axis_control_1 · axis_control_2 · fan · gps_rs232
               i2c · notes · power · power_3v3 · power_5v
               user_switches                                subsheets
               RCM4 · cm4_connectors · ethernet · usb        CM4 carrier
               fp-lib-table · sym-lib-table                 library tables
CM4_parts/   CM4IO symbols, footprints and 3D models from the Pi reference design
ref_designs/ Raspberry Pi CM4IO / CM5IO KiCad reference designs
docs/        datasheets, board diagram, design notes, design plan
software/    STM32 firmware (Core, Drivers, CubeMX .ioc) + host Python
```

## External dependency

The symbol and footprint tables reference `${MYPARTS}`, a KiCad environment variable
pointing at the shared parts library that lives in the `pcbs` repo. KiCad must have
`MYPARTS` configured or symbols and footprints will not resolve. This is worth revisiting
before any open-source release, since it makes the project non-self-contained.

`sym-lib-table` additionally holds an **absolute path** to `CM4_parts/CM4IO.kicad_sym`,
which will not resolve on any other machine. It should be
`${KIPRJMOD}/../CM4_parts/CM4IO.kicad_sym`.

## Status

The CM4 carrier is drawn — mezzanine connectors, Ethernet, the USB hub and mux, the USB-C
rpiboot path, and the 5 V / 3.3 V rails are all captured, and the project is at revision
2.0. See `docs/design_plan.md`.

## License

MIT — see [LICENSE](LICENSE).
