"""
Test script for drawing a rectangle with the pen plotter.

This script demonstrates the rectangle drawing functionality by drawing
a square rotated 45 degrees, similar to the example in the assignment.
"""

import math
from penplotter.hardware.plotter import Plotter
from penplotter.control import draw_rectangle
from penplotter.kinematics.transforms import cartesian_to_polar
from penplotter.config import DEFAULT_STEP_SIZE


def main():
    """Draw a rotated rectangle test pattern."""

    # Configuration
    SERIAL_PORT = "/dev/tty.usbmodem1101"

    # Rectangle parameters (matching assignment example)
    # Note: Origin is at rotation point (0,0), pen is at (0, 160mm)
    # Board extends from y=160mm to y=510mm
    CENTER = (0, 335)  # Center of the drawing board (175mm from pen = 335mm from rotation point)
    WIDTH = 100  # mm
    HEIGHT = 100  # mm (square)
    ROTATION = 45  # degrees (rotated like in assignment image)
    STEP_SIZE = DEFAULT_STEP_SIZE  # 1.0mm interpolation

    print("=" * 60)
    print("Rectangle Drawing Test")
    print("=" * 60)
    print(f"\nParameters:")
    print(f"  Center: {CENTER} mm")
    print(f"  Width: {WIDTH} mm")
    print(f"  Height: {HEIGHT} mm")
    print(f"  Rotation: {ROTATION}°")
    print(f"  Step size: {STEP_SIZE} mm")

    # Calculate expected perimeter and number of interpolation points
    perimeter = 2 * (WIDTH + HEIGHT)
    expected_points = int(perimeter / STEP_SIZE)
    print(f"\nExpected path:")
    print(f"  Perimeter: {perimeter:.1f} mm")
    print(f"  Interpolation points: ~{expected_points}")

    # Calculate corner positions for display
    half_w = WIDTH / 2
    half_h = HEIGHT / 2
    corners_local = [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h),
    ]

    # Apply rotation
    rad = math.radians(ROTATION)
    cos_r = math.cos(rad)
    sin_r = math.sin(rad)
    corners = []
    for x_local, y_local in corners_local:
        x_rot = x_local * cos_r - y_local * sin_r
        y_rot = x_local * sin_r + y_local * cos_r
        x_abs = CENTER[0] + x_rot
        y_abs = CENTER[1] + y_rot
        corners.append((x_abs, y_abs))

    print(f"\nCorner coordinates (Cartesian):")
    for i, (x, y) in enumerate(corners):
        angle, radius = cartesian_to_polar(x, y)
        print(f"  Corner {i}: ({x:6.1f}, {y:6.1f}) mm  →  "
              f"({angle:6.1f}°, {radius:6.1f} mm)")

    # Connect to plotter
    print(f"\nConnecting to plotter on {SERIAL_PORT}...")
    with Plotter(SERIAL_PORT) as plotter:
        print("Connected successfully!")

        # Home the plotter
        print("\nHoming plotter...")
        plotter.home()
        print("Homing complete.")

        # Draw the rectangle
        print("\nDrawing rectangle...")
        try:
            draw_rectangle(
                plotter,
                center=CENTER,
                width=WIDTH,
                height=HEIGHT,
                rotation=ROTATION,
                step_size=STEP_SIZE
            )
            print("\nRectangle completed successfully!")
        except ValueError as e:
            print(f"\nError: {e}")
            print("Rectangle could not be drawn - coordinates out of bounds.")
            return

        # Return to home
        print("\nReturning to home position...")
        plotter.home()
        print("Done!")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
