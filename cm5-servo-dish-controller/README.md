# CM5 Servo Dish Controller

A radio astronomy dish controller: a carrier board for a Raspberry Pi Compute
Module 5 (CM5) with an STM32G474 that drives the dish's servo motors over CANopen.

The board is derived from
[roboclaw-cm4-dc-dish-controller](https://github.com/jrseti/roboclaw-cm4-dc-dish-controller).
The RoboClaw motor controller is replaced by an STM32G474RET6, which is the CANopen
master for external servo drives (such as the DSY-400C) and runs the position and
velocity loop. The board runs from 5 V DC, supplied by an external Mean Well
DDR-60L-5 converter that isolates it from the 48 V battery. The CAN bus is isolated
and has two jacks, one to the drives and one to the nodes on the dish, which it
powers with 24 V from a second external converter. The board uses a CM5 in place
of the CM4, and has two USB 3.0 ports.

**Schematic:** [kicad/cm5-servo-dish-controller.pdf](kicad/cm5-servo-dish-controller.pdf)

**Design description and open items:** [DESIGN.md](DESIGN.md)

## Status

The schematic is a complete first pass and passes KiCad's electrical rules check.
The PCB layout, the STM32 firmware and the CM5 software have not been started.

## Repository layout

This project is one folder of the Dish repository:

```
Dish/
├── parts/                        # git submodule: KiCad symbol, footprint and 3D-model library
└── cm5-servo-dish-controller/    # this project: README.md, DESIGN.md
    └── kicad/                    # KiCad 10 project: schematic and PCB
```

## Cloning

The KiCad project finds its symbols, footprints and 3D models in the `parts/`
submodule at the root of the Dish repository (`${KIPRJMOD}/../../parts`). Clone with:

```sh
git clone --recurse-submodules <repository-url>
```

If you have already cloned the repository, run `git submodule update --init`.

KiCad finds the 3D models and datasheets through two path variables. Set them in
**Preferences → Configure Paths**:

| Variable | Value |
|---|---|
| `MYPARTS` | `<clone>/parts` |
| `MYPARTS_DATASHEETS` | `<clone>/parts/datasheets` |

## Hardware

Open `kicad/cm5-servo-dish-controller.kicad_pro` with KiCad 10.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
