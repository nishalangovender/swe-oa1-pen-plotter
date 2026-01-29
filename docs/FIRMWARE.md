# Pen Plotter Firmware

Command-based serial protocol firmware for RP2040-based pen plotter control.

## Upload Instructions

1. Open `pen_plotter/pen_plotter.ino` in Arduino IDE
2. Select Board: **Solder Party RP2040 Stamp**
3. Select Port: Your RP2040 device
4. Click Upload
5. Open Serial Monitor (9600 baud)

## Calibration Process (Do This First!)

Before using the plotter, you must calibrate the linear actuator ADC range:

1. Upload the firmware
2. Open Serial Monitor (9600 baud)
3. Run calibration sequence:
   ```
   # Start retracting
   RETRACT_RAW

   # Watch GET_POS until ADC stops changing (fully retracted)
   GET_POS
   GET_POS
   ...

   # Stop when fully retracted
   STOP_LINEAR

   # Record this ADC value as ADC_MIN
   GET_POS

   # Now extend
   EXTEND_RAW

   # Watch GET_POS until ADC stops changing (fully extended)
   GET_POS
   GET_POS
   ...

   # Stop when fully extended
   STOP_LINEAR

   # Record this ADC value as ADC_MAX
   GET_POS
   ```

4. Update firmware constants (lines 55-57):
   ```cpp
   constexpr int ADC_MIN = 127;      // Replace with your min value
   constexpr int ADC_MAX = 30000;    // Replace with your max value
   constexpr int ADC_HOME = ADC_MIN; // Home = fully retracted
   ```

5. Re-upload firmware with calibrated values

## Serial Protocol

### Command Format
```
COMMAND [arg1] [arg2]\n
```

### Commands

| Command | Parameters | Description | Response |
|---------|-----------|-------------|----------|
| `HOME` | None | Move to home/zero position (stepper + linear) | `OK` or `ERROR: HOME linear timeout` |
| `ROTATE <steps>` | steps (int) | Rotate to absolute position in microsteps | `OK` |
| `LINEAR <target>` | target (int) | Move to target ADC value with feedback | `OK` or `ERROR` |
| `EXTEND_RAW` | None | Extend linear actuator (for calibration) | `OK` |
| `RETRACT_RAW` | None | Retract linear actuator (for calibration) | `OK` |
| `DEBUG_ADC` | None | Read all 4 ADC channels (debugging) | Channel readings |
| `STOP_LINEAR` | None | Stop linear actuator | `OK` |
| `STOP` | None | Emergency stop all motors | `OK` |
| `GET_POS` | None | Get current position | `OK <steps> <adc_value>` |
| `STATUS` | None | Print detailed system status | Status info |

### Response Format
- Success: `OK [data]`
- Error: `ERROR: <message>`

## Testing via Serial Monitor

After uploading, test the firmware with these commands:

```
STATUS
HOME
GET_POS
ROTATE 51200
GET_POS
LINEAR 5000
GET_POS
STOP
```

**Expected behavior:**
- `STATUS` shows system state
- `HOME` returns to zero position
- `ROTATE 51200` rotates ~18 degrees (51200 / 1024000 * 360)
- `LINEAR` moves actuator using position feedback until target ADC value reached
- `GET_POS` returns current stepper position and ADC reading

## Implementation Details

### Stepper Motor Control
- Uses TMC5160 with SPI communication
- Position-based commands (XTARGET)
- Waits for `position_reached()` before responding `OK`
- Full rotation = 1,024,000 microsteps (200 steps × 256 microsteps × 20:1 gearbox)

### Linear Actuator Control
- Position feedback via ADS1015 ADC reading potentiometer
- Closed-loop control to reach target ADC value
- Tolerance: ±50 ADC counts
- Timeout: 5 seconds
- Uses PWM driver (PCA9685) for motor control

### State Management
- Tracks home position
- Homed flag set after HOME command
- Current positions readable via GET_POS

## Hardware Connections

**Stepper (SPI):**
- CS: GPIO 21
- MOSI: GPIO 19
- MISO: GPIO 20
- SCK: GPIO 22

**I2C Devices:**
- SDA: GPIO 2 (Wire1)
- SCL: GPIO 3 (Wire1)
- ADS1015: 0x48
- PCA9685: Default address

**PWM Channels:**
- Linear IN1: Channel 1
- Linear IN2: Channel 0

## Troubleshooting

**"Driver not connected" error:**
- Ensure external power supply is ON
- Check stepper driver SPI connections
- Try re-uploading firmware

**Linear actuator timeout:**
- Check ADC is reading valid values (use GET_POS)
- Verify actuator can physically reach target position
- Check power supply to actuator
- Adjust LINEAR_TOLERANCE if needed (currently 50)

**Stepper not moving:**
- Verify power supply connected
- Check `position_reached()` isn't stuck (add debug output)
- Confirm TMC5160 driver enabled (STATUS command)

## Next Steps

With firmware working:
1. Test all commands via Serial Monitor
2. Implement Python serial communication layer
3. Calibrate ADC min/max values
4. Test coordinate transformations
5. Draw first rectangle
