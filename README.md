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

### Firmware Setup
See [FIRMWARE.md](docs/FIRMWARE.md) for complete Arduino IDE setup and firmware upload instructions.

### Python Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
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

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and layer descriptions
- [FIRMWARE.md](docs/FIRMWARE.md) - Firmware upload and serial protocol reference
- [CALIBRATION.md](docs/CALIBRATION.md) - Hardware calibration guide
- [EXAMPLES.md](docs/EXAMPLES.md) - Example firmware setup instructions
- [ASSIGNMENT.md](docs/ASSIGNMENT.md) - Assignment description
