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
│   ├── control/              # Drawing primitives (lines, curves, shapes)
│   ├── path/                 # Path interpolation and Bezier curve generation
│   ├── visualization/        # Interactive matplotlib GUI with dual modes
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
- **Dual Drawing Modes**: Toggle between Line and Curve modes
- Click on canvas to add path points or Bezier curve control points
- **Mixed Paths**: Combine straight lines and smooth curves in a single drawing
- Connect to plotter via serial port (auto-detection available)
- Live actuator arm visualization during execution
- **Curve Visualization**: See Bezier handles and curve preview as you draw
- Workspace boundary visualization
- Path validation and statistics
- Undo/Clear path controls
- Home plotter button

**GUI Workflow:**
1. Click "Detect" to auto-detect USB serial ports
2. Click "Connect" to establish connection with plotter
3. Select drawing mode using "Line" or "Curve" buttons:
   - **Line Mode**: Click points to draw connected straight lines
   - **Curve Mode**: Click 4 points (start → control1 → control2 → end) to draw smooth Bezier curves
4. Switch modes anytime to create mixed paths (lines + curves)
5. Click "Execute" to draw the complete path on the physical plotter
6. Use "Undo" to step back or "Clear Path" to start over
7. Click "Home" to return plotter to home position

### Python API (Programmatic Control)

```python
from penplotter.hardware import Plotter
from penplotter.control import draw_line, draw_rectangle, draw_curve

# Connect to the plotter
with Plotter("/dev/tty.usbmodem1101") as plotter:
    # Home the plotter
    plotter.home()

    # Draw a straight line from (0, 100) to (50, 200)
    draw_line(plotter, start=(0, 100), end=(50, 200), step_size=1.0)

    # Draw a Bezier curve with control points
    draw_curve(
        plotter,
        start=(50, 200),
        end=(100, 200),
        control_points=[(60, 250), (90, 150)],
        step_size=0.5
    )

    # Draw a rectangle
    draw_rectangle(plotter, center=(0, 175), width=100, height=100, rotation=45)

    # Return to home
    plotter.home()
```

**Drawing Functions:**
- `draw_line(plotter, start, end, step_size)` - Draw a straight line
- `draw_curve(plotter, start, end, control_points, step_size)` - Draw a cubic Bezier curve
- `draw_rectangle(plotter, center, width, height, rotation)` - Draw a rectangle
- `draw_smooth_path(plotter, points, tension, step_size)` - Draw smooth curves through waypoints

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design and layer descriptions
- [FIRMWARE.md](docs/FIRMWARE.md) - Firmware upload and serial protocol reference
- [CALIBRATION.md](docs/CALIBRATION.md) - Hardware calibration guide
- [EXAMPLES.md](docs/EXAMPLES.md) - Example firmware setup instructions
- [ASSIGNMENT.md](docs/ASSIGNMENT.md) - Assignment description
