#!/usr/bin/env python3
"""Test script for drawing a straight line with the pen plotter.

This script demonstrates the Scenario 5 (Hybrid Rapid Sequential) approach:
- Fine interpolation (1mm default step size)
- Rapid sequential ROTATE + LINEAR commands
- Overlapping motor execution for smooth motion

Usage:
    python test_straight_line.py                    # Use default line
    python test_straight_line.py 0 100 50 200       # Custom line: start_x start_y end_x end_y
"""

import sys
import time
import math
from penplotter.hardware import Plotter
from penplotter.drawing import draw_line, validate_point
from penplotter.kinematics import cartesian_to_polar
from penplotter.config import DEFAULT_STEP_SIZE


def main():
    """Draw a single straight line to test the plotter."""

    # Configuration
    PORT = '/dev/tty.usbmodem1101'

    # Parse command-line arguments for custom line coordinates
    if len(sys.argv) == 5:
        try:
            START = (float(sys.argv[1]), float(sys.argv[2]))
            END = (float(sys.argv[3]), float(sys.argv[4]))
            print("Using custom coordinates from command line")
        except ValueError:
            print("Error: Invalid coordinates. Use format: start_x start_y end_x end_y")
            sys.exit(1)
    else:
        # Default line (in mm, Cartesian coordinates)
        # Origin is at pen position: (0, 0) at bottom center of board
        START = (0, 100)    # Start 100mm up from pen
        END = (50, 200)     # End at 50mm right, 200mm up
        print("Using default coordinates")

    # Step size for interpolation
    STEP_SIZE = DEFAULT_STEP_SIZE  # 1.0mm between points (very fine for maximum smoothness)

    print("=" * 60)
    print("Pen Plotter: Straight Line Test")
    print("=" * 60)
    print()
    print(f"Port: {PORT}")
    print(f"Line: {START} → {END}")
    print(f"Step size: {STEP_SIZE}mm")
    print()

    # Validate coordinates
    try:
        validate_point(*START)
        validate_point(*END)
        print("Coordinates validated: within workspace bounds")
    except ValueError as e:
        print(f"Error: {e}")
        print("Line cannot be drawn - coordinates out of bounds.")
        sys.exit(1)
    print()

    # Calculate line properties
    dx = END[0] - START[0]
    dy = END[1] - START[1]
    length = math.sqrt(dx**2 + dy**2)
    print(f"Line length: {length:.1f}mm")
    print(f"Expected points: ~{int(length / STEP_SIZE) + 1}")
    print()

    # Show polar coordinates for start and end
    start_angle, start_radius = cartesian_to_polar(*START)
    end_angle, end_radius = cartesian_to_polar(*END)
    print("Polar coordinates:")
    print(f"  Start: angle={start_angle:.1f}°, radius={start_radius:.1f}mm")
    print(f"  End:   angle={end_angle:.1f}°, radius={end_radius:.1f}mm")
    print()

    # Connect to plotter
    print("Connecting to plotter...")
    try:
        with Plotter(PORT) as plotter:
            print("Connected!")
            print()

            # Home the plotter
            print("Homing plotter...")
            plotter.home()
            print("Homed at (0, 0)")
            print()

            # Wait before drawing
            print("Starting line in 2 seconds...")
            time.sleep(2)

            # Draw the line
            print("Drawing line...")
            start_time = time.time()

            draw_line(plotter, START, END, step_size=STEP_SIZE)

            elapsed = time.time() - start_time
            print()
            print(f"Line complete! Elapsed time: {elapsed:.1f}s")
            print()

            # Return to home
            print("Returning to home position...")
            plotter.home()
            print("Done!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
