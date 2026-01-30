# Pen Plotter Control System

Control system for an RP2040-based pen plotter with stepper motor and linear actuator.

## Overview

This project implements a two-layer architecture:
- **Firmware (Arduino/C++)**: Low-level motor control and serial command interface
- **Application (Python)**: Interactive matplotlib-based GUI with path planning, kinematics, and live visualization

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
│   ├── control/              # Drawing primitives and shapes
│   ├── path/                 # Path interpolation
│   ├── visualization/        # Interactive matplotlib GUI
│   ├── data/                 # Path data structures
│   └── config.py             # System configuration
├── run.sh                    # GUI launcher script
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

### Interactive GUI (Primary Interface)

Launch the interactive matplotlib-based GUI:

```bash
# Using the launcher script
./run.sh

# Or directly with Python
python -m penplotter
```

**GUI Features:**
- Click on canvas to add path points
- Connect to plotter via serial port (auto-detection available)
- Live actuator arm visualization during execution
- Workspace boundary visualization
- Path validation and statistics
- Undo/Clear path controls
- Home plotter button

**GUI Workflow:**
1. Click "Detect" to auto-detect USB serial ports
2. Click "Connect" to establish connection with plotter
3. Click on canvas to add points to your drawing path
4. Click "Execute" to draw the path on the physical plotter
5. Use "Undo" to remove last point or "Clear Path" to start over
6. Click "Home" to return plotter to home position

### Python API (Programmatic Control)

```python
from penplotter.hardware import Plotter
from penplotter.control import draw_line, draw_rectangle

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
