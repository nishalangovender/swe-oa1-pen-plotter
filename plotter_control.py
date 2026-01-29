#!/usr/bin/env python3
"""Direct plotter control CLI for manual positioning and testing."""

import sys
from penplotter.hardware import Plotter
from penplotter.kinematics import polar_to_hardware, hardware_to_polar


def print_help():
    """Print available commands."""
    print("\nAvailable commands:")
    print("  home                    - Move to home position")
    print("  rotate <degrees>        - Rotate to angle (requires GET_POS)")
    print("  linear <mm>             - Extend to distance (requires GET_POS)")
    print("  raw_rotate <steps>      - Rotate to absolute microsteps (direct)")
    print("  raw_linear <adc>        - Extend to ADC value 0-834 (direct)")
    print("  pos                     - Get current position")
    print("  stop                    - Emergency stop")
    print("  debug                   - Toggle debug mode")
    print("  help                    - Show this help")
    print("  quit                    - Exit")
    print()


def main(port: str):
    """Run interactive plotter control.

    Args:
        port: Serial port (e.g., '/dev/ttyACM0' or 'COM3')
    """
    print(f"Connecting to plotter on {port}...")

    try:
        plotter = Plotter(port)
        plotter.connect()
        print("Connected! Type 'help' for available commands.\n")

        while True:
            try:
                # Get user input
                cmd_input = input("plotter> ").strip()

                if not cmd_input:
                    continue

                parts = cmd_input.split()
                command = parts[0].lower()

                # Process commands
                if command == "quit" or command == "exit":
                    break

                elif command == "help":
                    print_help()

                elif command == "home":
                    print("Homing...")
                    plotter.home()
                    print("Done")

                elif command == "rotate":
                    if len(parts) != 2:
                        print("Usage: rotate <degrees>")
                        continue
                    degrees = float(parts[1])
                    # Convert to hardware units (keep current radius)
                    current_steps, current_adc = plotter.get_pos()
                    current_angle, current_radius = hardware_to_polar(current_steps, current_adc)
                    steps, _ = polar_to_hardware(degrees, current_radius)
                    print(f"Rotating to {degrees}° ({steps} steps)...")
                    plotter.rotate(steps)
                    print("Done")

                elif command == "linear":
                    if len(parts) != 2:
                        print("Usage: linear <mm>")
                        continue
                    mm = float(parts[1])
                    # Convert to hardware units (keep current angle)
                    current_steps, current_adc = plotter.get_pos()
                    current_angle, current_radius = hardware_to_polar(current_steps, current_adc)
                    _, adc = polar_to_hardware(current_angle, mm)
                    print(f"Extending to {mm}mm (ADC {adc})...")
                    plotter.linear(adc)
                    print("Done")

                elif command == "pos":
                    steps, adc = plotter.get_pos()
                    angle, radius = hardware_to_polar(steps, adc)
                    print(f"Position: {angle:.1f}° ({steps} steps), {radius:.1f}mm (ADC {adc})")

                elif command == "stop":
                    print("Emergency stop!")
                    plotter.stop()
                    print("Stopped")

                elif command == "raw_rotate":
                    if len(parts) != 2:
                        print("Usage: raw_rotate <steps>")
                        continue
                    steps = int(parts[1])
                    print(f"Rotating to {steps} steps...")
                    plotter.rotate(steps)
                    print("Done")

                elif command == "raw_linear":
                    if len(parts) != 2:
                        print("Usage: raw_linear <adc>")
                        continue
                    adc = int(parts[1])
                    if adc < 0 or adc > 834:
                        print("ADC value must be between 0 and 834")
                        continue
                    print(f"Extending to ADC {adc}...")
                    plotter.linear(adc)
                    print("Done")

                elif command == "debug":
                    plotter.debug = not plotter.debug
                    print(f"Debug mode: {'ON' if plotter.debug else 'OFF'}")

                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands")

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'quit' to exit.")

            except Exception as e:
                print(f"Error: {e}")

        print("\nDisconnecting...")
        plotter.disconnect()
        print("Goodbye!")

    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python plotter_control.py <port>")
        print("Example: python plotter_control.py /dev/ttyACM0")
        sys.exit(1)

    port = sys.argv[1]
    main(port)
