"""
Bezier curve generation for pen plotter.

This module provides functions for generating cubic Bezier curves,
which are then interpolated into line segments for drawing.
"""

import numpy as np


def generate_bezier_curve(start, end, control_points, num_samples=100):
    """
    Generate points along a cubic Bezier curve.

    Uses the parametric Bezier equation to generate smooth curves.
    For cubic Bezier: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃

    Args:
        start: Tuple (x, y) for the start point
        end: Tuple (x, y) for the end point
        control_points: List of 2 tuples [(x1, y1), (x2, y2)] for control points
        num_samples: Number of points to sample along the curve (default: 100)

    Returns:
        List of (x, y) tuples representing points along the Bezier curve

    Raises:
        ValueError: If control_points doesn't contain exactly 2 points
    """
    if len(control_points) != 2:
        raise ValueError(f"Cubic Bezier curves require exactly 2 control points, got {len(control_points)}")

    # Extract points
    p0 = np.array(start)
    p1 = np.array(control_points[0])
    p2 = np.array(control_points[1])
    p3 = np.array(end)

    # Generate parameter values from 0 to 1
    t_values = np.linspace(0, 1, num_samples)

    # Calculate Bezier curve points using the cubic Bezier formula
    curve_points = []
    for t in t_values:
        # Bezier basis functions
        b0 = (1 - t) ** 3
        b1 = 3 * (1 - t) ** 2 * t
        b2 = 3 * (1 - t) * t ** 2
        b3 = t ** 3

        # Calculate point on curve
        point = b0 * p0 + b1 * p1 + b2 * p2 + b3 * p3
        curve_points.append((point[0], point[1]))

    return curve_points


def calculate_curve_length(start, end, control_points, num_samples=100):
    """
    Calculate the approximate length of a Bezier curve.

    Uses linear approximation by summing distances between sampled points.

    Args:
        start: Tuple (x, y) for the start point
        end: Tuple (x, y) for the end point
        control_points: List of 2 tuples for control points
        num_samples: Number of samples to use for length calculation

    Returns:
        Approximate length of the curve in mm
    """
    points = generate_bezier_curve(start, end, control_points, num_samples)

    total_length = 0.0
    for i in range(len(points) - 1):
        p1 = np.array(points[i])
        p2 = np.array(points[i + 1])
        total_length += np.linalg.norm(p2 - p1)

    return total_length


def validate_bezier_workspace(start, end, control_points, workspace_bounds):
    """
    Check if a Bezier curve stays within workspace boundaries.

    Samples the curve and checks if all points are within bounds.

    Args:
        start: Tuple (x, y) for the start point
        end: Tuple (x, y) for the end point
        control_points: List of 2 tuples for control points
        workspace_bounds: Tuple (max_x, max_y) for workspace limits

    Returns:
        Tuple (is_valid, out_of_bounds_points):
            - is_valid: Boolean indicating if curve is entirely in workspace
            - out_of_bounds_points: List of points outside workspace (empty if valid)
    """
    max_x, max_y = workspace_bounds
    curve_points = generate_bezier_curve(start, end, control_points, num_samples=50)

    out_of_bounds = []
    for x, y in curve_points:
        if x < 0 or x > max_x or y < 0 or y > max_y:
            out_of_bounds.append((x, y))

    is_valid = len(out_of_bounds) == 0
    return is_valid, out_of_bounds
