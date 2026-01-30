"""
Higher-level shape drawing functions for the pen plotter.

This module provides functions for drawing common shapes like rectangles,
with support for rotation, positioning, and workspace validation.
"""

import math
from typing import Tuple
from .primitives import draw_line
from .curves import draw_curve
from penplotter.config import BOARD_WIDTH, BOARD_HEIGHT, PEN_OFFSET_MM


def validate_point(x: float, y: float) -> bool:
    """
    Validate that a point falls within the plotter's workspace.

    Coordinate system: Origin (0,0) is at rotation point
    Pen is at (0, 160mm) when at home position
    Board extends from pen position upward

    Args:
        x: X coordinate in mm (should be in range [-140, 140] from rotation point)
        y: Y coordinate in mm (should be in range [160, 510] from rotation point)

    Returns:
        True if point is valid, False otherwise

    Raises:
        ValueError: If point is outside workspace boundaries
    """
    x_min = -BOARD_WIDTH / 2
    x_max = BOARD_WIDTH / 2
    y_min = PEN_OFFSET_MM  # Board starts at pen position (160mm from rotation point)
    y_max = PEN_OFFSET_MM + BOARD_HEIGHT  # Board extends 350mm from pen position

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
    corners: list,
    step_size: float = 1.0,
    progress_callback=None
) -> None:
    """
    Draw a rectangle with the pen plotter using four corner points.

    The rectangle is defined by 4 corner points in order. This allows
    for rectangles at any angle/rotation.

    Args:
        plotter: Plotter instance to control the hardware
        corners: List of 4 (x, y) corner positions in mm, in order
        step_size: Interpolation step size in mm (default: 1.0)
        progress_callback: Optional callback function for live updates

    Raises:
        ValueError: If any corner point falls outside the workspace

    Example:
        # Draw a rotated rectangle
        corners = [(0, 200), (50, 220), (40, 270), (-10, 250)]
        draw_rectangle(plotter, corners)
    """
    if len(corners) != 4:
        raise ValueError(f"Rectangle requires exactly 4 corners, got {len(corners)}")

    # Validate all corners are within workspace
    for i, (x, y) in enumerate(corners):
        try:
            validate_point(x, y)
        except ValueError as e:
            raise ValueError(f"Corner {i} ({x:.1f}, {y:.1f}mm): {e}")

    print(f"Drawing rectangle:")
    print(f"  Corners: {[(f'{x:.1f}', f'{y:.1f}') for x, y in corners]}")

    # Draw the four sides of the rectangle
    for i in range(4):
        start = corners[i]
        end = corners[(i + 1) % 4]  # Wrap around to first corner
        draw_line(plotter, start, end, step_size, progress_callback)

    print(f"Rectangle drawn successfully")


def draw_circle(
    plotter,
    center_x: float,
    center_y: float,
    radius: float,
    step_size: float = 0.5,
    progress_callback=None
) -> None:
    """
    Draw a circle with the pen plotter using Bezier curve approximation.

    The circle is drawn using 4 cubic Bezier curves (one per quadrant).
    This provides a smooth, mathematically accurate circle using the existing
    curve infrastructure.

    Args:
        plotter: Plotter instance to control the hardware
        center_x: X coordinate of circle center in mm
        center_y: Y coordinate of circle center in mm
        radius: Radius of circle in mm
        step_size: Interpolation step size in mm (default: 0.5)
        progress_callback: Optional callback function for live updates

    Raises:
        ValueError: If any point on the circle falls outside the workspace

    Example:
        # Draw a 50mm radius circle centered on the board
        draw_circle(plotter, center_x=0, center_y=335, radius=50)
    """
    # Magic constant for circular Bezier approximation
    # This is 4/3 * (sqrt(2) - 1), the optimal value for approximating
    # a circle with cubic Bezier curves
    k = 0.5522847498
    control_offset = radius * k

    # Calculate the 4 cardinal points on the circle
    top = (center_x, center_y + radius)
    right = (center_x + radius, center_y)
    bottom = (center_x, center_y - radius)
    left = (center_x - radius, center_y)

    # Validate all cardinal points are within workspace
    cardinal_points = [top, right, bottom, left]
    point_names = ["top", "right", "bottom", "left"]
    for name, (x, y) in zip(point_names, cardinal_points):
        try:
            validate_point(x, y)
        except ValueError as e:
            raise ValueError(f"Circle {name} point ({x:.1f}, {y:.1f}mm): {e}")

    print(f"Drawing circle:")
    print(f"  Center: ({center_x}, {center_y})mm")
    print(f"  Radius: {radius}mm")

    # Draw circle using 4 Bezier curves (one per quadrant)
    # Each curve connects two cardinal points with appropriate control points

    # Top-right quadrant (right → top)
    draw_curve(
        plotter,
        right,
        top,
        [
            (center_x + radius, center_y + control_offset),
            (center_x + control_offset, center_y + radius)
        ],
        step_size,
        progress_callback
    )

    # Top-left quadrant (top → left)
    draw_curve(
        plotter,
        top,
        left,
        [
            (center_x - control_offset, center_y + radius),
            (center_x - radius, center_y + control_offset)
        ],
        step_size,
        progress_callback
    )

    # Bottom-left quadrant (left → bottom)
    draw_curve(
        plotter,
        left,
        bottom,
        [
            (center_x - radius, center_y - control_offset),
            (center_x - control_offset, center_y - radius)
        ],
        step_size,
        progress_callback
    )

    # Bottom-right quadrant (bottom → right)
    draw_curve(
        plotter,
        bottom,
        right,
        [
            (center_x + control_offset, center_y - radius),
            (center_x + radius, center_y - control_offset)
        ],
        step_size,
        progress_callback
    )

    print(f"Circle drawn successfully")
