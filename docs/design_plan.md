# RCM_DishControllerBoard — Project Plan

The Axis Commander with a Raspberry Pi CM4 added on board. **Every existing capability is
retained**; the CM4 is additive, becoming an on-board host option alongside the external
RS485 host that the board already supports.

## Locked decisions

| Item | Decision |
|---|---|
| Architecture | STM32G474RET6 stays; Modbus register map stays; **all Axis Commander capability retained** |
| RS485 device port + passthrough | **Kept** (was removed in an earlier revision of this plan — that is reversed) |
| RS485 leader port | **Kept, still isolated** (ISOW1432) |
| Host link | CM4 **muxed onto USART1**, sharing the STM32 pins with the RS485 device transceiver |
| GPS | MAX-M10S + 1PPS retained, still on LPUART1 |
| CM4 variant | **CM4 with eMMC** — no SD slot, programmed via rpiboot |
| Ethernet | A70-112-331N126 magjack (same part CM4IO uses) |
| USB | **USB 2.0 only.** USB2514B 4-port hub behind an FSUSB42MUX, 2× USB-A + micro-USB OTG |
| CM4 I2C / SPI | Plain 3.3 V pin headers, series resistance + ESD |
| Board size / layers | **Determined by placement study** (Phase 5); 4-layer assumed |

## The governing constraint: STM32 pin budget

Keeping every existing capability means the STM32 has nothing spare. All three usable
UARTs are allocated, and ~46 of roughly 50 available I/O are assigned:

| UART | Pins | Function |
|---|---|---|
| USART1 | PB6 / PB7 | `RS485_1` — device/follower input (Modbus from host) |
| USART3 | PC10 / PC11 | `RS485_2` — leader port (`PD2` = `RS485_2_DE`) |
| LPUART1 | PB10 / PB11 | `RS232` — GPS NMEA |

There is therefore **no spare UART for a dedicated CM4 link**, which is why the CM4 is
muxed onto USART1 rather than given its own port.

### What the mux means

The CM4 and the external RS485 host are **mutually exclusive** — one Modbus leader at a
time, selected by hardware. In exchange:

- **Zero STM32 firmware change.** The MCU sees the same USART1 either way; same Modbus RTU
  framing, same register map, same baud. `REG_SYS_ADDR` and everything else stay valid.
- **Zero STM32 pin change.** No respin of the MCU section.
- The CM4 side is plain 3.3 V logic — no transceiver, no DE/RE turnaround on that path.

Two ways to build it:

1. **Discrete 2:1 mux (recommended).** `SN74CBTLV3257` (quad 2:1, one package covers TX and
   RX) or two `74LVC1G3157`. One select line, unambiguous behaviour, easy to document and
   probe.
2. **Lower part count, using the transceiver's own enable.** The ISOW1432 has an independent
   active-low `RE` with an internal pull-up — *"If pin is floating, receiver buffer is
   disabled"* — so its receiver output can be tri-stated off the STM32 RX node. The STM32 TX
   line can feed the transceiver `D` input and the CM4 RX simultaneously with no contention,
   since both are inputs. This still needs the CM4 TX gated (a `74LVC1G125` or similar) to
   avoid fighting the transceiver output. Fewer parts, but the correctness depends on two
   enables never overlapping.

**Select signal:** drive it from a **jumper**, defaulting to CM4, with optional pads for a
CM4 GPIO override. A jumper is the robust choice — if the CM4 fails, you can still fall back
to an external host without needing the CM4 to cooperate.

## Other CM4 gotchas

**`GPIO_VREF` must be powered.** The BCM2711 GPIO bank is powered from this pin — tie it to
+3.3 V for 3.3 V signalling. The CM4 will not operate correctly if it is left unpowered.

**GPIO2 and GPIO3 already have 1.8 kΩ pull-ups on the module**, so an I2C bus on those pins
needs no external pull-ups on the carrier.

**Keep total GPIO load under 50 mA** across the 28 GPIO pins.

**`nRPIBOOT` is sampled at reset, not continuously.** Fit jumper → power-cycle → run
`rpiboot`. On a dish-mounted board, bring `GLOBAL_EN` out to a header so a power-cycle
doesn't mean a climb.

**The CM4's USB interface is disabled by default** to save power — host mode needs
`otg_mode=1` in `config.txt`, or the USB-A ports are dead with no hardware fault.

**Use a PL011 UART, not the mini-UART.** The default `GPIO14/15` UART is the mini-UART,
whose baud derives from the VPU core clock and drifts as that clock scales. Fine for a
console, bad for Modbus RTU timing.

