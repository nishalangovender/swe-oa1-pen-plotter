/*
 * Pen Plotter Control Firmware
 * Command-based serial protocol for position control
 *
 * Calibrated for 300mm linear actuator travel (ADC range: 0-834)
 *
 * Commands:
 *   HOME              - Move to home/zero position (stepper + linear)
 *   ROTATE <steps>    - Rotate to absolute position (microsteps)
 *   LINEAR <target>   - Move linear actuator to target ADC value (with validation)
 *   EXTEND_RAW        - Extend linear actuator (for calibration)
 *   RETRACT_RAW       - Retract linear actuator (for calibration)
 *   STOP_LINEAR       - Stop linear actuator
 *   STOP              - Emergency stop all motors
 *   GET_POS           - Get current position
 *   STATUS            - Get system status
 *   DEBUG_ADC         - Read all 4 ADC channels (debugging)
 */

#include <TMCStepper.h>
#include <Wire.h>
#include "ADS1X15.h"
#include <Adafruit_PWMServoDriver.h>

// Pin definitions
constexpr pin_size_t pin_chipSelA = 21; // Mot0
constexpr pin_size_t pin_chipSelB = 18; // Enc0
constexpr pin_size_t pin_chipSelC = 25; // Mot1
constexpr pin_size_t pin_chipSelD = 24; // Enc1

constexpr pin_size_t pin_SPI0SCK = 22;
constexpr pin_size_t pin_SPI0MOSI = 19;
constexpr pin_size_t pin_SPI0MISO = 20;

constexpr pin_size_t in1Pin = 1;
constexpr pin_size_t in2Pin = 0;

// Motor configuration
constexpr uint16_t MOTOR_CURRENT = 500;
constexpr uint8_t DEFAULT_IRUN = 8;
constexpr uint8_t DEFAULT_IHOLD = 8;
constexpr uint8_t TMC_TOFFRUN = 4;

#define SPEED_RPS 3.5  // Conservative speed increase for smoother motion (was 3.0)
#define RATIO_ACCEL 4.0  // Increased acceleration for faster ramp-up (was 5.0)
#define RAIIO_DECEL 5.0

constexpr float FULL_STEPS_PER_REV = 200.0;
constexpr float MICROSTEP_FACTOR = 256.0;

constexpr float DEFAULT_VEL = (FULL_STEPS_PER_REV * MICROSTEP_FACTOR * SPEED_RPS);
constexpr float DEFAULT_ACCEL = (FULL_STEPS_PER_REV * MICROSTEP_FACTOR / RATIO_ACCEL);
constexpr float DEFAULT_DECEL = (FULL_STEPS_PER_REV * MICROSTEP_FACTOR / RAIIO_DECEL);

constexpr float RS = 0.05;

// Calibration constants - CALIBRATED VALUES
constexpr int ADC_MIN = 0;        // Fully retracted (calibrated)
constexpr int ADC_MAX = 834;      // Fully extended (calibrated)
constexpr int ADC_HOME = ADC_MIN; // Home position = fully retracted

// Hardware instances
TMC5160Stepper stepperDriver(pin_chipSelA, RS);
Adafruit_PWMServoDriver linearDriver(PCA9685_I2C_ADDRESS, Wire1);
ADS1015 ADS(0x48, &Wire1);

// State variables
long homePosition = 0;
long targetLinearPosition = 0;
bool isHomed = false;

// Linear actuator control parameters
constexpr int LINEAR_TOLERANCE = 7;             // Reduced from 10 for better accuracy (~±2.5mm vs ±3.6mm)
constexpr int HOME_TOLERANCE = 15;              // Larger tolerance for homing to accommodate mechanical stop
constexpr unsigned long LINEAR_TIMEOUT = 20000; // 20 second timeout (actuator is slow)

void setup()
{
  // Initialize pins
  pinMode(pin_chipSelA, OUTPUT);
  SPI.setTX(pin_SPI0MOSI);
  SPI.setRX(pin_SPI0MISO);
  SPI.setSCK(pin_SPI0SCK);
  SPI.begin();

  // Initialize serial
  Serial.begin(9600);
  while (!Serial)
    ;

  Serial.println("Pen Plotter Firmware v1.0");
  Serial.println("Initializing...");

  // Initialize motor driver
  setupMotor();

  // Initialize I2C devices
  setupI2C();

  // Check driver connection
  if (stepperDriver.test_connection() != 0)
  {
    Serial.println("ERROR: Driver not connected");
    while (1)
      ;
  }

  Serial.println("Initialization complete");
  Serial.println("Ready for commands");
}

