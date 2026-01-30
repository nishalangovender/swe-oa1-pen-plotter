"""
Real-time visualization during path execution.

This module provides live plotting capabilities that update as the pen
plotter draws, showing the planned path vs executed path and progress metrics.
"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

from penplotter.visualization.styles import (
    MONUMENTAL_ORANGE,
    MONUMENTAL_BLUE,
    MONUMENTAL_CREAM,
    MONUMENTAL_YELLOW_ORANGE,
    MONUMENTAL_DARK_BLUE,
    apply_dark_style,
    style_legend,
    format_time_label
)
from penplotter.config import BOARD_WIDTH, BOARD_HEIGHT, PEN_OFFSET_MM


class LivePlotter:
    """
    Live visualization of pen plotter execution.

    Displays:
    - Planned path (complete path in blue)
    - Executed path (growing orange line as drawing progresses)
    - Current pen position marker
    - Progress along path (segment completion percentage)
    """

    def __init__(self, planned_path: List[Tuple[float, float]]):
        """
        Initialize the live plotter.

        Args:
            planned_path: List of (x, y) coordinates defining the complete path (origin-relative)
        """
        # Store and display origin-relative coordinates directly
        self.planned_path = np.array(planned_path)
        self.executed_path = []
        self.current_position = None

        # Progress tracking
        self.total_segments = len(planned_path) - 1 if len(planned_path) > 1 else 0
        self.completed_segments = 0
        self.progress_percentage = 0.0

        # Timing
        self.start_time = None
        self.elapsed_time = 0.0
        self.estimated_total_time = None

        # Create figure and axes
        self._setup_figure()

    def _setup_figure(self):
        """Set up the matplotlib figure and axes."""
        self.fig = plt.figure(figsize=(10, 8), facecolor=MONUMENTAL_DARK_BLUE)

        # Create subplots: XY trajectory (top, larger), Progress bar (bottom, smaller)
        # Use gridspec for custom height ratios
        gs = self.fig.add_gridspec(2, 1, height_ratios=[5, 1], hspace=0.3)
        self.ax_trajectory = self.fig.add_subplot(gs[0])
        self.ax_progress = self.fig.add_subplot(gs[1])

        # Apply dark styling
        apply_dark_style(self.ax_trajectory, apply_grid=True)
        apply_dark_style(self.ax_progress, apply_grid=False)

        # Setup trajectory plot
        self._setup_trajectory_plot()

        # Setup progress plot
        self._setup_progress_plot()

    def _setup_trajectory_plot(self):
        """Setup the XY trajectory plot."""
        ax = self.ax_trajectory

        # Plot workspace boundaries (origin-relative coordinates)
        x_min = -BOARD_WIDTH / 2
        x_max = BOARD_WIDTH / 2
        y_min = PEN_OFFSET_MM  # Pen home position (160mm from origin)
        y_max = PEN_OFFSET_MM + BOARD_HEIGHT  # Maximum reach (470mm from origin)

        # Draw workspace rectangle
        ax.plot(
            [x_min, x_max, x_max, x_min, x_min],
            [y_min, y_min, y_max, y_max, y_min],
            color=MONUMENTAL_CREAM,
            alpha=0.3,
            linestyle="--",
            linewidth=1,
            label="Workspace"
        )

        # Plot planned path (full path in origin-relative coords)
        if len(self.planned_path) > 0:
            ax.plot(
                self.planned_path[:, 0],
                self.planned_path[:, 1],
                color=MONUMENTAL_BLUE,
                alpha=0.5,
                linewidth=2,
                label="Planned path"
            )

        # Initialize executed path line (will be updated)
        self.executed_line, = ax.plot(
            [], [],
            color=MONUMENTAL_ORANGE,
            linewidth=3,
            label="Executed path",
            zorder=5
        )

        # Initialize current position marker
        self.position_marker, = ax.plot(
            [], [],
            marker='o',
            markersize=10,
            color=MONUMENTAL_YELLOW_ORANGE,
            markeredgecolor=MONUMENTAL_CREAM,
            markeredgewidth=2,
            label="Current position",
            zorder=10
        )

        # Initialize actuator arm visualization
        self.arm_line, = ax.plot(
            [0, 0], [0, PEN_OFFSET_MM],
            color=MONUMENTAL_YELLOW_ORANGE,
            linewidth=4,
            alpha=0.6,
            zorder=8,
            label="Actuator arm"
        )

        # Labels and title
        ax.set_xlabel("X Position (mm)", fontsize=12, color=MONUMENTAL_CREAM)
        ax.set_ylabel("Y Position from rotation axis (mm)", fontsize=12, color=MONUMENTAL_CREAM)
        ax.set_title("Trajectory", fontsize=14, color=MONUMENTAL_CREAM, weight="bold")

        # Set equal aspect ratio
        ax.set_aspect("equal", adjustable="box")

        # Legend
        legend = ax.legend(loc="upper right", fontsize=9)
        style_legend(legend, framealpha=0.8)

    def _setup_progress_plot(self):
        """Setup the progress plot."""
        ax = self.ax_progress

        # Progress bar (horizontal)
        self.progress_bar = ax.barh(
            y=[0],
            width=[0],
            height=0.5,
            color=MONUMENTAL_ORANGE,
            edgecolor=MONUMENTAL_CREAM,
            linewidth=2
        )[0]

        # Add reference line at 100%
        ax.axvline(100, color=MONUMENTAL_BLUE, linestyle="--", linewidth=1, alpha=0.5)

        # Labels and title
        ax.set_xlabel("Progress (%)", fontsize=12, color=MONUMENTAL_CREAM)
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.5, 0.5)
        ax.set_yticks([])
        ax.set_title("Execution Progress", fontsize=14, color=MONUMENTAL_CREAM, weight="bold")

        # Add text annotations for metrics
        self.progress_text = ax.text(
            50, -0.3,
            "",
            ha="center",
            va="top",
            fontsize=10,
            color=MONUMENTAL_CREAM
        )

    def update_progress(
        self,
        executed_path: List[Tuple[float, float]],
        completed_segments: int,
        elapsed_time: float,
        estimated_total_time: Optional[float] = None
    ):
        """
        Update the visualization with new progress data.

        Args:
            executed_path: List of executed points so far
            completed_segments: Number of segments completed
            elapsed_time: Time elapsed since start (seconds)
            estimated_total_time: Estimated total execution time (seconds)
        """
        self.executed_path = executed_path
        self.completed_segments = completed_segments
        self.elapsed_time = elapsed_time
        self.estimated_total_time = estimated_total_time

        if self.total_segments > 0:
            self.progress_percentage = (completed_segments / self.total_segments) * 100.0

        # Update current position
        if len(executed_path) > 0:
            self.current_position = executed_path[-1]

        # Update plots
        self._update_plots()

    def _update_plots(self):
        """Update the plot elements with current data."""
        # Update executed path line (display origin-relative coordinates directly)
        if len(self.executed_path) > 0:
            executed_array = np.array(self.executed_path)
            self.executed_line.set_data(executed_array[:, 0], executed_array[:, 1])

        # Update current position marker (display origin-relative coordinates directly)
        if self.current_position is not None:
            pos_x = self.current_position[0]
            pos_y = self.current_position[1]
            self.position_marker.set_data([pos_x], [pos_y])

            # Update actuator arm to current position
            self.arm_line.set_data([0, pos_x], [0, pos_y])

        # Update progress bar
        self.progress_bar.set_width(self.progress_percentage)

        # Update progress text
        progress_str = f"{self.completed_segments}/{self.total_segments} segments "
        progress_str += f"({self.progress_percentage:.1f}%)\n"
        progress_str += f"Time: {format_time_label(self.elapsed_time)}"

        if self.estimated_total_time:
            remaining = self.estimated_total_time - self.elapsed_time
            if remaining > 0:
                progress_str += f" / {format_time_label(self.estimated_total_time)}"
                progress_str += f"\n(~{format_time_label(remaining)} remaining)"

        self.progress_text.set_text(progress_str)

        # Redraw (draw_idle is thread-safe, just schedules a redraw)
        self.fig.canvas.draw_idle()

    def show(self, block=False):
        """
        Display the live plot window.

        Args:
            block: If True, blocks until window is closed
        """
        plt.show(block=block)
        if not block:
            plt.pause(0.001)  # Allow GUI to update

    def save(self, filepath: Path):
        """
        Save the current plot to a file.

        Args:
            filepath: Path where to save the image
        """
        self.fig.savefig(
            filepath,
            facecolor=MONUMENTAL_DARK_BLUE,
            edgecolor='none',
            bbox_inches='tight',
            dpi=150
        )

    def close(self):
        """Close the plot window."""
        plt.close(self.fig)


def create_live_plotter(planned_path: List[Tuple[float, float]]) -> LivePlotter:
    """
    Convenience function to create a LivePlotter instance.

    Args:
        planned_path: List of (x, y) coordinates defining the complete path

    Returns:
        LivePlotter instance ready for use
    """
    return LivePlotter(planned_path)
