# Calibration Guide

## Overview

The pen plotter requires calibration to map the linear actuator's physical travel to ADC (Analog-to-Digital Converter) values from the potentiometer feedback.

## Current Calibration

This hardware has been calibrated with the following values:

- **Linear actuator travel**: 300mm
- **ADC range**: 0 (fully retracted) to 834 (fully extended)
- **ADC gain**: ±6.144V
- **Position tolerance**: ±10 ADC counts (~3.6mm accuracy)
- **Control timeout**: 20 seconds

## When to Recalibrate

Recalibration is needed if:
- Using different linear actuator hardware
- Mechanical changes affect travel range
- ADC readings seem inaccurate
- Testing on new hardware setup

## Calibration Procedure

### 1. Upload Base Firmware

Upload the firmware with default or estimated calibration values.

### 2. Run Calibration Sequence

Open Serial Monitor (9600 baud) and run:

```
# Start retracting to find minimum position
RETRACT_RAW

# Monitor position (second number is ADC value)
GET_POS
GET_POS
GET_POS
...

# When ADC stops changing (fully retracted), stop
STOP_LINEAR

# Record this as ADC_MIN
GET_POS

# Now extend to find maximum position
EXTEND_RAW

# Monitor position
GET_POS
GET_POS
GET_POS
...

# When ADC stops changing (fully extended), stop
STOP_LINEAR

# Record this as ADC_MAX
GET_POS
```

**Alternative:** Use `DEBUG_ADC` to see all 4 ADC channels and verify which channel has the widest range.

### 3. Update Firmware Constants

Edit `firmware/pen_plotter/pen_plotter.ino` (lines 55-57):

```cpp
// Calibration constants - CALIBRATED VALUES
constexpr int ADC_MIN = 0;        // Replace with your recorded min
constexpr int ADC_MAX = 834;      // Replace with your recorded max
constexpr int ADC_HOME = ADC_MIN; // Home position = fully retracted
```

### 4. Adjust Control Parameters (if needed)

If the actuator is very fast or slow, adjust timeout (line 71):

```cpp
constexpr unsigned long LINEAR_TIMEOUT = 20000; // Adjust as needed
```

For tighter or looser position control, adjust tolerance (line 70):

```cpp
constexpr int LINEAR_TOLERANCE = 10; // ±10 ADC counts
```

### 5. Re-upload and Test

1. Upload the updated firmware
2. Test with `HOME` command - should move to fully retracted position
3. Test with `LINEAR <middle_value>` - should move to mid-range
4. Test with `LINEAR <ADC_MAX>` - should move to fully extended
5. Verify positions with `GET_POS`

## Troubleshooting

### ADC range is very small (~200 counts for 300mm travel)

**Problem**: ADC gain is incorrect, compressing the voltage range.

**Solution**: The firmware sets `ADS.setGain(0)` for ±6.144V range. This was the fix for our hardware. If your range is still too small, the potentiometer might have limited voltage swing.

### Actuator times out before reaching target

**Problem**: Actuator is slower than expected, or timeout is too short.

**Solution**: Increase `LINEAR_TIMEOUT` from 20000ms to a higher value (e.g., 30000ms for 30 seconds).

### Position is inaccurate (stops far from target)

**Problem**: `LINEAR_TOLERANCE` is too large.

**Solution**: Reduce tolerance from 10 to 5 or lower. Be careful - too tight and it may oscillate.

### Wrong direction (extends when should retract)

**Problem**: Control direction is inverted.

**Solution**: Swap `in1Pin` and `in2Pin` assignments in the firmware, or reverse the motor wiring.

## Verification

After calibration, verify the system works correctly:

```
HOME          # Should move to ADC_MIN (fully retracted)
GET_POS       # Should show: OK 0 <value_near_ADC_MIN>

LINEAR 417    # Should move to middle (~150mm if 300mm total)
GET_POS       # Should show: OK 0 <value_near_middle>

LINEAR 834    # Should move to fully extended (if ADC_MAX=834)
GET_POS       # Should show: OK 0 <value_near_834>
```

All movements should complete within the timeout period and reach positions within ±10 ADC counts of the target.
