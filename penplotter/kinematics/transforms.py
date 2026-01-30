"""Coordinate transformation functions for pen plotter kinematics."""

import math
from typing import Tuple

from penplotter import config


def cartesian_to_polar(x: float, y: float) -> Tuple[float, float]:
    """Convert Cartesian coordinates to polar coordinates.

    Coordinate system convention:
    - Origin (0, 0) is at the stepper motor rotation point
    - Pen tip is at (0, 160mm) when at home position (160mm offset from rotation point)
    - Board extends: X from -140 to +140mm, Y from 160mm to 470mm (from rotation point)
    - 0° rotation points UP the board (+Y direction)
    - Positive angles sweep RIGHT (toward +X)
    - Negative angles sweep LEFT (toward -X)
    - Rotation range: ±45° from vertical

    Args:
        x: X coordinate in mm (left/right from rotation point)
        y: Y coordinate in mm (up from rotation point)

    Returns:
        Tuple of (angle_degrees, radius_mm)
        - angle_degrees: 0° = up, positive = left, negative = right
        - radius_mm: distance from rotation point (linear actuator extension)
    """
    # Calculate radius from rotation point to target position
    radius_mm = math.sqrt(x**2 + y**2)

    # Rotate coordinate system so 0° points up (+Y) instead of right (+X)
    # Positive x should give positive angle (rotate right), negative x gives negative angle (rotate left)
    angle_rad = math.atan2(x, y)
    angle_deg = math.degrees(angle_rad)

    return (angle_deg, radius_mm)


def polar_to_hardware(angle_deg: float, radius_mm: float) -> Tuple[int, int]:
    """Convert polar coordinates to hardware units.

    Args:
        angle_deg: Angle in degrees
        radius_mm: Radius in millimeters (total distance from origin)

    Returns:
        Tuple of (stepper_microsteps, linear_adc_value)
    """
    # Convert angle to microsteps
    microsteps = int(angle_deg * config.MICROSTEPS_PER_DEGREE)

    # Convert radius to linear actuator extension
    # The actuator extends beyond the base arm length (PEN_OFFSET_MM)
    extension_mm = radius_mm - config.PEN_OFFSET_MM
    adc_value = int(extension_mm * config.ADC_PER_MM + config.ADC_MIN)

    # Clamp ADC value to valid range
    adc_value = max(config.ADC_MIN, min(config.ADC_MAX, adc_value))

    return (microsteps, adc_value)


def hardware_to_polar(microsteps: int, adc_value: int) -> Tuple[float, float]:
    """Convert hardware units to polar coordinates.

    Args:
        microsteps: Stepper position in microsteps
        adc_value: Linear actuator ADC value

    Returns:
        Tuple of (angle_degrees, radius_mm) where radius_mm is total distance from origin
    """
    # Convert microsteps to angle
    angle_deg = microsteps / config.MICROSTEPS_PER_DEGREE

    # Convert ADC to extension, then to total radius
    extension_mm = (adc_value - config.ADC_MIN) / config.ADC_PER_MM
    radius_mm = extension_mm + config.PEN_OFFSET_MM

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
