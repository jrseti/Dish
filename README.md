# Dish Repository

This repository contains hardware and firmware work for refurbishing a legacy
3-meter satellite dish into a modern, networked robotic system.

The design is split into two PCB projects that work together over CAN:

## Projects

### 1. `controller/` - RCM Dish Controller Board

The main motion-control and compute board for the dish.

- STM32-based two-axis motion controller
- On-board Raspberry Pi Compute Module 4 carrier
- Power, I/O, communications, and safety/control interfaces
- KiCad hardware design plus associated embedded/software assets

See: [controller/README.md](controller/README.md)

### 2. `can_hub/` - CAN Bus Hub

A simple CAN distribution hub that also routes 24 V power to CAN_V+ pins.

See: [can_hub/README.md](can_hub/README.md)

## Repository Layout

- `controller/`: Main controller electronics, docs, and software
- `can_hub/`: CAN power/distribution hub hardware

## Purpose

Together, these boards provide the control and field-bus backbone for the dish:

- `controller/` runs motion control and local host integration
- `can_hub/` provides CAN/power fan-out for connected nodes




