"""Primitive drawing functions for pen plotter.

This module provides low-level drawing primitives that handle the conversion
from Cartesian coordinates to hardware commands.
"""

import time
from typing import Tuple

from penplotter.hardware import Plotter
from penplotter.path import interpolate_line
from penplotter.kinematics import cartesian_to_hardware, cartesian_to_polar
from penplotter import config


def draw_line(
    plotter: Plotter,
    start: Tuple[float, float],
    end: Tuple[float, float],
    step_size: float = None,
) -> None:
    """Draw a straight line from start to end in Cartesian space.

    This implementation uses Scenario 5 (Hybrid Rapid Sequential):
    - Interpolates Cartesian line into fine steps (default 5mm)
    - Sends ROTATE and LINEAR commands in rapid succession
    - Motors move with overlapping execution for smoother motion
    - No firmware changes required

    The line is approximated by visiting intermediate points along the
    Cartesian line segment. This ensures that curved paths in polar space
    approximate straight lines in Cartesian space.

    Args:
        plotter: Connected Plotter instance
        start: Starting point (x, y) in mm
        end: Ending point (x, y) in mm
        step_size: Distance between interpolated points in mm.
                   Smaller values = smoother lines but slower.
                   Default: 5mm (from config)

    Example:
        >>> with Plotter('/dev/ttyACM0') as p:
        ...     p.home()
        ...     draw_line(p, (0, 100), (50, 200))  # Draw from (0,100) to (50,200)

    Future Enhancement:
        Can be upgraded to use coordinated MOVE_TO firmware command for
        true simultaneous rotation + linear motion.
    """
    if step_size is None:
        step_size = config.DEFAULT_STEP_SIZE

    # Generate interpolated points along the line
    points = interpolate_line(start, end, step_size)

    print(f"  Drawing {len(points)} points along line (step_size={step_size}mm)")

    # Draw each point with rapid sequential commands
    for i, (x, y) in enumerate(points):
        # Convert to hardware units
        steps, adc = cartesian_to_hardware(x, y)

        print(f"    Point {i+1}/{len(points)}: ({x:.1f}, {y:.1f}) → steps={steps}, adc={adc}")

        # Execute movements in rapid succession (overlapping execution)
        plotter.rotate(steps)
        plotter.linear(adc)

        # No delay - send commands as fast as possible
        # Note: If firmware can't keep up, add small delay (0.02-0.05s)
