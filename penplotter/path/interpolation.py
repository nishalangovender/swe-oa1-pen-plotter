"""Line interpolation for generating smooth paths in Cartesian space."""

import math
from typing import List, Tuple


def interpolate_line(
    start: Tuple[float, float],
    end: Tuple[float, float],
    step_size: float = 5.0,
) -> List[Tuple[float, float]]:
    """Interpolate points along a straight line in Cartesian space.

    Generates intermediate points along the line from start to end,
    ensuring that when converted to polar coordinates and drawn by
    the plotter, the result approximates a straight line.

    Args:
        start: Starting point (x, y) in mm
        end: Ending point (x, y) in mm
        step_size: Maximum distance between interpolated points in mm

    Returns:
        List of (x, y) points including start and end.
        If start and end are very close, returns [start, end].
    """
    x1, y1 = start
    x2, y2 = end

    # Calculate line length
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)

    # If line is very short, just return start and end
    if length < step_size:
        return [start, end]

    # Calculate number of segments
    num_segments = int(math.ceil(length / step_size))
    num_points = num_segments + 1

    # Generate interpolated points
    points = []
    for i in range(num_points):
        t = i / num_segments  # Parameter from 0 to 1
        x = x1 + t * dx
        y = y1 + t * dy
        points.append((x, y))

    return points


def interpolate_path(
    points: List[Tuple[float, float]],
    step_size: float = 5.0,
) -> List[Tuple[float, float]]:
    """Interpolate all segments in a multi-point path.

    Takes a path defined by key points and adds intermediate points
    along each segment to approximate straight lines in Cartesian space.

    Args:
        points: List of (x, y) waypoints defining the path
        step_size: Maximum distance between interpolated points in mm

    Returns:
        List of (x, y) points with interpolation applied to all segments.
        The first point is always included. Subsequent segment endpoints
        are included only once (not duplicated at segment boundaries).
    """
    if len(points) < 2:
        return points

    interpolated = []

    for i in range(len(points) - 1):
        segment = interpolate_line(points[i], points[i + 1], step_size)

        if i == 0:
            # First segment: include all points
            interpolated.extend(segment)
        else:
            # Subsequent segments: skip first point (already added as last point of previous segment)
            interpolated.extend(segment[1:])

    return interpolated
