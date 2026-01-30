"""
Interactive matplotlib-based GUI for pen plotter control.

This module provides an interactive interface for drawing with the pen plotter,
replacing the previous Tkinter-based GUI with a matplotlib-based approach
that matches the wagon project's design patterns.
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox, RadioButtons
from matplotlib.backend_bases import MouseButton
from matplotlib.patches import Circle
import numpy as np
from typing import List, Tuple, Optional
import threading
import time
import serial.tools.list_ports

from penplotter.hardware import Plotter
from penplotter.control import validate_point
from penplotter.control.executor import PathExecutor
from penplotter.visualization.styles import (
    MONUMENTAL_ORANGE,
    MONUMENTAL_BLUE,
    MONUMENTAL_CREAM,
    MONUMENTAL_YELLOW_ORANGE,
    MONUMENTAL_DARK_BLUE,
    MONUMENTAL_TAUPE,
    apply_dark_style,
    style_legend
)
from penplotter.data.path import calculate_path_statistics
from penplotter.config import BOARD_WIDTH, BOARD_HEIGHT, PEN_OFFSET_MM


class PlotterGUI:
    """
    Interactive matplotlib-based GUI for pen plotter control.

    Features:
    - Click to add path points
    - Preview path before execution
    - Serial port connection management with auto-detection
    - Live actuator arm visualization during execution
    - Connection status indicator
    - Path validation and workspace boundaries
    """

    def __init__(self):
        """Initialize the plotter GUI."""
        self.plotter: Optional[Plotter] = None
        self.is_connected = False
        self.is_drawing = False
        self.serial_port = "/dev/tty.usbmodem1101"  # Default port
        self.available_ports = []
        self.current_pen_position = (0, PEN_OFFSET_MM)  # Track current pen position

        # Drawing mode: 'Line' or 'Curve'
        self.drawing_mode = 'Line'

        # Unified segment list (supports mixed line and curve segments)
        self.segments = []  # List of segment dicts with 'type' field

        # Current drawing state
        self.current_line_start = None  # For line mode: last point clicked
        self.current_curve = {
            'start': None,
            'control1': None,
            'control2': None,
            'end': None
        }

        # Setup the GUI
        self._setup_figure()

    def _setup_figure(self):
        """Setup the main GUI figure and controls."""
        self.fig = plt.figure(figsize=(12, 8), facecolor=MONUMENTAL_DARK_BLUE)
        self.fig.canvas.manager.set_window_title("Pen Plotter Control")

        # Main drawing canvas
        self.ax_canvas = plt.axes([0.1, 0.25, 0.8, 0.65])
        apply_dark_style(self.ax_canvas, apply_grid=True)

        self._setup_canvas()
        self._setup_controls()

        # Connect mouse events
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

    def _setup_canvas(self):
        """Setup the drawing canvas."""
        ax = self.ax_canvas

        # Calculate workspace boundaries (origin-relative coordinates)
        x_min = -BOARD_WIDTH / 2
        x_max = BOARD_WIDTH / 2
        y_min = PEN_OFFSET_MM  # Pen home position (160mm from origin)
        y_max = PEN_OFFSET_MM + BOARD_HEIGHT  # Maximum reach (470mm from origin)

        # Draw workspace rectangle
        ax.plot(
            [x_min, x_max, x_max, x_min, x_min],
            [y_min, y_min, y_max, y_max, y_min],
            color=MONUMENTAL_CREAM,
            alpha=0.5,
            linestyle="--",
            linewidth=2,
            label="Drawing area"
        )

        # Draw origin reference line (rotation axis at y=0)
        ax.axhline(y=0, color=MONUMENTAL_TAUPE,
                   linestyle=':', linewidth=1.5, alpha=0.7,
                   label="Rotation axis (y=0)")

        # Draw pen home position marker
        ax.plot(0, PEN_OFFSET_MM, 'x', color=MONUMENTAL_BLUE,
                markersize=12, markeredgewidth=2, label=f"Pen home (y={PEN_OFFSET_MM})")

        # Initialize path visualization
        self.path_line, = ax.plot([], [], 'o-',
                                   color=MONUMENTAL_ORANGE,
                                   linewidth=2,
                                   markersize=6,
                                   label="Drawing path")

        # Initialize curve control point visualization
        self.control_handles, = ax.plot([], [], '--',
                                        color=MONUMENTAL_YELLOW_ORANGE,
                                        linewidth=1.5,
                                        alpha=0.6,
                                        label="Bezier handles")
        self.control_points, = ax.plot([], [], 's',
                                       color=MONUMENTAL_YELLOW_ORANGE,
                                       markersize=8,
                                       alpha=0.8)
        self.curve_preview, = ax.plot([], [], '-',
                                      color=MONUMENTAL_ORANGE,
                                      linewidth=1.5,
                                      alpha=0.5)

        # Initialize actuator arm visualization
        self.arm_line, = ax.plot([0, 0], [0, PEN_OFFSET_MM],
                                  color=MONUMENTAL_YELLOW_ORANGE,
                                  linewidth=4,
                                  alpha=0.7,
                                  label="Actuator arm")
        self.pen_marker, = ax.plot([0], [PEN_OFFSET_MM], 'o',
                                    color=MONUMENTAL_YELLOW_ORANGE,
                                    markersize=10,
                                    markeredgecolor=MONUMENTAL_CREAM,
                                    markeredgewidth=2,
                                    label="Pen position")

        # Labels and styling
        ax.set_xlabel("X Position (mm)", fontsize=12, color=MONUMENTAL_CREAM)
        ax.set_ylabel("Y Position from rotation axis (mm)", fontsize=12, color=MONUMENTAL_CREAM)
        ax.set_title("Click to Add Path Points", fontsize=14,
                     color=MONUMENTAL_CREAM, weight="bold")
        ax.set_xlim(x_min - 20, x_max + 20)
        ax.set_ylim(-20, y_max + 20)  # Show from origin to max reach
        ax.set_aspect("equal", adjustable="box")

        # Legend
        legend = ax.legend(loc="upper right", fontsize=9)
        style_legend(legend, framealpha=0.8)

        # Status text
        self.status_text = ax.text(
            0.02, 0.98,
            "Status: Ready\nClick to add points",
            transform=ax.transAxes,
            fontsize=10,
            color=MONUMENTAL_CREAM,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor=MONUMENTAL_DARK_BLUE,
                      edgecolor=MONUMENTAL_TAUPE, alpha=0.8)
        )

    def _setup_controls(self):
        """Setup control buttons and inputs."""
        button_color = MONUMENTAL_TAUPE
        hover_color = MONUMENTAL_ORANGE
        text_color = MONUMENTAL_CREAM

        # Serial port input
        ax_port = plt.axes([0.15, 0.14, 0.2, 0.04])
        ax_port.set_facecolor(MONUMENTAL_DARK_BLUE)
        self.port_box = TextBox(
            ax_port,
            'Port:',
            initial=self.serial_port,
            color=button_color,
            hovercolor=hover_color,
            label_pad=0.01
        )
        self.port_box.label.set_color(text_color)
        self.port_box.on_submit(self._on_port_changed)

        # Detect Ports button
        ax_detect = plt.axes([0.36, 0.14, 0.08, 0.04])
        self.btn_detect = Button(
            ax_detect,
            'Detect',
            color=button_color,
            hovercolor=hover_color
        )
        self.btn_detect.label.set_color(text_color)
        self.btn_detect.on_clicked(self._on_detect_ports)

        # Connection status indicator (circle)
        ax_status = plt.axes([0.45, 0.14, 0.02, 0.04])
        ax_status.set_xlim(0, 1)
        ax_status.set_ylim(0, 1)
        ax_status.axis('off')
        self.status_circle = Circle((0.5, 0.5), 0.3,
                                     color=MONUMENTAL_TAUPE,
                                     transform=ax_status.transAxes)
        ax_status.add_patch(self.status_circle)

        # Connect button
        ax_connect = plt.axes([0.48, 0.14, 0.10, 0.04])
        self.btn_connect = Button(
            ax_connect,
            'Connect',
            color=button_color,
            hovercolor=hover_color
        )
        self.btn_connect.label.set_color(text_color)
        self.btn_connect.on_clicked(self._on_connect)

        # Clear button
        ax_clear = plt.axes([0.15, 0.08, 0.12, 0.04])
        self.btn_clear = Button(
            ax_clear,
            'Clear Path',
            color=button_color,
            hovercolor=hover_color
        )
        self.btn_clear.label.set_color(text_color)
        self.btn_clear.on_clicked(self._on_clear)

        # Undo button
        ax_undo = plt.axes([0.28, 0.08, 0.12, 0.04])
        self.btn_undo = Button(
            ax_undo,
            'Undo Point',
            color=button_color,
            hovercolor=hover_color
        )
        self.btn_undo.label.set_color(text_color)
        self.btn_undo.on_clicked(self._on_undo)

        # Execute button
        ax_execute = plt.axes([0.42, 0.08, 0.12, 0.04])
        self.btn_execute = Button(
            ax_execute,
            'Execute',
            color=MONUMENTAL_BLUE,
            hovercolor=MONUMENTAL_ORANGE
        )
        self.btn_execute.label.set_color(text_color)
        self.btn_execute.on_clicked(self._on_execute)

        # Home button
        ax_home = plt.axes([0.60, 0.14, 0.10, 0.04])
        self.btn_home = Button(
            ax_home,
            'Home',
            color=button_color,
            hovercolor=hover_color
        )
        self.btn_home.label.set_color(text_color)
        self.btn_home.on_clicked(self._on_home)

        # Close button
        ax_close = plt.axes([0.72, 0.14, 0.10, 0.04])
        self.btn_close = Button(
            ax_close,
            'Close',
            color=button_color,
            hovercolor=hover_color
        )
        self.btn_close.label.set_color(text_color)
        self.btn_close.on_clicked(self._on_close)

        # Drawing mode toggle buttons (Line vs Curve)
        ax_line_mode = plt.axes([0.56, 0.08, 0.06, 0.04])
        self.btn_line_mode = Button(
            ax_line_mode,
            'Line',
            color=MONUMENTAL_ORANGE,  # Active by default
            hovercolor=hover_color
        )
        self.btn_line_mode.label.set_color(text_color)
        self.btn_line_mode.on_clicked(lambda event: self._on_mode_changed('Line'))

        ax_curve_mode = plt.axes([0.62, 0.08, 0.06, 0.04])
        self.btn_curve_mode = Button(
            ax_curve_mode,
            'Curve',
            color=button_color,  # Inactive by default
            hovercolor=hover_color
        )
        self.btn_curve_mode.label.set_color(text_color)
        self.btn_curve_mode.on_clicked(lambda event: self._on_mode_changed('Curve'))

    def _on_mode_changed(self, mode):
        """Handle drawing mode change."""
        if mode == self.drawing_mode:
            return  # Already in this mode

        self.drawing_mode = mode

        # Reset current drawing state (but keep completed segments)
        self.current_line_start = None
        self.current_curve = {
            'start': None,
            'control1': None,
            'control2': None,
            'end': None
        }

        # Update button styling
        if mode == 'Line':
            self.btn_line_mode.color = MONUMENTAL_ORANGE
            self.btn_curve_mode.color = MONUMENTAL_TAUPE
            self._update_status("Line mode: Click points to draw lines")
        else:
            self.btn_line_mode.color = MONUMENTAL_TAUPE
            self.btn_curve_mode.color = MONUMENTAL_ORANGE
            self._update_status("Curve mode: Click start → control1 → control2 → end")

        self._update_path_display()
        self.fig.canvas.draw_idle()

    def _on_click(self, event):
        """Handle mouse click to add path points."""
        # Only process left clicks on the canvas
        if event.inaxes != self.ax_canvas:
            return
        if event.button != MouseButton.LEFT:
            return
        if self.is_drawing:
            return

        # Get origin-relative coordinates from GUI (no conversion needed)
        x, y = event.xdata, event.ydata

        # Validate point is within workspace
        try:
            validate_point(x, y)

            if self.drawing_mode == 'Line':
                # Line mode: create line segment from last end point to new point
                if self.current_line_start is not None:
                    # Create line segment
                    segment = {
                        'type': 'line',
                        'start': self.current_line_start,
                        'end': (x, y)
                    }
                    self.segments.append(segment)
                    self._update_status(f"Line added: {self.current_line_start} → ({x:.1f}, {y:.1f})\n"
                                        f"Total segments: {len(self.segments)}")
                else:
                    # First point in line mode
                    self._update_status(f"Start point: ({x:.1f}, {y:.1f})\nClick next point")

                # Update start point for next line
                self.current_line_start = (x, y)
                self._update_path_display()

            else:
                # Curve mode: collect 4 points for Bezier curve
                if self.current_curve['start'] is None:
                    self.current_curve['start'] = (x, y)
                    self._update_status(f"Curve start: ({x:.1f}, {y:.1f})\nClick control point 1")
                elif self.current_curve['control1'] is None:
                    self.current_curve['control1'] = (x, y)
                    self._update_status(f"Control 1: ({x:.1f}, {y:.1f})\nClick control point 2")
                elif self.current_curve['control2'] is None:
                    self.current_curve['control2'] = (x, y)
                    self._update_status(f"Control 2: ({x:.1f}, {y:.1f})\nClick end point")
                else:
                    # Fourth click completes the curve
                    self.current_curve['end'] = (x, y)

                    # Store the completed curve segment
                    segment = {
                        'type': 'curve',
                        'start': self.current_curve['start'],
                        'end': self.current_curve['end'],
                        'control1': self.current_curve['control1'],
                        'control2': self.current_curve['control2']
                    }
                    self.segments.append(segment)

                    self._update_status(f"Curve completed!\nTotal segments: {len(self.segments)}")

                    # Reset for next curve
                    self.current_curve = {
                        'start': None,
                        'control1': None,
                        'control2': None,
                        'end': None
                    }

                self._update_path_display()

        except ValueError as e:
            self._update_status(f"Invalid point: {e}", error=True)

    def _update_path_display(self):
        """Update the visualization of the current path."""
        from penplotter.path.bezier import generate_bezier_curve

        # Collect all path points from completed segments
        all_path_points = []
        all_control_points = []
        all_handle_lines = []

        for segment in self.segments:
            if segment['type'] == 'line':
                # Add line segment endpoints
                all_path_points.extend([segment['start'], segment['end']])
            elif segment['type'] == 'curve':
                # Generate curve visualization
                curve_points = generate_bezier_curve(
                    segment['start'],
                    segment['end'],
                    [segment['control1'], segment['control2']],
                    num_samples=50
                )
                all_path_points.extend(curve_points)

                # Add control points
                all_control_points.extend([segment['control1'], segment['control2']])

                # Add handle lines (start to control1, control2 to end)
                all_handle_lines.extend([
                    segment['start'], segment['control1'],
                    [np.nan, np.nan],  # Break in line
                    segment['control2'], segment['end'],
                    [np.nan, np.nan]  # Break before next segment
                ])

        # Show completed segments
        if all_path_points:
            points_array = np.array(all_path_points)
            self.path_line.set_data(points_array[:, 0], points_array[:, 1])
        else:
            self.path_line.set_data([], [])

        # Show current drawing state
        temp_points = []
        temp_controls = []
        temp_handles = []

        if self.drawing_mode == 'Line' and self.current_line_start is not None:
            # Show the current start point for the next line
            temp_points.append(self.current_line_start)

        elif self.drawing_mode == 'Curve':
            # Show current curve being built
            if self.current_curve['start'] is not None:
                temp_points.append(self.current_curve['start'])

                if self.current_curve['control1'] is not None:
                    temp_controls.append(self.current_curve['control1'])
                    temp_handles.extend([
                        self.current_curve['start'],
                        self.current_curve['control1']
                    ])

                if self.current_curve['control2'] is not None:
                    temp_controls.append(self.current_curve['control2'])

                # Show preview if we have enough points
                if self.current_curve['control1'] is not None and self.current_curve['control2'] is not None:
                    try:
                        # Use control2 as temporary end if no end yet
                        temp_end = self.current_curve['end'] if self.current_curve['end'] else self.current_curve['control2']
                        preview_points = generate_bezier_curve(
                            self.current_curve['start'],
                            temp_end,
                            [self.current_curve['control1'], self.current_curve['control2']],
                            num_samples=30
                        )
                        if preview_points:
                            preview_array = np.array(preview_points)
                            self.curve_preview.set_data(preview_array[:, 0], preview_array[:, 1])
                    except:
                        self.curve_preview.set_data([], [])

                    # Add handle to control2
                    if self.current_curve['end']:
                        temp_handles.extend([[np.nan, np.nan], self.current_curve['control2'], self.current_curve['end']])
                        temp_points.append(self.current_curve['end'])

        # Update current state visualizations
        if temp_controls or all_control_points:
            all_controls = all_control_points + temp_controls
            control_array = np.array(all_controls)
            self.control_points.set_data(control_array[:, 0], control_array[:, 1])
        else:
            self.control_points.set_data([], [])

        if temp_handles or all_handle_lines:
            all_handles = all_handle_lines + temp_handles
            handle_array = np.array(all_handles)
            self.control_handles.set_data(handle_array[:, 0], handle_array[:, 1])
        else:
            self.control_handles.set_data([], [])

        if self.drawing_mode != 'Curve' or self.current_curve['start'] is None:
            self.curve_preview.set_data([], [])

        self.fig.canvas.draw_idle()

    def _update_actuator_display(self, x: float, y: float):
        """Update the actuator arm visualization."""
        self.current_pen_position = (x, y)
        # Draw arm from origin to pen position
        self.arm_line.set_data([0, x], [0, y])
        self.pen_marker.set_data([x], [y])
        self.fig.canvas.draw_idle()

    def _update_status(self, message: str, error: bool = False):
        """Update the status text."""
        prefix = "Status: "
        if error:
            prefix = "ERROR: "

        connection_status = "Connected" if self.is_connected else "Disconnected"
        full_message = f"{prefix}{connection_status}\n{message}"

        self.status_text.set_text(full_message)
        if error:
            self.status_text.set_color(MONUMENTAL_ORANGE)
        else:
            self.status_text.set_color(MONUMENTAL_CREAM)

        self.fig.canvas.draw_idle()

    def _on_port_changed(self, text):
        """Handle serial port input change."""
        self.serial_port = text
        self._update_status(f"Port set to: {text}")

    def _on_detect_ports(self, event):
        """Handle detect ports button click."""
        # Get list of available serial ports
        ports = serial.tools.list_ports.comports()

        # Filter for USB serial ports only (exclude Bluetooth, WiFi, etc.)
        usb_ports = [
            port.device for port in ports
            if 'usb' in port.device.lower() or
               'acm' in port.device.lower() or
               'usbserial' in port.device.lower() or
               'usbmodem' in port.device.lower()
        ]

        self.available_ports = usb_ports

        if self.available_ports:
            port_list = "\n".join(self.available_ports)
            self._update_status(f"USB ports found:\n{port_list}")
            # Auto-select first USB port
            self.serial_port = self.available_ports[0]
            self.port_box.set_val(self.serial_port)
        else:
            self._update_status("No USB serial ports detected", error=True)

    def _on_connect(self, event):
        """Handle connect button click."""
        if self.is_connected:
            # Disconnect
            if self.plotter:
                self.plotter.disconnect()
                self.plotter = None
            self.is_connected = False
            self.btn_connect.label.set_text('Connect')
            self.status_circle.set_color(MONUMENTAL_TAUPE)  # Gray when disconnected
            self._update_status("Disconnected")
        else:
            # Connect
            try:
                self.plotter = Plotter(self.serial_port)
                self.plotter.connect()  # Actually connect to the plotter
                self.is_connected = True
                self.btn_connect.label.set_text('Disconnect')
                self.status_circle.set_color('#00ff00')  # Green when connected
                self._update_status(f"Connected to {self.serial_port}")
            except Exception as e:
                self._update_status(f"Connection failed: {e}", error=True)
                self.status_circle.set_color('#ff0000')  # Red on error
                if self.plotter:
                    self.plotter = None

        self.fig.canvas.draw_idle()

    def _on_clear(self, event):
        """Handle clear button click."""
        if not self.is_drawing:
            self.segments = []
            self.current_line_start = None
            self.current_curve = {
                'start': None,
                'control1': None,
                'control2': None,
                'end': None
            }
            self._update_path_display()
            self._update_status("All segments cleared")

    def _on_undo(self, event):
        """Handle undo button click."""
        if not self.is_drawing:
            if self.drawing_mode == 'Line':
                # Undo in line mode: remove current start point or last segment
                if self.current_line_start is not None:
                    # Remove the pending start point
                    self.current_line_start = None
                    # Set start to the end of the last segment if exists
                    if len(self.segments) > 0:
                        last_seg = self.segments[-1]
                        self.current_line_start = last_seg['end']
                    self._update_status("Removed pending point. Click to continue from last position")
                elif len(self.segments) > 0:
                    # Remove last segment
                    removed = self.segments.pop()
                    if removed['type'] == 'line':
                        # Set start point to the removed segment's start
                        self.current_line_start = removed['start']
                        self._update_status(f"Removed line segment. {len(self.segments)} segments remaining")
                    else:
                        self._update_status(f"Removed curve segment. {len(self.segments)} segments remaining")
                self._update_path_display()

            elif self.drawing_mode == 'Curve':
                # Undo in curve mode: remove last control point or last segment
                if self.current_curve['end'] is not None:
                    self.current_curve['end'] = None
                    self._update_status("Removed end point. Click end point")
                elif self.current_curve['control2'] is not None:
                    self.current_curve['control2'] = None
                    self._update_status("Removed control point 2. Click control point 2")
                elif self.current_curve['control1'] is not None:
                    self.current_curve['control1'] = None
                    self._update_status("Removed control point 1. Click control point 1")
                elif self.current_curve['start'] is not None:
                    self.current_curve['start'] = None
                    self._update_status("Removed start point. Click start point")
                elif len(self.segments) > 0:
                    removed = self.segments.pop()
                    seg_type = removed['type']
                    self._update_status(f"Removed {seg_type} segment. {len(self.segments)} segments remaining")
                self._update_path_display()

    def _on_home(self, event):
        """Handle home button click."""
        if self.is_connected and not self.is_drawing:
            try:
                self._update_status("Homing plotter...")
                self.plotter.home()
                # Update actuator display to home position
                self._update_actuator_display(0, PEN_OFFSET_MM)
                self._update_status("Plotter homed successfully")
            except Exception as e:
                self._update_status(f"Homing failed: {e}", error=True)

    def _on_execute(self, event):
        """Handle execute button click."""
        if not self.is_connected:
            self._update_status("Error: Not connected to plotter", error=True)
            return

        if len(self.segments) < 1:
            self._update_status("Error: Need at least 1 segment to draw", error=True)
            return

        if self.is_drawing:
            return

        # Print segment statistics
        line_count = sum(1 for seg in self.segments if seg['type'] == 'line')
        curve_count = sum(1 for seg in self.segments if seg['type'] == 'curve')

        print(f"\nPath Statistics:")
        print(f"  Total segments: {len(self.segments)}")
        print(f"    Lines: {line_count}")
        print(f"    Curves: {curve_count}")

        # Start drawing in a separate thread
        self.is_drawing = True
        thread = threading.Thread(target=self._execute_drawing)
        thread.daemon = True
        thread.start()

    def _execute_drawing(self):
        """Execute the drawing path with live actuator arm updates."""
        try:
            from penplotter.control.primitives import draw_line
            from penplotter.control.curves import draw_curve

            # Home before drawing
            self._update_status("Homing plotter...")
            self.plotter.home()
            time.sleep(1)

            # Setup progress callback for live position updates
            def on_position_update(current_pos, segment_progress):
                """Called frequently during drawing for live position updates."""
                if current_pos:
                    self._update_actuator_display(current_pos[0], current_pos[1])

            start_time = time.time()
            self._update_status(f"Drawing {len(self.segments)} segments...")

            # Draw each segment in order
            for i, segment in enumerate(self.segments):
                print(f"\nSegment {i+1}/{len(self.segments)} ({segment['type']})")

                if segment['type'] == 'line':
                    # Draw line segment with live position tracking
                    draw_line(
                        self.plotter,
                        segment['start'],
                        segment['end'],
                        progress_callback=on_position_update
                    )

                elif segment['type'] == 'curve':
                    # Draw curve segment with live position tracking
                    draw_curve(
                        self.plotter,
                        segment['start'],
                        segment['end'],
                        [segment['control1'], segment['control2']],
                        progress_callback=on_position_update
                    )

            end_time = time.time()
            duration = end_time - start_time

            # Count segment types
            line_count = sum(1 for seg in self.segments if seg['type'] == 'line')
            curve_count = sum(1 for seg in self.segments if seg['type'] == 'curve')

            self._update_status(f"Drawing complete!\n"
                                f"Drew {len(self.segments)} segments ({line_count} lines, {curve_count} curves) in "
                                f"{duration:.1f}s")

            # Home after drawing
            self._update_status("Returning to home...")
            self.plotter.home()
            self._update_actuator_display(0, PEN_OFFSET_MM)

        except Exception as e:
            self._update_status(f"Drawing failed: {e}", error=True)
            import traceback
            traceback.print_exc()

        finally:
            self.is_drawing = False

    def _on_close(self, event):
        """Handle close button click."""
        if self.plotter:
            self.plotter.disconnect()
        plt.close('all')

    def run(self):
        """Start the GUI event loop."""
        plt.show()


def main():
    """Main entry point for the GUI application."""
    print("=" * 60)
    print("Pen Plotter Interactive Control")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Enter serial port and click 'Connect'")
    print("2. Click on canvas to add path points")
    print("3. Click 'Execute' to draw the path")
    print("4. Use 'Undo' to remove last point or 'Clear Path' to start over")
    print("=" * 60)
    print()

    gui = PlotterGUI()
    gui.run()


if __name__ == "__main__":
    main()
