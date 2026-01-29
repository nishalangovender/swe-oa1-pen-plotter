# Example Firmware Setup

This directory contains the example firmware from the assignment to test the pen plotter hardware.

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
