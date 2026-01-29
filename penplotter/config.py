"""Configuration and calibration constants for pen plotter control system."""

# ============================================================================
# Hardware Calibration
# ============================================================================

# Linear actuator calibration
ADC_MIN = 0  # Fully retracted (calibrated)
ADC_MAX = 834  # Fully extended (calibrated)
PHYSICAL_RANGE_MM = 300  # Physical travel distance in millimeters

# ADC to mm conversion factor
ADC_PER_MM = (ADC_MAX - ADC_MIN) / PHYSICAL_RANGE_MM  # ~2.78 ADC counts per mm

# Stepper motor configuration
MICROSTEPS_PER_REV = 1024000  # 200 steps × 256 microsteps × 20:1 gearbox
MICROSTEPS_PER_DEGREE = MICROSTEPS_PER_REV / 360.0  # ~2844.44 microsteps per degree

# ============================================================================
# Serial Communication
# ============================================================================

# Serial port settings
BAUD_RATE = 9600
SERIAL_TIMEOUT = 1.0  # seconds for read timeout

# Command timeouts (seconds)
TIMEOUT_FAST = 5.0  # For STOP, GET_POS
TIMEOUT_SLOW = 60.0  # For HOME, LINEAR, ROTATE (slow under load)

# ============================================================================
# Control Parameters
# ============================================================================

# Position tolerance
LINEAR_TOLERANCE_MM = 3.6  # Approximately ±10 ADC counts

# Home position
HOME_ANGLE_DEG = 0.0  # Home angle in degrees
HOME_RADIUS_MM = 0.0  # Home radius (fully retracted)

# ============================================================================
# Workspace and Board Configuration
# ============================================================================

# Board dimensions (mm)
BOARD_WIDTH = 280  # X extent: -140 to +140mm from pen
BOARD_HEIGHT = 350  # Y extent: 0 to 350mm from pen

# Physical limits
ANGLE_MIN = -45  # Minimum rotation angle (degrees)
ANGLE_MAX = 45  # Maximum rotation angle (degrees)
RADIUS_MIN = 0  # Minimum extension (mm)
RADIUS_MAX = 300  # Maximum extension (mm)

# Safety margins for validation
ANGLE_MARGIN = 2  # Degrees to leave as margin from limits
RADIUS_MARGIN = 5  # mm to leave as margin from limits

# Path interpolation
DEFAULT_STEP_SIZE = 1.0  # mm between interpolated points for straight lines
                         # Smaller = smoother but slower. Tunable per draw_line() call.
                         # Recommended range: 0.5-2mm for good smoothness
