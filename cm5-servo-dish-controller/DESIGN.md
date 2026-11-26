# Hardware design

Design description for the CM5 Servo Dish Controller. The KiCad project files are
in [kicad/](kicad/).

## Status

- **Schematic:** first pass complete. KiCad's electrical rules check reports 0 violations.
- **PCB:** not started.
- **Not yet done:** nothing here has been built or reviewed by a second person.
  See [Open items](#open-items).
- **Earlier version:** the git tag `48v-input` is the previous design, which took
  48 V on the board and made 5 V with an on-board LM5116 buck.

Schematic PDF: [kicad/cm5-servo-dish-controller.pdf](kicad/cm5-servo-dish-controller.pdf)

## Board overview

A carrier board for a Raspberry Pi Compute Module 5 (CM5) with an STM32G474RET6 that
drives the dish's servo motors over CANopen. It is derived from the
[roboclaw-cm4-dc-dish-controller](https://github.com/jrseti/roboclaw-cm4-dc-dish-controller)
board. The CM5, Ethernet, GPS, I2C and header circuits are carried over. These parts changed:

| Area | RoboClaw CM4 board | This board |
|---|---|---|
| Motor control | RoboClaw 2x15A, brushed DC motors | Removed. An STM32G474RET6 is the CANopen master for external servo drives (e.g. DSY-400C) |
| Motor power | On the board (PGND, 15 A fuse) | None. The drives are wired straight to the 48 V supply |
| Encoders, limit switches, E-stop | On the board | Removed. They will be separate CANopen nodes (future boards) |
| Control loop | In the RoboClaw | In the STM32: it commands drive velocity and reads position over CAN |
| Module to controller link | UART, CM4 to RoboClaw | UART, CM5 to STM32 (same CM pins, GPIO12/13) |
| Supply | 12.8 V battery | 5 V DC from an external Mean Well DDR-60L-5, which converts and isolates the 48 V battery. No 48 V on the board |
| CAN bus | None | One isolated CANopen bus with two RJ45 jacks: J11 to the servo drives, J12 to the dish-side nodes, which it also powers (24 V `CAN_V+`). The isolated side has its own external supply (isolated 48 V to 24 V converter) |
| 5 V rail | eFuse + AP64500 buck | The 5 V input, through a fuse and two P-channel MOSFETs (reverse polarity, on/off) |
| Module | CM4 | CM5 |
| USB | USB 2.0 hub, 2 × USB-A | The CM5's two USB 3.0 ports on a stacked USB 3.0 Type-A connector |
| USB-C | rpiboot through a mux | rpiboot, wired straight to the CM5 USB 2.0 port |

### Schematic sheets

| Sheet | File | Contents |
|---|---|---|
| Top | `cm5-servo-dish-controller.kicad_sch` | Block diagram, grounding, mounting holes |
| power-input | `power-input.kicad_sch` | 5 V terminal, fuse, reverse-polarity and on/off MOSFETs, TVS, bulk capacitors, power LED, design notes |
| STM32 | `stm32.kicad_sch` | STM32G474RET6, its 3.3 V regulator, crystal, SWD, UART buffers, reset/boot control |
| STM32 / CAN | `can.kicad_sch` | Isolated CAN transceiver, choke, two RJ45 jacks, termination, 24 V isolated input, `CAN_V+` eFuse and its isolator, 5 V buck for the isolated side |
| CM5 | `cm5.kicad_sch` | CM5 module |
| CM5 / usb | `usb.kicad_sch` | USB 3.0 ports, port power switch, ESD |
| CM5 / usb / usb2 | `usb2.kicad_sch` | USB-C rpiboot port |
| CM5 / ethernet | `ethernet.kicad_sch` | Gigabit Ethernet (unchanged) |
| CM5 / CM5_Connectors | `cm5_connectors.kicad_sch` | GPIO header, boot jumpers, console UART |
| CM5 / I2C | `i2c.kicad_sch` | Temperature sensor, I2C connector (unchanged) |
| GPS | `gps.kicad_sch` | GPS receiver and 1PPS (unchanged) |

Each sheet carries notes explaining its part values.

### Power

- **Supply:** a Mean Well DDR-60L-5 DIN-rail converter, mounted off the board. It
  takes the 48 V battery (18–75 V input) and gives 5 V at up to 12 A, isolated to
  4 kVdc. Its +Vo terminals (3, 4) go to J7 pin 1 and its −Vo terminals (1, 2) to
  J7 pin 2. The board's load budget is 5 A.
- **Input:** J7 screw terminal, F2 (5×20 mm fuse, T6.3A), Q1 and Q2, then the `5V`
  rail with D2 (SMCJ6.0A surge clamp), C13–C18 (224 µF bulk) and LED3.
  - Q1 (SI7137DP P-channel MOSFET, 2.5 mΩ) is the reverse-polarity protection. A
    reversed supply leaves it off: nothing reaches the board and F2 does not blow.
  - Q2 (a second SI7137DP, back to back with Q1) is the on/off switch, driven by
    SW1. SW1 switches the board only; the converter stays powered.
  - TP13 is a bare pad on `V_IN_F` between F2 and Q1, for checking the fuse. TP14
    is the `5V` rail.
- **Isolated CAN supply:** a second external converter (isolated, 48 V to 24 V,
  15–30 W, part not chosen yet) feeds J13 on the CAN sheet. It powers only the
  isolated bus side: the dish-side nodes through the U21 eFuse (`CAN_V+` on J12
  pin 8, limited to 0.5 A) and a small buck (U23) that makes `5V_ISO` for the bus
  side of the transceiver and the isolator. Its negative output is `GND_ISO`,
  which has no connection to `GND` or `CHASSIS` on the board.
- **3.3 V:** the CM5 supplies `3V3_CM5` as before. The STM32 has its own regulator
  (`3V3_MCU`), so it keeps running while the CM5 is off or rebooting.

### STM32 and CAN

- **CAN:** one CANopen bus, galvanically isolated (U18 ISO1042 transceiver). The
  design brief is [plans/isolated-can-section-brief.md](../plans/isolated-can-section-brief.md)
  (2-jack, single-bus version, rev C1). The board is a middle node of one linear bus:
  `CAN_H`/`CAN_L` run straight from J11 (drive side, to DSY-C CN1) to J12 (dish side:
  weather bridge, AZ node, EL node), and the transceiver taps off through a
  common-mode choke. The bus runs classic CAN at 500 kbit/s; the transceiver also
  supports CAN FD.
  - Both jacks use the CiA 303-1 pinout: pin 1 CAN_H, pin 2 CAN_L.
  - J11: pin 3 is `GND_ISO` through a 0 Ω link (R51). Pins 4–8 are not connected,
    so no bus power can reach a drive.
  - J12: pins 3 and 7 are `GND_ISO`, pin 8 is `CAN_V+` (24 V). Pins 4–6 are not
    connected.
  - SW2 switches in a 120 Ω split termination. It stays OFF in this topology: the
    bus is terminated at the far drive (DIP SW4) and at the EL axis node.
  - Each jack has a CAN ESD clamp, and its shell goes to `CHASSIS` through a 0 Ω
    link, with an unfitted RC option (1 MΩ, 4.7 nF 2 kV).
- **Dish-side bus power:** `CAN_VBUS_EN` (PC8) switches `CAN_V+` through the U21
  eFuse, and `CAN_VBUS_FLT` (PC9) goes low on an eFuse fault. Both cross the barrier
  in U22 (ISO7721). The eFuse is on whenever PC8 is high or not driven, so the dish
  segment powers up without firmware.
- **Where the schematic differs from the brief:**
  - The 5 V buck is an LMR51606X (65 V, 0.6 A, SOT-23-6), not the LMR36006: 4,978
    in stock at JLCPCB against 215, and a standard package.
  - The input TVS D12 is the bidirectional SMBJ28CA. The SMBJ28A in the brief is
    unidirectional and would short a reversed supply instead of letting the eFuse
    block it. The output TVS D13 is the SMBJ28A.
  - The eFuse control pins are not wired straight to the isolator: SHDN goes
    through a divider (its recommended maximum is 4 V), and FLT through a 47 kΩ
    series resistor, which protects the isolator if the 24 V supply is reversed.
  - The under- and over-voltage thresholds are 8.6 V and 34.4 V (brief: about
    9–36 V), so that the over-voltage cut-off stays below 36 V at worst-case
    tolerance.
  - The CAN ESD clamps are the PESD2CANFD27V already on the board (27 V stand-off,
    above `CAN_V+`), and the termination link is the existing DIP switch SW2
    rather than a jumper.
  - The optional 0 Ω footprints on J12 pins 4–6 are not included.
  - Net names follow the board: `3V3_MCU` for +3V3, `5V_ISO` for +5V_ISO,
    `24V_ISO_IN` and `CAN_V+` for +24V_ISO, `CHASSIS` for PE.
- **UART to the CM5:** USART1 through two buffers powered from `3V3_CM5`, so the STM32
  never drives a pin of an unpowered CM5.
- **Firmware update from the CM5:** CM5 GPIO23 resets the STM32 and GPIO24 selects its
  system bootloader, which listens on the same USART1. No SWD probe is needed.
- **Debug:** STDC14 connector (STLINK-V3) with SWD, SWO and a virtual COM port.
- **Serial header:** J14 (1×3, 2.54 mm) brings out USART1 for a 3.3 V serial adapter
  when the CM5 is off or not fitted. Same pin order as J4: 1 `MCU_RX` (into the
  STM32), 2 `MCU_TX`, 3 `GND`. With the CM5 on, U16 also drives `MCU_RX` through
  R32, so the header is listen-only then.

STM32 pin use:

| Pin | Function | Connects to |
|---|---|---|
| PA9 / PA10 | USART1 TX / RX | CM5 GPIO13 / GPIO12, J14 |
| PA12 / PA11 | FDCAN1 TX / RX | ISO1042 (U18). R66 pulls TXD up to `3V3_MCU` |
| PC8 / PC9 | `CAN_VBUS_EN` (output) / `CAN_VBUS_FLT` (input, EXTI) | ISO7721 (U22), to the `CAN_V+` eFuse |
| PA13 / PA14 / PB3 | SWDIO / SWCLK / SWO | STDC14 |
| PA2 / PA3 | USART2 (or LPUART1) TX / RX | STDC14 virtual COM port |
| PC6 / PC7 | CANopen RUN (green) / ERR (red) LED | LED5 / LED6 |
| PF0 / PF1 | 24 MHz crystal | X1 |
| PG10 | NRST | CM5 GPIO23 (through Q3), STDC14 |
| PB8 | BOOT0 | CM5 GPIO24 |

All other pins are unconnected.

CM5 GPIO changes from the CM4 board: GPIO23 `MCU_RST`, GPIO24 `MCU_BOOT0`, GPIO25
`USB_nFAULT`. GPIO24/25 were the eFuse fault and power-good inputs.

## Open items

Check these before layout or ordering:

1. **5 V setting.** The converter's output is adjustable from 4.5 V to 5.5 V. F2, Q1,
   Q2 and the cable drop about 0.2 V at 5 A. With the board running, adjust the
   converter until TP14 reads 5.10 V. The CM5 needs 4.75–5.25 V.
2. **Supply over-voltage.** The converter is rated for 18–75 V input. If the servo
   drives can pump the 48 V bus above 75 V when braking, fit brake resistors on the
   drives. The 48 V feed to the converter also needs its own fuse, off the board.
3. **Fuse.** F2 is the fuse holder; the assembler does not fit the fuse. Fit a
   Littelfuse 021806.3MXP (6.3 A time-lag, glass, LCSC C142706) by hand. It is
   named in F2's `Fuse` field. Do not fit a larger fuse: the holder is rated 6.3 A.
   The converter limits its output to 12.6–16.2 A, which is only 2.0 to 2.6 times
   the fuse rating, so into a short F2 opens slowly (within 2 minutes at 13.2 A)
   and may not open at 12.6 A. The converter's current limit is the short-circuit
   protection. Lay out the copper from J7 through F2, Q1 and Q2 for 16 A.
4. **CM5 module connectors.** J1/J18 are still the Hirose DF40C-100DS-0.4V(51)
   parts from the CM4 board. The CM5 datasheet names Amphenol 10164227-1001A1RLF
   as the mating part, tested to the CM5's higher current.
5. **Self power-cycle circuit** (`nPWR_CYCLE`, U9) is carried over from the CM4
   board and is not proven on a CM5.
6. **Console UART notes** on the connectors sheet (how to enable the Linux console
   on GPIO14/15 on a CM5) need checking against current Raspberry Pi documentation.
7. **Part stock.** All fitted parts were checked against live JLCPCB stock on
   2026-11-17. USB1 was out of stock and was replaced by the Molex 48406-0003.
   U18 was changed to a CA-IS3052G for the same reason. Since 2026-11-24 it is
   the ISO1042DWR (SOIC-16 wide): the same transceiver as the SOIC-8 wide
   ISO1042DWVR, at $3.31 against $9.19. It needs one more 100 nF capacitor
   (C68), because the package has two VCC2 pins and each gets its own.
   The parts added for the isolated CAN section were checked on 2026-11-24. The
   lowest stocks were U18 (192), U22 ISO7721DWR (1,995), J11/J12 (3,230) and U23
   LMR51606XDBVR (4,978).
   Still low: U13 TPS70933DBVR (10), U20 LTC4311ISC6 (15), U19 LM75BIMX-3 (54),
   U14 STM32G474RET6 (72), J10 FTSH-107-01-L-DV-K-A (173). Recheck stock before
   ordering.
   The 5 V input parts were checked the same day: Q1/Q9 SI7137DP-T1-GE3 (C784367)
   and D2 SMCJ6.0A/TR13 (C310065) each had over 100,000 in stock.
   The USB1 footprint comes from EasyEDA; check it against the Molex drawing
   before layout.
8. **Net classes** in the project file were updated for the new net names, but the
   track widths are still the 12 V board's. `/5V` is in the `PWR_3A` class (1.0 mm)
   and the input nets in `V_IN` (2.0 mm): neither is enough for the 16 A input
   path in item 3, which needs copper pours.
   The Ethernet and USB pairs also carry net class flags on the CM5 sheet
   (`ETH_100_OHM`, `USB_90_OHM`), so the target impedance shows on the drawing.
9. **Drive CAN port isolation** (brief OPEN-1). The DSY-C manual does not say
   whether its CAN port is isolated. On an unpowered drive, measure the resistance
   from CN1 pin 3 to DC− and to PE. R51 is fitted either way; if the port is not
   isolated, it ties `GND_ISO` to the drive power ground and the dish domain no
   longer floats from the cabinet.
10. **Isolated 24 V converter** (brief OPEN-2). The part is not chosen: input
    18–75 V or wider, 15–30 W, 24 V out, output left floating.
11. **DSY-C pins 4–8** (brief OPEN-3). Check with a continuity test whether the
    drive passes them through between CN1 and CN2.
12. **Isolation barrier** (brief OPEN-5). A 7.1 mm gap with no copper pour on any
    of the four layers, widened from 6.0 mm on 2026-11-26. It runs along
    x 130.75–137.85 mm, left of the CAN section, and y 82.70–89.80 mm, below it,
    under U18, U22 and C57.
    On the CAN side of the gap, `GND_ISO` has its own pour on all four layers. On
    the other side, F.Cu, In1.Cu and B.Cu are `GND`. In2.Cu is `5V`, except for a
    `3V3_MCU` island in the lower right: east of x 168 mm, and east of x 162 mm
    above y 105 mm, so that it reaches the logic side of U22. A 0.5 mm split
    separates the two and passes between U13's input and output pins. The top-right corner (H2
    and the J12 shield links) is left out of the `GND_ISO` pour for the PE entry.
    The gap is centred under the isolators and ends flush with their lands, which
    are 7.1 mm apart. The package allows 8 mm; reaching that needs TI's isolation
    land pattern on U18 and U22. Only the zone outlines set the gap: no
    keep-out area or design rule stops a track or via from entering it. No slot
    is drawn.
13. **48 V input stage** (brief OPEN-6) is outside this board: main fuse, reverse
    polarity, brake resistors sized for AC operation. The brief's 48 V bus-voltage
    sensing is not implemented: no 48 V comes onto this board.
14. **eFuse control pins.** The SHDN divider and the FLT series resistor follow
    the TPS2660 datasheet limits but are not from a TI reference circuit. Check
    them against TI's application report "Fault Handling Using TPS2660 eFuse".
15. **CAN_V+ over-voltage.** D12 starts to conduct at 31.1 V, below the 34.4 V
    eFuse cut-off, so it clamps transients only. Set the converter no higher than
    26.4 V.

## Libraries

- **Symbols and footprints:** the `MyParts` library in the `parts/` submodule
  ([jrseti/parts](https://github.com/jrseti/parts)), referenced from the project
  library tables as `${KIPRJMOD}/../../parts/...` (the submodule is at the
  root of the Dish repository).
- **IPC-named footprints:** every part on the board uses a `MyParts` footprint,
  except the mounting holes. The `MyParts` footprints carry IPC-7351B names (see
  the naming section of `parts/README.md`); these were first made in a
  project-local `myparts-ipc.pretty` library, which has since been merged into
  `MyParts` and removed.
  - Standard packages have IPC-7351B names. Most come from the reference project.
    The ones added here are named from datasheet maximum heights:
    `QFP50P1200X1200X160-64N` (STM32), `SON127P615X515X120-9N` (Q1/Q9),
    `SOT95P240X110-3N` (PESD2CANFD27V), `RESC2012X60N`,
    `OSCCC320X250X80-4N` (X1), `SOP127P835X250-4N` (SW2),
    `SOP65P640X120-17N` (TPS26600), `SOIC127P1030X265-16N` (ISO1042, ISO7721) and
    `INDM6060X450N` (L3).
  - `CAPRD1000W55L820T450` (C57, the Y capacitor) is KiCad's
    `C_Disc_D8.0mm_W5.0mm_P10.00mm` under an IPC-7251 style name.
  - `SON127P615X515X120-9N` was made for the BSC098N10NS5 (TDSON-8). Q1/Q9 are in
    Vishay's PowerPAK SO-8, which has the same land pattern and pin order; its
    maximum height is 1.12 mm, not the 1.20 mm in the name.
  - Parts with no IPC-7351 package family (connectors, headers, modules, switches,
    the CAN choke, the battery, the RH-5016 test points) are named manufacturer_part,
    e.g. `Molex_48406-0003`, `HanRun_HR911130A`, `KEFA_KF2EDGR-5.08-2P` (J13),
    `PinHeader_2x12_P2.54mm_Vertical`.
  - D2 uses the reference project's SMC pattern `DIOM7959X262N`
    (2.7 × 3.3 mm pads instead of 3.03 × 3.82 mm).
  - `Samtec_FTSH-107-01-L-DV-K-A` (J10) numbers its pads `01`–`14` to match the
    STDC14 symbol. The old `MyParts` footprint numbered them `1`–`14`, which left
    J10 pins 1–9 without pads; the library now uses the `01`–`14` version.
- **3D models:** set the KiCad path variable `MYPARTS` to `<clone>/parts` and
  `MYPARTS_DATASHEETS` to `<clone>/parts/datasheets`
  (**Preferences → Configure Paths**).

This design added these symbols to `parts/myparts.kicad_sym`, with footprints and
3D models where the library had none. The 48 V parts among them (`LM5116MHX`,
`BSC098N10NS5`, `TMPC1265HP-100MG-D`, `RLP25FEGR015`,
`0402CG331J500NT`, `SS510C`, `SMCJ58A`, `BAV21WS_C2903901`, `BLM31PG121SN1L`) and
`CA-IS3052G` are no longer used by this board:

| Symbol | Part | LCSC |
|---|---|---|
| `ComputeModule5-CM5` | CM5 (the CM4 symbol with CM5 pin names) | – |
| `LM5116MHX` | 100 V buck controller | C13755 |
| `BSC098N10NS5` | 100 V MOSFET | C534398 |
| `TMPC1265HP-100MG-D` | 10 µH inductor | C305223 |
| `RLP25FEGR015` | 15 mΩ sense resistor | C459682 |
| `CL31Y225KCHVPNE` | 2.2 µF 100 V capacitor | C2803390 |
| `EFVH100ADA101M10C0` | 100 µF 100 V electrolytic | C22387799 |
| `0402CG331J500NT` | 330 pF C0G capacitor | C190579 |
| `SS510C` | 100 V Schottky | C123944 |
| `SMCJ58A` | TVS | C151899 |
| `BAV21WS_C2903901` | 250 V switching diode | C2903901 |
| `XC-7_5x20_FuseHolder` | 5×20 mm fuse holder | C3131 |
| `ACT45B-510-2P-TL003` | CAN common-mode choke | C76584 |
| `484060003` | Molex stacked USB 3.0 Type-A connector | C565298 |
| `CA-IS3052G` | Isolated CAN transceiver (the ISO1042 symbol, re-labelled) | C528764 |
| `BLM31PG121SN1L` | 120 Ω 3.5 A ferrite bead | C85841 |
| `SI7137DP-T1-GE3` | 20 V P-channel MOSFET, 2.5 mΩ at 4.5 V, PowerPAK SO-8 | C784367 |
| `SMCJ6.0A` | 6 V TVS, 1.5 kW, SMC | C310065 |
| `TPS26600PWPR` | 60 V eFuse, HTSSOP-16 | C544399 |
| `ISO1042DWR` | Isolated CAN transceiver, SOIC-16 wide | C1848126 |
| `ISO7721DWR` | 2-channel digital isolator, SOIC-16 wide | C524805 |
| `LMR51606XDBVR` | 65 V 0.6 A buck converter, SOT-23-6 | C21260865 |
| `KF2EDGR-5.08-2P` | Pluggable terminal block header, 2-pin, 5.08 mm | C441204 |
| `SMNR6045-330MT` | 33 µH 1.5 A shielded inductor | C135306 |
| `SMBJ28CA` / `SMBJ28A` | 28 V TVS, 600 W, SMB, bidirectional / unidirectional | C151259 / C178227 |
| `SS210` | 100 V 2 A Schottky, SMA | C14996 |
| `AJTF222M2GF0200A082E` | 2.2 nF Y1 safety capacitor, 10 mm pitch | C2836435 |
| `GRM2165C1H472JA01D` | 4.7 nF 50 V C0G capacitor, 0805 | C77063 |
| `TCC0402X7R224K250AT` | 220 nF 25 V capacitor, 0402 | C915854 |
| `CL10B104KC8NNNC` | 100 nF 100 V capacitor, 0603 | C15725 |
| `1206W4F604JT5E` / `1206W4F0000T5E` | 60.4 Ω 0.25 W / 0 Ω resistor, 1206 | C57572 / C17888 |
| `0603WAF2493T5E` / `0603WAF0000T5E` | 249 kΩ / 0 Ω resistor, 0603 | C22918 / C21189 |
| `0402WGF330JTCE`, `0402WGF2402TCE`, `0402WGF3002TCE`, `0402WGF1183TCE` | 33 Ω, 24 kΩ, 30 kΩ, 118 kΩ resistors, 0402 | C25105, C25769, C25776, C25748 |
| `0402WGF220JTCE` | 22 Ω resistor, 0402 (I2C series resistors R45, R46) | C25092 |
| `CL05A475MP5NRNC_ALT` / `CL10A106KP8NNNC_ALT` | 4.7 µF 10 V capacitor, 0402 / 10 µF 10 V capacitor, 0603 (C52, C51) | C23733 / C19702 |

It also renamed the footprint `SW-SMD_DSHP02TSGER` to `SOP127P835X250-4N` in
`parts/myparts.pretty` (used by the `DSHP02TSGER` symbol). Other projects that
share the library still reference the old name.

These changes are committed in `parts/`, except the symbols from `TPS26600PWPR`
down (with their footprints, 3D models and datasheets), which were added on
2026-11-24 and are in the submodule's working tree. Commit and push those in
`parts/` first, then commit the new submodule pointer here.

## Checking the schematic

```sh
cd cm5-servo-dish-controller/kicad
/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli sch erc --severity-all cm5-servo-dish-controller.kicad_sch
```

Expected result: `Found 0 violations`.

## Fabrication

Not started. The reference board is a 4-layer, 150 × 90 mm PCB assembled by JLCPCB
with LCSC part numbers; this board is expected to follow it.

## STM32

`stm32/` is for the STM32G474RET6 firmware and its CubeMX `.ioc` file. Use the pin
table above when creating the `.ioc`.
