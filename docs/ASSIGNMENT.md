# SWE OA1: Pen-plotter

Welcome to the Monumental office! We’re very excited to have you here for this trial for the software engineer role.

![You can open this in your browser by scanning this code.](images/image.png)

You can open this in your browser by scanning this code.

# Assignment

Over the next two days, you will be drawing some shapes using our pen-plotter hardware.

![pen-plotter.png](images/pen-plotter.png)

There will be a couple of other activities during the on-site. You should have a printed schedule - if not, ask for it now!

Use any tools you normally would while working. That means you can search for answers, ask an LLM, look up formulas and so on. We want to see your problem-solving skills, but we don’t want you to get stuck on minor technical issues. Ask an engineer nearby if you need something.

## 1. Get the example code running

First, let’s get some example code running on the board.

### Arduino

- You’ll need to install Arduino IDE, along with the Arduino-Pico core:

  https://github.com/earlephilhower/arduino-pico?tab=readme-ov-file#installation

- The pen-plotter uses a custom board based on the RP2040 microcontroller, you should select the board as “Solder Party RP2040 Stamp”.

### Arduino libraries

Libraries (These should all be available from the internal libraries manager in the IDE — no need to manually install)

- TMCStepper - https://github.com/teemuatlut/TMCStepper
- ADS1X15 - [https://www.arduino.cc/reference/en/libraries/ads1x15](https://www.arduino.cc/reference/en/libraries/ads1x15/)
- Adafruit PWM Servo - https://github.com/adafruit/Adafruit-PWM-Servo-Driver-Library

### Sample code

At the bottom of this document you will find some firmware code to get you started.

You should have received an email with a link to this page. Paste the example code into the Arduino IDE and upload it to to the board.

The code contains some setup (no need to understand it in-depth) and some example code (in the `loop()` function) to move the actuators. It won’t do anything until you open the serial monitor.

Having trouble? Ask for help now - we don’t want you to get stuck on this.

## 2. Write a program to send commands to the board

Modify the firmware so that you can control the motors by sending commands over serial from your computer (e.g. from a Python script).

Start with a couple of simple commands (e.g. ‘rotate by n steps’ or ‘extend by m units’). You can add more when you need them!

Your firmware should eventually handle only low-level commands, while your application code (e.g. Python script) will reason about higher-level concepts such as drawing lines.

## 3. Draw a rectangle

Next, we want you to draw a rectangle using the system. Parameterise the rectangle somehow (e.g. by side length or rotation).

You should start with a simple solution - even if it doesn’t produce perfect output. We want to see how you trade off expediency and quality.

You should aim to get this working by the end of day 1.

![You should be able to draw a rectangle like this.](images/draw-a-square.png)

You should be able to draw a rectangle like this.

## 4. Be creative

Once you’ve got this working, extend your system with something interesting.

**Vision/control candidates**: we expect you to add a vision component to the system. For instance, draw something yourself on a piece of paper, take a picture of it with a camera and then make the pen-plotter draw the same thing.

**Other candidates**: here are some ideas.

- Design an UI for the system. How would you make it possible for the user to design and draw more interesting shapes?
- Support reading a configuration file to draw arbitrary polygons and curves.
  - If you let us know what format your program takes a little before you’re finished on the second day, then we’ll generate some fun shapes for you.
- Implement an alternative control method. There are some more complex solutions that can significantly improve the speed and quality of your drawings.
- Something else? If you have a cool idea, we’d like to see your creativity!

## 5. Demo and assignment debrief

At the end of day 2, we’ll move the pen plotter to a meeting room. You will have a chance to show what you’ve built and the output it can produce. Then we’ll talk about your implementation, the choices you made and reflect on what you might have done differently. Make sure you are able to explain the design decisions you have made and how they are implemented.

Please submit your work as a zip file or a public GitHub repository to Dom, Ross, or Bouke ahead of the debrief.

Include a clear README that explains your approach and lists all dependencies - no installation script needed.

# About the hardware

- The stepper motor has 200 steps, which the motor driver divides further down to 256 microsteps per full step.
  - At the output of the motor there is also a 20:1 gearbox, ergo a full rotation would be 200 _ 256 _ 20 microsteps.
  - As an example, if `stepperDriver.XACTUAL()` currently returned 0, then setting `stepperDriver.XTARGET(200 * 256 * 20)` would cause the output to move one complete rotation.
- The linear actuator has an potentiometer which returns a value indicating how extended the actuator is. See the `readPosition()` function below.

## Tips

- You will probably want to do some calibration of the actuator positions.
- The microcontroller can work with USB-C alone. In order to drive the actuators you will need to turn on the power supply (ask one of us for help if you need it!)
- If you turn off the power supply after running the setup code (see `setup()` below), you will need to run setup again as the motor driver needs to be reinitialised (`setupMotor()`)
- If the microcontroller does not respond when you try to upload new firmware, try plugging in the USB-C cable while holding the small ‘BOOT’ button. It should appear as a storage device and you will be able to upload firmware again.

# Sample firmware code

Below you will find some sample firmware code that gives basic control over the pen-plotter’s actuators. You will probably want to use this as your starting point for controlling them.

```arduino
#include <TMCStepper.h>

#include <Wire.h>
#include "ADS1X15.h"
#include <Adafruit_PWMServoDriver.h>

constexpr pin_size_t pin_chipSelA = 21; // Mot0
constexpr pin_size_t pin_chipSelB = 18; // Enc0
constexpr pin_size_t pin_chipSelC = 25; // Mot1
constexpr pin_size_t pin_chipSelD = 24; // Enc1

constexpr pin_size_t pin_SPI0SCK = 22;
constexpr pin_size_t pin_SPI0MOSI = 19;
constexpr pin_size_t pin_SPI0MISO = 20;

constexpr pin_size_t in1Pin = 1;
constexpr pin_size_t in2Pin = 0;

// Stepper Motor OConfig
constexpr uint16_t MOTOR_CURRENT = 500;
constexpr uint8_t DEFAULT_IRUN = 8;
constexpr uint8_t DEFAULT_IHOLD = 8;
constexpr uint8_t TMC_TOFFRUN = 4;

#define SPEED_RPS 1.0
#define RATIO_ACCEL 5.0
#define RAIIO_DECEL 5.0

constexpr float FULL_STEPS_PER_REV = 200.0;
constexpr float MICROSTEP_FACTOR = 256.0;

constexpr float DEFAULT_VEL = (FULL_STEPS_PER_REV * MICROSTEP_FACTOR * SPEED_RPS);
constexpr float DEFAULT_ACCEL = (FULL_STEPS_PER_REV * MICROSTEP_FACTOR / RATIO_ACCEL);
constexpr float DEFAULT_DECEL = (FULL_STEPS_PER_REV * MICROSTEP_FACTOR / RAIIO_DECEL);

constexpr float RS = 0.05;

TMC5160Stepper stepperDriver(pin_chipSelA, RS);

Adafruit_PWMServoDriver linearDriver(PCA9685_I2C_ADDRESS, Wire1);
ADS1015 ADS(0x48, &Wire1);

void setupMotor() {
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
  //
  // Sets the internal motion profile —- see datasheet
  stepperDriver.v1(0); // Use Trapezoid Only, disable first ramps
  stepperDriver.a1(DEFAULT_ACCEL);
  stepperDriver.d1(DEFAULT_DECEL);
  stepperDriver.AMAX(DEFAULT_ACCEL);
  stepperDriver.VMAX(DEFAULT_VEL);
  stepperDriver.DMAX(DEFAULT_DECEL);

  stepperDriver.toff(TMC_TOFFRUN);
}

void setupI2C() {
  Wire1.setSDA(2);
  Wire1.setSCL(3);
  Wire1.begin();

  Serial.println("Wire 1 Begin");
  if (!ADS.begin())
    Serial.println("ADS Error");

  if (!linearDriver.begin())
    Serial.println("PWM Error");

  linearDriver.setPin(in1Pin, 0);
  linearDriver.setPin(in2Pin, 0);

  Serial.println("I2C Done");
}

void setup() {
  pinMode(pin_chipSelA, OUTPUT);
  SPI.setTX(pin_SPI0MOSI);
  SPI.setRX(pin_SPI0MISO);
  SPI.setSCK(pin_SPI0SCK);

  SPI.begin();

  Serial.begin(9600);
  while (!Serial); // Wait for USB monitor to open
  Serial.println("Online");

  setupMotor();
  setupI2C();

  if (stepperDriver.test_connection() != 0)
  {
    Serial.println("Driver not connected");
    while (1);
  }
}

int readPosition() {
  return ADS.readADC(1);
}

void linearRetract(uint16_t speed = 4095)
{
  linearDriver.setPin(in1Pin, speed);
  linearDriver.setPin(in2Pin, 0);
}

void linearExtend(uint16_t speed = 4095)
{

  linearDriver.setPin(in1Pin, 0);
  linearDriver.setPin(in2Pin, speed);
}

void linearStop() {
  linearDriver.setPin(in1Pin, 0);
  linearDriver.setPin(in2Pin, 0);
}

// Example of using the functions to control things
void loop() {
  Serial.println(readPosition()); // Read "FL" Port
  linearRetract();
  delay(1000);
  linearExtend();
  delay(1000);
  linearStop();
  delay(1000);

  // Move 10 full steps from current position
  stepperDriver.XTARGET(stepperDriver.XACTUAL() + (MICROSTEP_FACTOR * 10) ); // This is in Microsteps
  // Wait until done
  while (!stepperDriver.position_reached()) {
    Serial.println("Moving");
    delay(1000);
  }
}

```
