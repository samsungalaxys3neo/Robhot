#include "servo_control.h"
#include <Servo.h>

static Servo s;
static bool attached = false;

void setupServoControl(uint8_t pin) {
  s.attach(pin);
  attached = true;
  s.write(90);
}

void moveServo(uint8_t angle) {
  if (!attached) return;
  if (angle > 180) angle = 180;
  s.write(angle);
}

void doWave() {
  if (!attached) return;
  s.write(60);  delay(200);
  s.write(120); delay(200);
  s.write(60);  delay(200);
  s.write(90);  delay(200);
  s.write(60);  delay(200);
  s.write(120); delay(200);
  s.write(60);  delay(200);
  s.write(90);  delay(200);
}