void setupMotor()
{
  stepperDriver.setSPISpeed(1000000);
  stepperDriver.reset();
  stepperDriver.toff(0);
  stepperDriver.rms_current(MOTOR_CURRENT);
  stepperDriver.ihold(DEFAULT_IHOLD);
  stepperDriver.irun(DEFAULT_IRUN);
  stepperDriver.en_pwm_mode(false);
  stepperDriver.VSTOP(10);
  stepperDriver.RAMPMODE(0);
  stepperDriver.TZEROWAIT(0);

  stepperDriver.shaft(0);
  stepperDriver.en_softstop(0);
  stepperDriver.shortdelay(true);
  stepperDriver.shortfilter(2);

  // Set motion profile
  stepperDriver.v1(0);
  stepperDriver.a1(DEFAULT_ACCEL);
  stepperDriver.d1(DEFAULT_DECEL);
  stepperDriver.AMAX(DEFAULT_ACCEL);
  stepperDriver.VMAX(DEFAULT_VEL);
  stepperDriver.DMAX(DEFAULT_DECEL);

  stepperDriver.toff(TMC_TOFFRUN);
}

void setupI2C()
{
  Wire1.setSDA(2);
  Wire1.setSCL(3);
  Wire1.begin();

  if (!ADS.begin())
  {
    Serial.println("ERROR: ADS1015 initialization failed");
  }

  // Set ADC gain for maximum voltage range (±6.144V)
  // This should give us the full potentiometer voltage swing
  ADS.setGain(0);  // 0 = ±6.144V range
  Serial.println("ADC gain set to ±6.144V");

  if (!linearDriver.begin())
  {
    Serial.println("ERROR: PWM driver initialization failed");
  }

  linearDriver.setPin(in1Pin, 0);
  linearDriver.setPin(in2Pin, 0);
}

void loop()
{
  if (Serial.available() > 0)
  {
    String command = Serial.readStringUntil('\n');
    command.trim();
    processCommand(command);
  }
}

void processCommand(String cmd)
{
  cmd.toUpperCase();

  if (cmd.startsWith("HOME"))
  {
    cmdHome();
  }
  else if (cmd.startsWith("ROTATE"))
  {
    int spaceIdx = cmd.indexOf(' ');
    if (spaceIdx > 0)
    {
      long steps = cmd.substring(spaceIdx + 1).toInt();
      cmdRotate(steps);
    }
    else
    {
      Serial.println("ERROR: ROTATE requires steps parameter");
    }
  }
  else if (cmd.startsWith("LINEAR"))
  {
    int spaceIdx = cmd.indexOf(' ');
    if (spaceIdx > 0)
    {
      int target = cmd.substring(spaceIdx + 1).toInt();
      cmdLinear(target);
    }
    else
    {
      Serial.println("ERROR: LINEAR requires target parameter");
    }
  }
  else if (cmd.startsWith("EXTEND_RAW"))
  {
    cmdExtendRaw();
  }
  else if (cmd.startsWith("RETRACT_RAW"))
  {
    cmdRetractRaw();
  }
  else if (cmd.startsWith("STOP_LINEAR"))
  {
    cmdStopLinear();
  }
  else if (cmd.startsWith("STOP"))
  {
    cmdStop();
  }
  else if (cmd.startsWith("GET_POS"))
  {
    cmdGetPos();
  }
  else if (cmd.startsWith("STATUS"))
  {
    cmdStatus();
  }
  else if (cmd.startsWith("DEBUG_ADC"))
  {
    cmdDebugADC();
  }
  else
  {
    Serial.println("ERROR: Unknown command");
  }
}

void cmdHome()
{
  // Move stepper to home position
  stepperDriver.XTARGET(homePosition);

  // Wait for stepper to reach position
  while (!stepperDriver.position_reached())
  {
    delay(5);  // Faster polling for quicker response
  }

  // Move linear actuator to home position (fully retracted)
  unsigned long startTime = millis();
  while (true)
  {
    int currentADC = ADS.readADC(1);
    int error = ADC_HOME - currentADC;

    // Check if reached target (use larger tolerance for homing to accommodate mechanical stop)
    if (abs(error) < HOME_TOLERANCE)
    {
      linearDriver.setPin(in1Pin, 0);
      linearDriver.setPin(in2Pin, 0);
      isHomed = true;
      Serial.println("OK");
      return;
    }

    // Check timeout
    if (millis() - startTime > LINEAR_TIMEOUT)
    {
      linearDriver.setPin(in1Pin, 0);
      linearDriver.setPin(in2Pin, 0);
      Serial.print("ERROR: HOME linear timeout at ADC ");
      Serial.println(currentADC);
      return;
    }

    // Apply velocity ramp-down control for smoother motion
    int absError = abs(error);
    uint16_t pwmValue;

    if (absError > 50)
    {
      pwmValue = 4095;  // Full speed
    }
    else if (absError > 20)
    {
      pwmValue = 2048;  // Medium speed (50%)
    }
    else
    {
      pwmValue = 1024;  // Slow approach (25%)
    }

    // Apply control based on error direction
    if (error > 0)
    {
      linearDriver.setPin(in1Pin, 0);
      linearDriver.setPin(in2Pin, pwmValue);
    }
    else
    {
      linearDriver.setPin(in1Pin, pwmValue);
      linearDriver.setPin(in2Pin, 0);
    }

    delay(5);  // Faster control loop: 200Hz vs 100Hz
  }
}

