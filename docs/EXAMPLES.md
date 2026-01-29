# Examples

This document covers example usage of the pen plotter system, including test scripts and API examples.

## Test Scripts

### Drawing a Rectangle

The `test_rectangle.py` script demonstrates drawing a rotated rectangle:

```bash
python test_rectangle.py
```

**Default parameters:**
- Center: (0, 175)mm - middle of the drawing board
- Size: 100×100mm (square)
- Rotation: 45 degrees
- Step size: 1.0mm interpolation

**What it does:**
1. Connects to the plotter
2. Homes the plotter
3. Draws a 45-degree rotated square
4. Returns to home position

**Output includes:**
- Corner coordinates in Cartesian and polar
- Expected perimeter and interpolation points
- Workspace validation status

### Drawing a Straight Line

The `test_straight_line.py` script demonstrates the line drawing functionality:

```bash
# Use default coordinates (0,100) → (50,200)
python test_straight_line.py

# Use custom coordinates
python test_straight_line.py 0 100 50 200  # start_x start_y end_x end_y
```

**Features:**
- Command-line parameterization of start/end points
- Workspace boundary validation
- Timing and progress information
- Polar coordinate display

## Python API Examples

### Basic Line Drawing

```python
from penplotter.hardware import Plotter
from penplotter.drawing import draw_line

with Plotter("/dev/tty.usbmodem1101") as plotter:
    plotter.home()

    # Draw a diagonal line
    draw_line(plotter, start=(0, 100), end=(50, 200), step_size=1.0)

    plotter.home()
```

### Rectangle Drawing

```python
from penplotter.hardware import Plotter
from penplotter.drawing import draw_rectangle

with Plotter("/dev/tty.usbmodem1101") as plotter:
    plotter.home()

    # Draw a rotated rectangle matching the assignment example
    draw_rectangle(
        plotter,
        center=(0, 175),    # Center position
        width=100,          # Width in mm
        height=100,         # Height in mm
        rotation=45,        # Rotation angle in degrees
        step_size=1.0       # Interpolation step size
    )

    plotter.home()
```

### Drawing Multiple Shapes

```python
from penplotter.hardware import Plotter
from penplotter.drawing import draw_rectangle

with Plotter("/dev/tty.usbmodem1101") as plotter:
    plotter.home()

    # Draw three rectangles with different parameters
    rectangles = [
        {"center": (0, 100), "width": 60, "height": 60, "rotation": 0},
        {"center": (0, 175), "width": 100, "height": 100, "rotation": 45},
        {"center": (0, 280), "width": 80, "height": 40, "rotation": 30},
    ]

    for rect in rectangles:
        draw_rectangle(plotter, **rect)

    plotter.home()
```

### Workspace Validation

```python
from penplotter.drawing import validate_point

# Validate coordinates before drawing
try:
    validate_point(0, 175)    # Valid - center of workspace
    validate_point(150, 200)  # Raises ValueError - X out of bounds
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

## Coordinate System

**Origin**: (0, 0) at pen position (bottom center of board)
- **X-axis**: -140mm to +140mm (left/right)
- **Y-axis**: 0mm to 350mm (up the board)
- **Rotation**: 0° points UP (+Y direction)
  - Positive angles sweep LEFT (toward -X)
  - Negative angles sweep RIGHT (toward +X)
  - Range: ±45° from vertical

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
