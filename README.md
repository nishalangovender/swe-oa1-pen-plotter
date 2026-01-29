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
│   ├── drawing/              # Drawing primitives and shapes
│   ├── path/                 # Path interpolation
│   └── config.py             # System configuration
├── test_straight_line.py     # Straight line test script
├── test_rectangle.py         # Rectangle drawing test script
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

### Test Scripts

```bash
# Draw a rectangle (100x100mm square rotated 45 degrees)
python test_rectangle.py

# Draw a straight line with default coordinates
python test_straight_line.py

# Draw a straight line with custom coordinates (x1 y1 x2 y2)
python test_straight_line.py 0 100 50 200
```

### Python API

```python
from penplotter.hardware import Plotter
from penplotter.drawing import draw_line, draw_rectangle

# Connect to the plotter
with Plotter("/dev/tty.usbmodem1101") as plotter:
    # Home the plotter
    plotter.home()

    # Draw a straight line from (0, 100) to (50, 200)
    draw_line(plotter, start=(0, 100), end=(50, 200), step_size=1.0)

    # Draw a rectangle
    draw_rectangle(plotter, center=(0, 175), width=100, height=100, rotation=45)

    # Return to home
    plotter.home()
```

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and layer descriptions
- [FIRMWARE.md](docs/FIRMWARE.md) - Firmware upload and serial protocol reference
- [CALIBRATION.md](docs/CALIBRATION.md) - Hardware calibration guide
- [EXAMPLES.md](docs/EXAMPLES.md) - Example firmware setup instructions
- [ASSIGNMENT.md](docs/ASSIGNMENT.md) - Assignment description
