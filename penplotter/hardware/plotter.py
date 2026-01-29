"""Hardware communication layer for pen plotter control."""

import serial
import time
from typing import Optional, Tuple

from penplotter import config


class PlotterError(Exception):
    """Exception raised for plotter hardware errors."""

    pass


class Plotter:
    """Serial communication interface for pen plotter hardware.

    Handles low-level communication with the firmware via serial protocol.
    """

    def __init__(self, port: str, baud_rate: int = config.BAUD_RATE, debug: bool = False):
        """Initialize plotter connection.

        Args:
            port: Serial port name (e.g., '/dev/ttyACM0' or 'COM3')
            baud_rate: Serial baud rate (default: from config)
            debug: Enable debug output for serial communication
        """
        self.port = port
        self.baud_rate = baud_rate
        self.serial: Optional[serial.Serial] = None
        self._connected = False
        self.debug = debug

    def connect(self) -> None:
        """Open serial connection to plotter."""
        try:
            self.serial = serial.Serial(
                self.port,
                self.baud_rate,
                timeout=config.SERIAL_TIMEOUT,
                write_timeout=config.SERIAL_TIMEOUT,
            )
            # Wait longer for Arduino auto-reset and firmware initialization
            print("Waiting for firmware to initialize...")
            time.sleep(3)

            # Clear any startup messages
            discarded_lines = 0
            while self.serial.in_waiting:
                line = self.serial.readline()
                discarded_lines += 1
                if self.debug:
                    print(f"[DEBUG] Discarded startup: {line.decode().strip()}")

            if self.debug and discarded_lines > 0:
                print(f"[DEBUG] Cleared {discarded_lines} startup message(s)")

            self._connected = True
            print(f"Connected to plotter on {self.port}")
        except serial.SerialException as e:
            raise PlotterError(f"Failed to connect to {self.port}: {e}")

    def disconnect(self) -> None:
        """Close serial connection."""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self._connected = False
            print("Disconnected from plotter")

    def _send_command(self, command: str, timeout: float = config.TIMEOUT_FAST) -> str:
        """Send command and wait for response.

        Args:
            command: Command string to send
            timeout: Timeout in seconds to wait for response

        Returns:
            Response string from firmware

        Raises:
            PlotterError: If command fails or times out
        """
        if not self._connected or not self.serial:
            raise PlotterError("Not connected to plotter")

        # Clear any pending input
        while self.serial.in_waiting:
            discarded = self.serial.readline().decode().strip()
            if self.debug:
                print(f"[DEBUG] Discarded: {discarded}")

        # Send command
        if self.debug:
            print(f"[DEBUG] Sending: {command}")
        self.serial.write(f"{command}\n".encode())
        self.serial.flush()

        # Wait for response with timeout
        start_time = time.time()
        response_lines = []

        while time.time() - start_time < timeout:
            if self.serial.in_waiting:
                line = self.serial.readline().decode().strip()
                if self.debug:
                    print(f"[DEBUG] Received: {line}")
                response_lines.append(line)

                # Check for terminal responses
                if line.startswith("OK"):
                    return line
                elif line.startswith("ERROR"):
                    raise PlotterError(f"Command '{command}' failed: {line}")

            time.sleep(0.01)

        if self.debug:
            print(f"[DEBUG] All received lines: {response_lines}")
        raise PlotterError(f"Command '{command}' timed out after {timeout}s")

    def home(self) -> None:
        """Move to home position (stepper=0, linear=fully retracted)."""
        response = self._send_command("HOME", timeout=config.TIMEOUT_SLOW)
        print("Homed")

    def rotate(self, steps: int) -> None:
        """Rotate to absolute position in microsteps.

        Args:
            steps: Target position in microsteps
        """
        # Use slow timeout - rotation can be slow when arm is extended
        response = self._send_command(f"ROTATE {steps}", timeout=config.TIMEOUT_SLOW)

    def linear(self, adc_value: int) -> None:
        """Move linear actuator to target ADC value.

        Args:
            adc_value: Target ADC value (0-834)
        """
        response = self._send_command(f"LINEAR {adc_value}", timeout=config.TIMEOUT_SLOW)

    def get_pos(self) -> Tuple[int, int]:
        """Get current position.

        Returns:
            Tuple of (stepper_position_microsteps, linear_adc_value)
        """
        # Use longer timeout - sometimes GET_POS is slow
        response = self._send_command("GET_POS", timeout=config.TIMEOUT_SLOW)
        # Parse "OK <steps> <adc>"
        parts = response.split()
        if len(parts) != 3 or parts[0] != "OK":
            raise PlotterError(f"Invalid GET_POS response: {response}")

        try:
            steps = int(parts[1])
            adc = int(parts[2])
            return (steps, adc)
        except ValueError:
            raise PlotterError(f"Failed to parse GET_POS response: {response}")

    def stop(self) -> None:
        """Emergency stop all motors."""
        response = self._send_command("STOP")
        print("Stopped")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
