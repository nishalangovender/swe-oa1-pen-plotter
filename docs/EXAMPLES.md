# Examples

This document covers example usage of the pen plotter system, including the interactive GUI and programmatic API examples.

## Interactive GUI (Primary Interface)

### Launching the GUI

```bash
# Using the launcher script
./run.sh

# Or directly with Python
python -m penplotter
```

### GUI Workflow

1. **Connect to Plotter:**
   - Click "Detect" to auto-detect available USB serial ports
   - The first USB port will be automatically selected
   - Alternatively, manually enter the port path (e.g., `/dev/tty.usbmodem1101`)
   - Click "Connect" to establish connection
   - Connection status indicator will turn green when connected

2. **Create Drawing Path:**
   - Click anywhere on the canvas to add path points
   - Points are displayed with orange markers and connecting lines
   - The workspace boundary is shown with a dashed cream-colored rectangle
   - Invalid points (outside workspace) will show an error message

3. **Edit Path:**
   - Click "Undo Point" to remove the last added point
   - Click "Clear Path" to remove all points and start over

4. **Execute Drawing:**
   - Click "Execute" to start drawing the path on the physical plotter
   - The actuator arm visualization will update in real-time as the plotter moves
   - Path statistics (length, segments, bounds) are printed to console
   - Drawing status is shown in the status panel

5. **Home Plotter:**
   - Click "Home" to return the plotter to its home position
   - The actuator arm visualization will update to show the home position

### GUI Features

- **Live Visualization:** Real-time actuator arm position updates during drawing
- **Workspace Boundaries:** Visual representation of valid drawing area
- **Connection Status:** Color-coded indicator (gray=disconnected, green=connected, red=error)
- **Path Validation:** Immediate feedback on point validity
- **Path Statistics:** Total length, segment count, and bounding box information
- **Auto-Port Detection:** Automatic detection of USB serial devices

## Python API Examples

### Basic Line Drawing

```python
from penplotter.hardware import Plotter
from penplotter.control.primitives import draw_line

with Plotter("/dev/tty.usbmodem1101") as plotter:
    plotter.home()

    # Draw a diagonal line
    draw_line(plotter, start=(0, 200), end=(50, 300), step_size=1.0)

    plotter.home()
```

### Rectangle Drawing

```python
from penplotter.hardware import Plotter
from penplotter.control.shapes import draw_rectangle

with Plotter("/dev/tty.usbmodem1101") as plotter:
    plotter.home()

    # Draw a rotated rectangle
    draw_rectangle(
        plotter,
        center=(0, 300),    # Center position (origin-relative)
        width=100,          # Width in mm
        height=100,         # Height in mm
        rotation=45,        # Rotation angle in degrees
        step_size=1.0       # Interpolation step size
    )

    plotter.home()
```

### Path Execution with Progress Tracking

```python
from penplotter.hardware import Plotter
from penplotter.control.executor import PathExecutor

# Define a custom path
path_points = [
    (0, 200),
    (50, 250),
    (0, 300),
    (-50, 250),
    (0, 200)  # Close the path
]

with Plotter("/dev/tty.usbmodem1101") as plotter:
    plotter.home()

    # Create executor and set path
    executor = PathExecutor(plotter)
    executor.set_path(path_points)

    # Optional: Set progress callback
    def on_progress(current_pos, segment_progress):
        print(f"Drawing at position: {current_pos}")

    executor.set_progress_callback(on_progress)

    # Execute the path
    executor.execute()

    # Print summary
    executor.print_summary()

    plotter.home()
```

### Workspace Validation

```python
from penplotter.control.shapes import validate_point

# Validate coordinates before drawing
try:
    validate_point(0, 300)    # Valid - center of workspace
    validate_point(150, 300)  # Raises ValueError - X out of bounds
except ValueError as e:
    print(f"Invalid coordinates: {e}")
```

### Low-Level Hardware Control

```python
from penplotter.hardware import Plotter
from penplotter.kinematics import cartesian_to_hardware

with Plotter("/dev/tty.usbmodem1101") as plotter:
    plotter.home()

    # Convert Cartesian coordinates to hardware units
    x, y = 50, 200  # mm
    microsteps, adc_value = cartesian_to_hardware(x, y)

    # Send low-level commands
    plotter.rotate(microsteps)
    plotter.linear(adc_value)

    # Get current position
    current_steps, current_adc = plotter.get_pos()
    print(f"Position: {current_steps} steps, {current_adc} ADC")

    plotter.home()
```

