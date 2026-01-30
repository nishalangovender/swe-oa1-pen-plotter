"""
Path storage and logging utilities.

This module provides functions for storing planned paths, tracking execution
progress, and saving simple logs for later analysis.
"""

import csv
import json
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime


class PathLogger:
    """
    Simple logger for path execution data.

    Stores planned paths and execution progress to files for later
    visualization and analysis.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the path logger.

        Args:
            log_dir: Directory to store log files. If None, uses current directory.
        """
        if log_dir is None:
            # Create a timestamped directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = Path(f"run_{timestamp}")

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.planned_path_file = self.log_dir / "planned_path.csv"
        self.execution_log_file = self.log_dir / "execution_log.csv"
        self.summary_file = self.log_dir / "summary.json"

    def log_planned_path(self, points: List[Tuple[float, float]]):
        """
        Log the planned path to a CSV file.

        Args:
            points: List of (x, y) coordinates defining the path
        """
        with open(self.planned_path_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["index", "x_mm", "y_mm"])

            for i, (x, y) in enumerate(points):
                writer.writerow([i, x, y])

    def log_segment_completion(
        self,
        segment_index: int,
        start: Tuple[float, float],
        end: Tuple[float, float],
        duration: float,
        timestamp: float
    ):
        """
        Log the completion of a path segment.

        Args:
            segment_index: Index of the completed segment
            start: Start point (x, y) in mm
            end: End point (x, y) in mm
            duration: Segment execution time in seconds
            timestamp: Unix timestamp when segment completed
        """
        # Check if file exists to determine if we need to write header
        write_header = not self.execution_log_file.exists()

        with open(self.execution_log_file, "a", newline="") as f:
            writer = csv.writer(f)

            if write_header:
                writer.writerow([
                    "segment_index",
                    "start_x_mm",
                    "start_y_mm",
                    "end_x_mm",
                    "end_y_mm",
                    "duration_s",
                    "timestamp"
                ])

            writer.writerow([
                segment_index,
                start[0],
                start[1],
                end[0],
                end[1],
                duration,
                timestamp
            ])

    def log_summary(self, summary: dict):
        """
        Save execution summary to JSON file.

        Args:
            summary: Dictionary containing execution statistics
        """
        with open(self.summary_file, "w") as f:
            json.dump(summary, f, indent=2)

    def get_log_directory(self) -> Path:
        """Get the log directory path."""
        return self.log_dir


def load_planned_path(csv_file: Path) -> List[Tuple[float, float]]:
    """
    Load a planned path from a CSV file.

    Args:
        csv_file: Path to the planned_path.csv file

    Returns:
        List of (x, y) coordinate tuples
    """
    points = []

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            x = float(row["x_mm"])
            y = float(row["y_mm"])
            points.append((x, y))

    return points


def load_execution_log(csv_file: Path) -> List[dict]:
    """
    Load execution log from a CSV file.

    Args:
        csv_file: Path to the execution_log.csv file

    Returns:
        List of dictionaries containing segment execution data
    """
    segments = []

    with open(csv_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            segment = {
                "segment_index": int(row["segment_index"]),
                "start": (float(row["start_x_mm"]), float(row["start_y_mm"])),
                "end": (float(row["end_x_mm"]), float(row["end_y_mm"])),
                "duration": float(row["duration_s"]),
                "timestamp": float(row["timestamp"])
            }
            segments.append(segment)

    return segments


def calculate_path_statistics(points: List[Tuple[float, float]]) -> dict:
    """
    Calculate statistics for a path.

    Args:
        points: List of (x, y) coordinates

    Returns:
        Dictionary with path statistics
    """
    if len(points) < 2:
        return {
            "num_points": len(points),
            "num_segments": 0,
            "total_length_mm": 0.0,
            "avg_segment_length_mm": 0.0,
            "min_x": None,
            "max_x": None,
            "min_y": None,
            "max_y": None
        }

    # Calculate segment lengths
    segment_lengths = []
    for i in range(len(points) - 1):
        dx = points[i + 1][0] - points[i][0]
        dy = points[i + 1][1] - points[i][1]
        length = (dx**2 + dy**2) ** 0.5
        segment_lengths.append(length)

    # Find bounding box
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]

    return {
        "num_points": len(points),
        "num_segments": len(segment_lengths),
        "total_length_mm": sum(segment_lengths),
        "avg_segment_length_mm": sum(segment_lengths) / len(segment_lengths) if segment_lengths else 0.0,
        "min_x": min(x_coords),
        "max_x": max(x_coords),
        "min_y": min(y_coords),
        "max_y": max(y_coords)
    }
