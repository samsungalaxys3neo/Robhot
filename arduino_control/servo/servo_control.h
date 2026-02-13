// dichiaro le variabili per i servo 

#ifndef SERVO_CONTROL_H
#define SERVO_CONTROL_H

#include <Servo.h>
#include <LiquidCrystal.h>

// Pin mapping (adjust if your wiring differs)
extern const int RS;
extern const int E_PIN;
extern const int D4;
extern const int D5;
extern const int D6;
extern const int D7;
extern const int SERVO_PIN;

extern LiquidCrystal lcd;
extern Servo servoMotor;

extern String inputBuf;

void setupServoControl();
void doWave();
void displayMessage(const String &l1, const String &l2);

#endif