## Direct Hardware Control CLI

For low-level testing and debugging, use the `plotter_control.py` CLI tool:

```bash
python plotter_control.py /dev/tty.usbmodem1101
```

**Available commands:**
- `home` - Move to home position
- `rotate <degrees>` - Rotate to angle
- `linear <mm>` - Extend to distance from rotation axis
- `raw_rotate <steps>` - Rotate to absolute microsteps (direct hardware control)
- `raw_linear <adc>` - Extend to ADC value 0-834 (direct hardware control)
- `pos` - Get current position (angle and radius)
- `stop` - Emergency stop
- `debug` - Toggle debug mode
- `help` - Show help
- `quit` - Exit

**Use cases:**
- Manual hardware testing
- Debugging serial communication
- Position verification
- Calibration assistance

## Coordinate System

**Origin**: (0, 0) at rotation axis
- **X-axis**: -140mm to +140mm (left/right)
- **Y-axis**: 160mm to 510mm from rotation axis
  - Pen home position: y=160mm
  - Drawing area: 160mm to 510mm (350mm height)
- **Rotation**: 0° points UP (+Y direction)
  - Positive angles sweep counter-clockwise
  - Negative angles sweep clockwise

## Firmware Setup

This section contains the example firmware from the assignment to test the pen plotter hardware.

## Arduino IDE Setup

### 1. Install Arduino IDE
Download and install Arduino IDE 2.x from [arduino.cc](https://www.arduino.cc/en/software)

### 2. Install RP2040 Board Support
1. Open Arduino IDE
2. Go to **File > Preferences**
3. Add this URL to "Additional Board Manager URLs":
   ```
   https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
   ```
4. Go to **Tools > Board > Boards Manager**
5. Search for "pico" and install **"Raspberry Pi Pico/RP2040"** by Earle F. Philhower, III

### 3. Install Required Libraries
Go to **Tools > Manage Libraries** and install:
- **TMCStepper** by teemuatlut
- **ADS1X15** (search for ADS1X15 and select the appropriate library)
- **Adafruit PWM Servo Driver Library** by Adafruit

### 4. Board Configuration
1. Connect RP2040 Stamp via USB-C
2. Select **Tools > Board > Raspberry Pi Pico/RP2040 > Solder Party RP2040 Stamp**
3. Select **Tools > Port** and choose your device (typically `/dev/ttyACM0` on Linux/Mac, `COM#` on Windows)

### 5. Upload Example Firmware
1. Open `example_firmware.ino` in Arduino IDE
2. Click **Upload** button (right arrow icon)
3. Wait for compilation and upload to complete

## Testing the Example

### Serial Monitor
1. Open **Tools > Serial Monitor**
2. Set baud rate to **9600**
3. You should see:
   - "Online"
   - "Wire 1 Begin"
   - "I2C Done"
   - Position values continuously printing

### What the Example Does
The example firmware demonstrates basic hardware control:
- Reads potentiometer position from linear actuator
- Retracts the actuator (1 second)
- Extends the actuator (1 second)
- Stops the actuator (1 second)
- Moves stepper motor 10 steps forward
- Repeats

**Note**: This is just a demo loop. The actual firmware (step 2 of assignment) will implement a command protocol for controlled movements.

## Hardware Notes

**Motor Parameters:**
- Stepper: 200 steps/rev, 256 microsteps, 20:1 gearbox = 1,024,000 microsteps/rev
- Full rotation: `stepperDriver.XTARGET(stepperDriver.XACTUAL() + (256 * 200 * 20))`
- Linear actuator: PWM control, potentiometer feedback

**Important:**
- Turn on external power supply for motors to move
- If power cycled, need to re-upload firmware to reinitialize motor driver
- Press BOOTSEL button while connecting USB if board doesn't respond

## Troubleshooting

**Board not detected**:
- Try different USB cable (must support data)
- Hold BOOTSEL button while connecting for bootloader mode
- Check device appears: `ls /dev/ttyACM*` (Mac/Linux) or Device Manager (Windows)

**Upload fails**:
- Verify "Solder Party RP2040 Stamp" board selected
- Try resetting board
- Check USB cable supports data transfer

**"Driver not connected" error**:
- Verify power supply is on
- Check SPI connections
- Try re-uploading firmware

**Motor not moving**:
- Ensure external power supply is connected and turned on
- Firmware must complete setup successfully
- Check Serial Monitor for error messages
