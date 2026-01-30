"""
Path execution module with segment-based progress tracking.

This module wraps the drawing primitives to provide progress tracking,
timing metrics, and visualization updates during drawing operations.
"""

import time
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
import datetime

from penplotter.hardware import Plotter
from penplotter.control.primitives import draw_line
from penplotter.path import interpolate_line
from penplotter import config


@dataclass
class PathSegment:
    """Represents a single segment of the drawing path."""

    index: int  # Segment number in sequence
    start: Tuple[float, float]  # Start point (x, y) in mm
    end: Tuple[float, float]  # End point (x, y) in mm
    length: float  # Segment length in mm
    completed: bool = False  # Whether segment has been drawn
    start_time: Optional[float] = None  # When execution started
    end_time: Optional[float] = None  # When execution completed

    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds, or None if not completed."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class PathExecutor:
    """
    Manages path execution with segment-based progress tracking.

    This class wraps the low-level drawing primitives to provide:
    - Segment-based progress tracking
    - Timing metrics for each segment
    - Progress callbacks for live visualization
    - Simple data logging
    """

    def __init__(self, plotter: Plotter, step_size: float = None):
        """
        Initialize the path executor.

        Args:
            plotter: Connected Plotter instance
            step_size: Interpolation step size in mm (default: from config)
        """
        self.plotter = plotter
        self.step_size = step_size if step_size is not None else config.DEFAULT_STEP_SIZE
        self.segments: List[PathSegment] = []
        self.current_segment_index: int = -1
        self.progress_callback: Optional[Callable[[Optional[Tuple[float, float]], float], None]] = None
        self.execution_start_time: Optional[float] = None
        self.execution_end_time: Optional[float] = None

    def set_path(self, points: List[Tuple[float, float]]):
        """
        Set the path to be drawn as a sequence of connected line segments.

        Args:
            points: List of (x, y) coordinates defining the path
        """
        self.segments = []

        for i in range(len(points) - 1):
            start = points[i]
            end = points[i + 1]

            # Calculate segment length
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            length = (dx**2 + dy**2) ** 0.5

            segment = PathSegment(
                index=i,
                start=start,
                end=end,
                length=length
            )
            self.segments.append(segment)

        self.current_segment_index = -1

    def set_progress_callback(self, callback: Callable[[PathSegment], None]):
        """
        Set a callback function to be called after each segment completes.

        Args:
            callback: Function that takes a PathSegment as argument
        """
        self.progress_callback = callback

    def execute(self):
        """
        Execute the complete path, tracking progress for each segment.

        This method draws all segments in sequence and tracks timing/progress.
        """
        if not self.segments:
            raise ValueError("No path segments defined. Call set_path() first.")

        self.execution_start_time = time.time()

        for i, segment in enumerate(self.segments):
            self.current_segment_index = i
            self._execute_segment(segment)

        self.execution_end_time = time.time()

    def _execute_segment(self, segment: PathSegment):
        """
        Execute a single path segment with live position tracking.

        Args:
            segment: The segment to execute
        """
        segment.start_time = time.time()

        # Get interpolated points for this segment
        from penplotter.kinematics import cartesian_to_hardware
        points = interpolate_line(segment.start, segment.end, self.step_size)

        # Draw each point and call progress callback
        for i, (x, y) in enumerate(points):
            # Convert to hardware units
            steps, adc = cartesian_to_hardware(x, y)

            # Execute movements
            self.plotter.rotate(steps)
            self.plotter.linear(adc)

            # Call progress callback with current position
            if self.progress_callback:
                progress = (i + 1) / len(points)
                self.progress_callback((x, y), progress)

        segment.end_time = time.time()
        segment.completed = True

    @property
    def total_segments(self) -> int:
        """Get total number of segments in the path."""
        return len(self.segments)

    @property
    def completed_segments(self) -> int:
        """Get number of completed segments."""
        return sum(1 for seg in self.segments if seg.completed)

    @property
    def progress_percentage(self) -> float:
        """Get execution progress as percentage (0-100)."""
        if not self.segments:
            return 0.0
        return (self.completed_segments / self.total_segments) * 100.0

    @property
    def total_path_length(self) -> float:
        """Get total length of all segments in mm."""
        return sum(seg.length for seg in self.segments)

    @property
    def completed_path_length(self) -> float:
        """Get length of completed segments in mm."""
        return sum(seg.length for seg in self.segments if seg.completed)

    @property
    def total_execution_time(self) -> Optional[float]:
        """Get total execution time in seconds, or None if not completed."""
        if self.execution_start_time and self.execution_end_time:
            return self.execution_end_time - self.execution_start_time
        return None

    @property
    def average_segment_time(self) -> Optional[float]:
        """Get average time per segment in seconds."""
        completed = [seg for seg in self.segments if seg.completed and seg.duration]
        if not completed:
            return None
        return sum(seg.duration for seg in completed) / len(completed)

    @property
    def estimated_time_remaining(self) -> Optional[float]:
        """Estimate remaining execution time based on average segment time."""
        avg_time = self.average_segment_time
        if avg_time is None:
            return None

        remaining = self.total_segments - self.completed_segments
        return remaining * avg_time

    def get_executed_path(self) -> List[Tuple[float, float]]:
        """
        Get the list of points that have been executed so far.

        Returns:
            List of (x, y) coordinates including all completed segments
        """
        if not self.segments:
            return []

        points = [self.segments[0].start]  # Start with first point

        for segment in self.segments:
            if segment.completed:
                points.append(segment.end)
            else:
                break

        return points

    def get_summary(self) -> dict:
        """
        Get a summary of execution metrics.

        Returns:
            Dictionary containing execution statistics
        """
        return {
            "total_segments": self.total_segments,
            "completed_segments": self.completed_segments,
            "progress_percentage": self.progress_percentage,
            "total_path_length_mm": self.total_path_length,
            "completed_path_length_mm": self.completed_path_length,
            "total_execution_time_s": self.total_execution_time,
            "average_segment_time_s": self.average_segment_time,
            "estimated_time_remaining_s": self.estimated_time_remaining,
        }

    def print_summary(self):
        """Print execution summary to console."""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("Path Execution Summary")
        print("=" * 60)
        print(f"Segments: {summary['completed_segments']}/{summary['total_segments']} "
              f"({summary['progress_percentage']:.1f}%)")
        print(f"Path length: {summary['completed_path_length_mm']:.1f}/"
              f"{summary['total_path_length_mm']:.1f} mm")

        if summary['total_execution_time_s']:
            print(f"Total time: {summary['total_execution_time_s']:.2f}s")

        if summary['average_segment_time_s']:
            print(f"Average segment time: {summary['average_segment_time_s']:.3f}s")

        if summary['estimated_time_remaining_s']:
            print(f"Estimated remaining: {summary['estimated_time_remaining_s']:.1f}s")

        print("=" * 60)