void cmdRotate(long steps)
{
  stepperDriver.XTARGET(steps);

  // Wait for position reached with timeout
  unsigned long startTime = millis();
  unsigned long timeout = 30000; // 30 second timeout

  while (!stepperDriver.position_reached())
  {
    if (millis() - startTime > timeout) {
      Serial.println("ERROR: ROTATE timeout - position not reached");
      return;
    }
    delay(5);  // Faster polling for quicker response
  }

  Serial.println("OK");
}

void cmdLinear(int targetADC)
{
  // Validate target is within calibrated range
  if (targetADC < ADC_MIN || targetADC > ADC_MAX)
  {
    Serial.print("ERROR: Target ");
    Serial.print(targetADC);
    Serial.print(" out of range [");
    Serial.print(ADC_MIN);
    Serial.print(", ");
    Serial.print(ADC_MAX);
    Serial.println("]");
    return;
  }

  targetLinearPosition = targetADC;
  unsigned long startTime = millis();

  // Control loop with feedback
  while (true)
  {
    int currentADC = ADS.readADC(1);
    int error = targetADC - currentADC;

    // Check if reached target
    if (abs(error) < LINEAR_TOLERANCE)
    {
      linearDriver.setPin(in1Pin, 0);
      linearDriver.setPin(in2Pin, 0);
      Serial.println("OK");
      return;
    }

    // Check timeout
    if (millis() - startTime > LINEAR_TIMEOUT)
    {
      linearDriver.setPin(in1Pin, 0);
      linearDriver.setPin(in2Pin, 0);
      Serial.print("ERROR: LINEAR timeout at ADC ");
      Serial.println(currentADC);
      return;
    }

    // Apply velocity ramp-down control for smoother motion
    // Use 3-zone control: full speed far away, ramp down as we approach target
    int absError = abs(error);
    uint16_t pwmValue;

    if (absError > 50)
    {
      // Zone 1: Far from target - full speed
      pwmValue = 4095;
    }
    else if (absError > 20)
    {
      // Zone 2: Approaching target - medium speed (50%)
      pwmValue = 2048;
    }
    else
    {
      // Zone 3: Near target - slow approach (25%)
      pwmValue = 1024;
    }

    // Apply control based on error direction
    if (error > 0)
    {
      // Need to extend
      linearDriver.setPin(in1Pin, 0);
      linearDriver.setPin(in2Pin, pwmValue);
    }
    else
    {
      // Need to retract
      linearDriver.setPin(in1Pin, pwmValue);
      linearDriver.setPin(in2Pin, 0);
    }

    delay(5);  // Faster control loop: 200Hz vs 100Hz
  }
}

void cmdStop()
{
  // Stop stepper at current position
  long currentPos = stepperDriver.XACTUAL();
  stepperDriver.XTARGET(currentPos);

  // Stop linear actuator
  linearDriver.setPin(in1Pin, 0);
  linearDriver.setPin(in2Pin, 0);

  Serial.println("OK");
}

void cmdGetPos()
{
  long stepperPos = stepperDriver.XACTUAL();
  int adcValue = ADS.readADC(1);

  Serial.print("OK ");
  Serial.print(stepperPos);
  Serial.print(" ");
  Serial.println(adcValue);
}

void cmdExtendRaw()
{
  // Extend at full speed (for calibration)
  linearDriver.setPin(in1Pin, 0);
  linearDriver.setPin(in2Pin, 4095);
  Serial.println("OK");
}

void cmdRetractRaw()
{
  // Retract at full speed (for calibration)
  linearDriver.setPin(in1Pin, 4095);
  linearDriver.setPin(in2Pin, 0);
  Serial.println("OK");
}

void cmdStopLinear()
{
  // Stop linear actuator
  linearDriver.setPin(in1Pin, 0);
  linearDriver.setPin(in2Pin, 0);
  Serial.println("OK");
}

void cmdStatus()
{
  Serial.println("=== Pen Plotter Status ===");
  Serial.print("Homed: ");
  Serial.println(isHomed ? "Yes" : "No");
  Serial.print("Stepper position: ");
  Serial.println(stepperDriver.XACTUAL());
  Serial.print("Linear ADC: ");
  Serial.println(ADS.readADC(1));
  Serial.print("ADC Range: [");
  Serial.print(ADC_MIN);
  Serial.print(", ");
  Serial.print(ADC_MAX);
  Serial.println("]");
  Serial.print("ADC Home: ");
  Serial.println(ADC_HOME);
  Serial.print("Driver enabled: ");
  Serial.println(stepperDriver.toff() > 0 ? "Yes" : "No");
  Serial.println("========================");
}

void cmdDebugADC() {
    // Read all 4 ADC channels
    Serial.println("=== ADC Channel Readings ===");
    Serial.print("Channel 0: ");
    Serial.println(ADS.readADC(0));
    Serial.print("Channel 1: ");
    Serial.println(ADS.readADC(1));
    Serial.print("Channel 2: ");
    Serial.println(ADS.readADC(2));
    Serial.print("Channel 3: ");
    Serial.println(ADS.readADC(3));
    Serial.println("===========================");
  }