**Why not USB 3.0.** It needs a VL805 PCIe→USB3 controller (RPi's CM4IOUSB3, doc RP-008176),
consuming the only PCIe lane and awkward to source at JLCPCB, to solve a bandwidth problem
this design does not have. Layer count is *not* the objection — both RPi reference boards
are 4-layer. The decisive point: **rpiboot can never run through VL805 ports**, since the
boot ROM never enumerates PCIe, so the USB 2.0 mux and micro-USB path are required anyway.

**Reference designs.** RPi publishes both as KiCad projects with gerbers: RP-008173 (CM4IO,
USB 2.0 hub + OTG) and RP-008176 (CM4IOUSB3, VL805).

---

## Phase 1 — Repo setup ✅ complete

KiCad project forked from `jrdish_axis_controller` @ `5318ffa` and renamed to
`rcm_dish_controller` (verified: identical netlist, 243 components / 163 nets). Firmware
`.ioc` renamed with all `TARGET` references updated (verified: `make` exits 0). KiCad-aware
`.gitignore` in place. Design files live in `kicad/`.

## Phase 2 — Design documentation (before any schematic edits)

Deliverables into `docs/`, all reviewable as text:

1. **Block diagram** — updated from `board_diagram.drawio`: CM4 added as an on-board host
   alongside the retained external RS485 host input, with the USART1 mux shown explicitly.
   Add Ethernet, USB, OTG, I2C/SPI headers.
2. **CM4 pin map** — every mezzanine signal used, with CM4 pin, net, and destination.
3. **STM32 pin delta** — expected to be **none**. Document the mux instead.
4. **Power budget** — see Phase 3.
5. **Modbus delta** — expected to be **none**.

## Phase 3 — Power architecture (the largest electrical change)

| Load | Rail | Budget |
|---|---|---|
| CM4 (peak, all cores + I/O) | 5 V | ~3 A headroom (typ 0.6–1.5 A) |
| 2× USB 2.0 ports | 5 V | 2× 0.5 A |
| USB hub + mux ICs | 3.3 V / 5 V | ~0.1 A |
| STM32 + GPS + isolators + sensors | 3.3 V | existing |
| Fan + 2 encoders | 12 V | existing |

- New **12 V → 5 V buck, ≥4 A**, sized for CM4 peak plus both USB ports.
- Feed the 3.3 V MP2322 from the new 5 V rail rather than 12 V — less dissipation, part
  already proven in-circuit.
- **Re-spec the input path**: fuse, reverse-polarity FET, DC jack and input filter now carry
  ~30 W rather than a few watts. Check the existing choke and connector against the new
  current rather than assuming.
- **Per-port USB current limiting** on the two type-A ports.
- CM4 housekeeping rails and straps: `GPIO_VREF` → +3.3 V, `GLOBAL_EN`, `RUN_PG`,
  `nRPIBOOT`, `EEPROM_nWP`.

## Phase 4 — Schematic changes

**Sheets carried over untouched:** `axis_control_1`, `axis_control_2` (isolated PWM out,
isolated encoder in, limit switches), `i2c`, `fan`, `user_switches`, `gps_rs232`, SPI flash,
STM32 core + SWD/SWO.

**Sheets modified:**
- `RS485.kicad_sch` — **device input and passthrough stay.** Add the USART1 mux between the
  RS485_1 transceiver and the CM4, plus its select jumper.
- `power.kicad_sch` — per Phase 3.

**New sheet `cm4.kicad_sch`:**
- 2× Hirose DF40C-100DS-0.4V mezzanine connectors
- `GPIO_VREF` tied to +3.3 V
- Gigabit Ethernet: A70-112-331N126 magjack. The CM4 carries the BCM54210PE PHY on-module,
  so this magjack **must** include magnetics (it does) — plus Bob Smith termination and the
  activity/link LED lines.
- **USB section — copy RPi's `USB2-HUB.kicad_sch` (CM4IO, RP-008173) near-verbatim:**

  ```
  CM4 USB_N/USB_P (103/105)
        │
   FSUSB42MUX                     2:1 analog USB mux
    ├── USBD_N/P ──→ micro-USB OTG receptacle   (rpiboot, device)
    └── USBH_N/P ──→ USB2514B-I/M2 4-port hub   (host)
                        ├── HD1, HD2 → 2× USB-A
                        └── HD3, HD4 → internal header (optional, unpopulated)
   mux select ←── micro-USB ID pin, also feeding CM4 USB_OTG_ID (101)
   nEXTRST (100) ──→ hub reset
  ```

  Supporting parts from the same sheet: **AP2553W6 / AP22653W6** current-limited port power
  switches with overcurrent sense, **TPD4EUSB30** ESD arrays on every external pair, hub
  strap resistors, hub crystal. Fit the 4-port hub even though two ports suffice — same die
  cost, spare ports become unpopulated headers. Add common-mode chokes on the downstream
  pairs: USB is broadband noise and the MAX-M10S shares this board.
- **CM4 I2C header** — SDA / SCL / +3.3 V / GND. If using GPIO2/GPIO3, the module's internal
  1.8 kΩ pull-ups suffice.
- **CM4 SPI header** — MOSI / MISO / SCLK / CE0 / CE1 / +3.3 V / GND.
- Both headers: **CM4 GPIO is 3.3 V and not 5 V tolerant.** Series resistance, ESD
  protection, and clear silkscreen. Short in-enclosure runs only.
- **Boot-control jumpers** — see pin table below.

**CM4 boot-control / programming pins.** Datasheet numbering is continuous 1–200 across both
mezzanine connectors; pins ≥ 101 are on the second connector. Confirm the physical pad
mapping against the KiCad CM4 footprint before routing.

| Signal | Pin | Purpose | Internal state |
|---|---|---|---|
| `nRPIBOOT` | 93 | Short to GND to force USB boot. **Required.** | 10 kΩ pull-up to +3.3 V |
| `EEPROM_nWP` | 20 | Ground to write-protect the bootloader EEPROM | 100 kΩ pull-up to CM4_3.3V |
| `GLOBAL_EN` | 99 | Drive low to power off — power-cycle into rpiboot | 100 kΩ pull-up to +5 V |
| `RUN_PG` | 92 | Drive low via 220 Ω to reset the CPU | 10 kΩ pull-up to +3.3 V |
| `USB_OTG_ID` | 101 | Host/device select — **input**, driven by micro-USB ID pin | Internally pulled up |
| `USB_N` / `USB_P` | 103 / 105 | The single USB 2.0 interface | — |

Keep `EEPROM_nWP` on a jumper rather than hard-grounding it: the CM4 cannot run
`recovery.bin` from eMMC, so usbboot is the only route to update the bootloader EEPROM.

**Proposed addition (recommend, small cost):** wire two CM4 GPIOs to the STM32's `NRST` and
`BOOT0`, letting the CM4 flash STM32 firmware over the muxed UART via the built-in
bootloader — no SWD probe at the dish. With Ethernet back to the house, in-field firmware
update becomes remote instead of a climb.

**Carry the known fix:** the encoder-input RC correction (commit `9e2432b`) is already in the
`5318ffa` baseline. Confirm it survives into the new layout.

## Phase 5 — Floorplan and layout (drives the board size decision)

The outline and layer count fall out of this phase rather than being fixed up front. This
is where the risk sits: a 4-layer board carrying a CM4, gigabit Ethernet, USB, a GPS
receiver, and multiple isolated ground islands — with nothing removed to make room.

- **Zone A (noisy/high-speed):** CM4, Ethernet, USB, OTG — one end.
- **Zone B (isolated field I/O):** motor, encoder, limit switch, both RS485 ports —
  opposite end, existing ground islands (`GND1`, `GND2`, `GNDIO`, `RS485_1_GND`,
  `RS485_2_GND`) preserved.
- **Zone C (GPS):** MAX-M10S as far from CM4/Ethernet/USB and the switching 5 V rail as the
  outline allows, at a board edge, disciplined ground pour, consider a shield can. A GPS
  front end beside a gigabit PHY is a genuine EMI risk, not a theoretical one.
- **Controlled impedance:** Ethernet and USB 2.0 both need 90–100 Ω differential. Confirm a
  JLCPCB 4-layer impedance-controlled stackup and compute geometry from *that* stackup
  before routing.
- Output of this phase: final outline, layer count, and connector edges.

## Phase 6 — Firmware and host software

- **STM32: no change expected.** Same USART1, same Modbus RTU, same register map. Bump
  `MODBUS_FW_VERSION` only if something else changes.
- **Host:** the Python in `software/` (`modbus_menu.py`, `modbus_test.py`) moves from the Mac
  to the CM4; change the serial device to the PL011 (`/dev/ttyAMA*`).
- The position loop is still unproven. This board should not be gated on it — bring-up order
  is power → CM4 boot → mux/UART/Modbus link → axis I/O.

## Phase 7 — Review gates

1. ERC clean; DRC clean against the existing `.kicad_dru`.
2. Power budget re-checked against measured CM4 draw before ordering.
3. BOM sourcing check on JLCPCB — hub, mux, magjack, buck, DF40C connectors.
4. Fab output via the existing fabrication-toolkit config.

## What I can and cannot do here

Phases 1, 2, 3, 6 and the documentation throughout — repo scaffolding, pin maps, power
calculations, block diagram source, firmware/host edits.

**Schematic capture and layout are GUI work in KiCad.** I can prepare netlists, pin
assignment tables and review the resulting files, but I will not be drawing sheets or
routing copper. Phases 4 and 5 are yours; I support them with documentation and review.

## Open items

- Whether the generic 8-pin GPIO header is still wanted alongside the I2C and SPI headers.
- Which CM4 I2C and SPI instances to use, and which PL011 for the STM32 link.
- Enclosure/mounting constraints — drives the outline and connector edges.
- Whether the RS485 leader port keeps its own isolated DC-DC or shares one.
- Surge protection for the outdoor Ethernet run; the magjack magnetics isolate, but the
  cable run to the house deserves a decision.
