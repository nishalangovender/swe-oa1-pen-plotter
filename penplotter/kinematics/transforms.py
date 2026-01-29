"""Coordinate transformation functions for pen plotter kinematics."""

import math
from typing import Tuple

from penplotter import config


def cartesian_to_polar(x: float, y: float) -> Tuple[float, float]:
    """Convert Cartesian coordinates to polar coordinates.

    Coordinate system convention:
    - Pen is at origin (0, 0) at bottom center of board
    - Board extends: X from -140 to +140mm, Y from 0 to 350mm
    - 0° rotation points UP the board (+Y direction)
    - Positive angles sweep LEFT (toward -X)
    - Negative angles sweep RIGHT (toward +X)
    - Rotation range: ±45° from vertical

    Args:
        x: X coordinate in mm (left/right from pen position)
        y: Y coordinate in mm (up the board from pen position)

    Returns:
        Tuple of (angle_degrees, radius_mm)
        - angle_degrees: 0° = up, positive = left, negative = right
        - radius_mm: distance from origin
    """
    radius_mm = math.sqrt(x**2 + y**2)
    # Rotate coordinate system so 0° points up (+Y) instead of right (+X)
    angle_rad = math.atan2(-x, y)
    angle_deg = math.degrees(angle_rad)

    return (angle_deg, radius_mm)


def polar_to_hardware(angle_deg: float, radius_mm: float) -> Tuple[int, int]:
    """Convert polar coordinates to hardware units.

    Args:
        angle_deg: Angle in degrees
        radius_mm: Radius in millimeters

    Returns:
        Tuple of (stepper_microsteps, linear_adc_value)
    """
    # Convert angle to microsteps
    microsteps = int(angle_deg * config.MICROSTEPS_PER_DEGREE)

    # Convert radius to ADC value
    adc_value = int(radius_mm * config.ADC_PER_MM + config.ADC_MIN)

    # Clamp ADC value to valid range
    adc_value = max(config.ADC_MIN, min(config.ADC_MAX, adc_value))

    return (microsteps, adc_value)


def hardware_to_polar(microsteps: int, adc_value: int) -> Tuple[float, float]:
    """Convert hardware units to polar coordinates.

    Args:
        microsteps: Stepper position in microsteps
        adc_value: Linear actuator ADC value

    Returns:
        Tuple of (angle_degrees, radius_mm)
    """
    # Convert microsteps to angle
    angle_deg = microsteps / config.MICROSTEPS_PER_DEGREE

    # Convert ADC to radius
    radius_mm = (adc_value - config.ADC_MIN) / config.ADC_PER_MM

    return (angle_deg, radius_mm)


def cartesian_to_hardware(x: float, y: float) -> Tuple[int, int]:
    """Convert Cartesian coordinates directly to hardware units.

    Convenience function that combines cartesian_to_polar and polar_to_hardware.

    Args:
        x: X coordinate in mm
        y: Y coordinate in mm

    Returns:
        Tuple of (stepper_microsteps, linear_adc_value)
    """
    angle_deg, radius_mm = cartesian_to_polar(x, y)
    return polar_to_hardware(angle_deg, radius_mm)
