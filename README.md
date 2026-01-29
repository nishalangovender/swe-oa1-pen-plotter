# Pen Plotter Control System

Control system for an RP2040-based pen plotter with stepper motor and linear actuator.

## Overview

This project implements a two-layer architecture:
- **Firmware (Arduino/C++)**: Low-level motor control and serial command interface
- **Application (Python)**: High-level path planning, kinematics, and shape generation

## Hardware

- **Microcontroller**: RP2040 (Solder Party RP2040 Stamp)
- **Stepper Motor**: 200 steps, 256 microsteps/step, 20:1 gearbox
- **Linear Actuator**: Potentiometer feedback
- **Motor Driver**: TMC5160 (SPI control)

## Project Structure

```
swe-oa1-pen-plotter/
├── firmware/pen_plotter/     # Arduino firmware
├── penplotter/               # Python package
│   ├── hardware/             # Serial communication
│   ├── kinematics/           # Coordinate transforms
│   ├── shapes/               # Shape generation
│   └── ui/                   # CLI interface
├── examples/                 # Example shape configs
├── docs/                     # Documentation
└── tests/                    # Unit tests
```

## Installation

```bash
# Set up Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Upload firmware using Arduino IDE
# Open firmware/pen_plotter/pen_plotter.ino and upload to RP2040
```

## Usage

```bash
# Draw a rectangle
python -m penplotter draw-rectangle --size 50 --rotation 45

# Draw from config file
python -m penplotter draw-config examples/hexagon.yaml

# Calibrate workspace
python -m penplotter calibrate
```

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [USAGE.md](docs/USAGE.md) - Usage guide
- [ASSIGNMENT.md](docs/ASSIGNMENT.md) - Assignment description
