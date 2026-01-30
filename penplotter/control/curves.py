"""Curve drawing primitives for pen plotter.

This module provides functions for drawing smooth curves using Bezier interpolation.
Curves are implemented as a series of interpolated straight line segments.
"""

import time
from typing import Tuple, List
import numpy as np

from penplotter.hardware import Plotter
from penplotter.path import interpolate_line
from penplotter.path.bezier import generate_bezier_curve, calculate_curve_length
from penplotter.kinematics import cartesian_to_hardware
from penplotter import config


def draw_curve(
    plotter: Plotter,
    start: Tuple[float, float],
    end: Tuple[float, float],
    control_points: List[Tuple[float, float]],
    step_size: float = None,
    progress_callback=None,
) -> None:
    """Draw a cubic Bezier curve from start to end with control points.

    The curve is generated using cubic Bezier interpolation with 2 control points,
    then broken down into small line segments for drawing. This approach allows
    smooth curves without requiring firmware changes.

    Implementation:
    - Generates Bezier curve points using parametric equation
    - Interpolates the curve into fine line segments
    - Sends ROTATE and LINEAR commands for each segment
    - Motors move with overlapping execution for smooth motion

    Args:
        plotter: Connected Plotter instance
        start: Starting point (x, y) in mm
        end: Ending point (x, y) in mm
        control_points: List of 2 control point tuples [(x1, y1), (x2, y2)]
                        These define the curve shape (Bezier handles)
        step_size: Distance between interpolated points in mm.
                   Smaller values = smoother curves but slower.
                   Default: 0.5mm (from config)
        progress_callback: Optional callback function(position, progress) for live updates

    Raises:
        ValueError: If control_points doesn't contain exactly 2 points

    Example:
        >>> with Plotter('/dev/ttyACM0') as p:
        ...     p.home()
        ...     # Draw a curved path with control points
        ...     draw_curve(p, (0, 100), (100, 100), [(25, 150), (75, 50)])
    """
    if step_size is None:
        step_size = config.DEFAULT_STEP_SIZE

    if len(control_points) != 2:
        raise ValueError(f"Cubic Bezier curves require exactly 2 control points, got {len(control_points)}")

    # Calculate approximate curve length for progress reporting
    curve_length = calculate_curve_length(start, end, control_points)

    # Generate Bezier curve points
    # Use more samples to ensure smooth curves (100 samples typically works well)
    curve_points = generate_bezier_curve(start, end, control_points, num_samples=100)

    print(f"  Drawing Bezier curve (length ≈ {curve_length:.1f}mm)")
    print(f"    Start: {start}")
    print(f"    Control 1: {control_points[0]}")
    print(f"    Control 2: {control_points[1]}")
    print(f"    End: {end}")

    # Interpolate the curve into fine segments for drawing
    all_points = []
    for i in range(len(curve_points) - 1):
        segment_start = curve_points[i]
        segment_end = curve_points[i + 1]

        # Interpolate each segment of the Bezier curve
        segment_points = interpolate_line(segment_start, segment_end, step_size)

        # Avoid duplicate points at segment boundaries
        if i > 0:
            segment_points = segment_points[1:]

        all_points.extend(segment_points)

    print(f"  Interpolated into {len(all_points)} points (step_size={step_size}mm)")

    # Draw each point with rapid sequential commands
    for i, (x, y) in enumerate(all_points):
        # Convert to hardware units
        steps, adc = cartesian_to_hardware(x, y)

        if i % 50 == 0 or i == len(all_points) - 1:  # Print progress every 50 points
            print(f"    Point {i+1}/{len(all_points)}: ({x:.1f}, {y:.1f}) → steps={steps}, adc={adc}")

        # Execute movements in rapid succession (overlapping execution)
        plotter.rotate(steps)
        plotter.linear(adc)

        # Call progress callback for live position updates
        if progress_callback:
            progress = (i + 1) / len(all_points)
            progress_callback((x, y), progress)

        # No delay - send commands as fast as possible
        # Note: If firmware can't keep up, add small delay (0.02-0.05s)


def draw_smooth_path(
    plotter: Plotter,
    points: List[Tuple[float, float]],
    tension: float = 0.5,
    step_size: float = None,
) -> None:
    """Draw a smooth path through multiple points using connected Bezier curves.

    This is a convenience function for drawing complex shapes by automatically
    generating control points to create smooth transitions between waypoints.

    Args:
        plotter: Connected Plotter instance
        points: List of waypoints [(x1, y1), (x2, y2), ...] to pass through
        tension: Controls curve tightness (0.0 = very curved, 1.0 = nearly straight)
                 Default: 0.5
        step_size: Distance between interpolated points in mm

    Raises:
        ValueError: If fewer than 2 points provided

    Example:
        >>> with Plotter('/dev/ttyACM0') as p:
        ...     p.home()
        ...     # Draw smooth path through 4 points
        ...     draw_smooth_path(p, [(0,100), (50,150), (100,100), (150,150)])
    """
    if len(points) < 2:
        raise ValueError("Need at least 2 points to draw a path")

    if len(points) == 2:
        # Just draw a straight line for 2 points
        from penplotter.control.primitives import draw_line
        draw_line(plotter, points[0], points[1], step_size)
        return

    print(f"  Drawing smooth path through {len(points)} waypoints")

    # For each pair of consecutive points, draw a Bezier curve
    # with automatically generated control points for smoothness
    for i in range(len(points) - 1):
        start = points[i]
        end = points[i + 1]

        # Generate control points based on neighboring points
        # This creates smooth transitions between segments
        if i == 0:
            # First segment: control points biased toward start
            dx, dy = end[0] - start[0], end[1] - start[1]
            control1 = (start[0] + dx * tension * 0.33, start[1] + dy * tension * 0.33)
            control2 = (start[0] + dx * tension * 0.66, start[1] + dy * tension * 0.66)
        elif i == len(points) - 2:
            # Last segment: control points biased toward end
            dx, dy = end[0] - start[0], end[1] - start[1]
            control1 = (start[0] + dx * (1 - tension) * 0.33, start[1] + dy * (1 - tension) * 0.33)
            control2 = (start[0] + dx * (1 - tension) * 0.66, start[1] + dy * (1 - tension) * 0.66)
        else:
            # Middle segments: consider previous and next points for smoothness
            prev = points[i - 1]
            next_point = points[i + 2] if i + 2 < len(points) else end

            # Calculate tangent direction based on neighbors
            dx1, dy1 = start[0] - prev[0], start[1] - prev[1]
            dx2, dy2 = next_point[0] - end[0], next_point[1] - end[1]

            # Control points offset from waypoints
            control1 = (start[0] + dx1 * tension * 0.5, start[1] + dy1 * tension * 0.5)
            control2 = (end[0] - dx2 * tension * 0.5, end[1] - dy2 * tension * 0.5)

        # Draw the curve segment
        draw_curve(plotter, start, end, [control1, control2], step_size)
