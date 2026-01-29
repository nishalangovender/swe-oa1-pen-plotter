"""
Higher-level shape drawing functions for the pen plotter.

This module provides functions for drawing common shapes like rectangles,
with support for rotation, positioning, and workspace validation.
"""

import math
from typing import Tuple
from .primitives import draw_line
from ..config import BOARD_WIDTH, BOARD_HEIGHT


def validate_point(x: float, y: float) -> bool:
    """
    Validate that a point falls within the plotter's workspace.

    Args:
        x: X coordinate in mm (should be in range [-140, 140])
        y: Y coordinate in mm (should be in range [0, 350])

    Returns:
        True if point is valid, False otherwise

    Raises:
        ValueError: If point is outside workspace boundaries
    """
    x_min = -BOARD_WIDTH / 2
    x_max = BOARD_WIDTH / 2
    y_min = 0
    y_max = BOARD_HEIGHT

    if not (x_min <= x <= x_max):
        raise ValueError(
            f"X coordinate {x}mm is outside workspace bounds "
            f"[{x_min}, {x_max}]mm"
        )

    if not (y_min <= y <= y_max):
        raise ValueError(
            f"Y coordinate {y}mm is outside workspace bounds "
            f"[{y_min}, {y_max}]mm"
        )

    return True


def draw_rectangle(
    plotter,
    center: Tuple[float, float],
    width: float,
    height: float,
    rotation: float = 0.0,
    step_size: float = 1.0
) -> None:
    """
    Draw a rectangle with the pen plotter.

    The rectangle is defined by its center point, dimensions, and rotation angle.
    It is drawn as four connected line segments, starting from the bottom-left
    corner and proceeding counter-clockwise.

    Args:
        plotter: Plotter instance to control the hardware
        center: (x, y) center position of rectangle in mm
        width: Width of rectangle in mm
        height: Height of rectangle in mm
        rotation: Rotation angle in degrees (default: 0, counter-clockwise from horizontal)
        step_size: Interpolation step size in mm (default: 1.0)

    Raises:
        ValueError: If any corner point falls outside the workspace

    Example:
        # Draw a 100x100mm square rotated 45 degrees, centered on the board
        draw_rectangle(plotter, center=(0, 175), width=100, height=100, rotation=45)
    """
    cx, cy = center

    # Calculate corner offsets from center (before rotation)
    half_w = width / 2
    half_h = height / 2

    # Define corners relative to center (counter-clockwise from bottom-left)
    corners_local = [
        (-half_w, -half_h),  # Bottom-left
        (half_w, -half_h),   # Bottom-right
        (half_w, half_h),    # Top-right
        (-half_w, half_h),   # Top-left
    ]

    # Apply rotation if specified
    if rotation != 0:
        rad = math.radians(rotation)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        # Rotate each corner point
        corners_rotated = []
        for x_local, y_local in corners_local:
            x_rot = x_local * cos_r - y_local * sin_r
            y_rot = x_local * sin_r + y_local * cos_r
            corners_rotated.append((x_rot, y_rot))
        corners_local = corners_rotated

    # Translate corners to absolute coordinates
    corners = [(cx + x, cy + y) for x, y in corners_local]

    # Validate all corners are within workspace
    for i, (x, y) in enumerate(corners):
        try:
            validate_point(x, y)
        except ValueError as e:
            raise ValueError(f"Corner {i} ({x:.1f}, {y:.1f}mm): {e}")

    # Draw the four sides of the rectangle
    for i in range(4):
        start = corners[i]
        end = corners[(i + 1) % 4]  # Wrap around to first corner
        draw_line(plotter, start, end, step_size)

    print(f"Rectangle drawn successfully:")
    print(f"  Center: ({cx}, {cy})mm")
    print(f"  Size: {width}x{height}mm")
    print(f"  Rotation: {rotation}°")
    print(f"  Corners: {[(f'{x:.1f}', f'{y:.1f}') for x, y in corners]}")
