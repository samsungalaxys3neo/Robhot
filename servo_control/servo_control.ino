#include <Servo.h>
// LCD + Servo sketch: listen on Serial for simple commands
// Commands:
//  W        -> perform wave servo motion
//  M<l1>|<l2>\n -> display message on LCD (line1|line2)

#include <LiquidCrystal.h>
#include <Servo.h>

// Pin mapping (adjust if your wiring differs)
const int RS = 12;
const int E_PIN = 11;
const int D4 = 5;
const int D5 = 4;
const int D6 = 3;
const int D7 = 2;
const int SERVO_PIN = 9;

LiquidCrystal lcd(RS, E_PIN, D4, D5, D6, D7);
Servo servoMotor;

String inputBuf = "";

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("RobHot Ready");
  servoMotor.attach(SERVO_PIN);
  servoMotor.write(90);
}

void doWave() {
  for (int i = 0; i < 3; i++) {
    servoMotor.write(0);
    delay(200);
    servoMotor.write(90);
    delay(200);
  }
  servoMotor.write(90);
}

void displayMessage(const String &l1, const String &l2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  // ensure strings fit 16 chars
  String a = l1;
  String b = l2;
  if (a.length() > 16) a = a.substring(0, 16);
  if (b.length() > 16) b = b.substring(0, 16);
  lcd.print(a);
  lcd.setCursor(0, 1);
  lcd.print(b);
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      // process inputBuf
      if (inputBuf.length() > 0) {
        if (inputBuf.charAt(0) == 'W') {
          doWave();
          Serial.println("WAVE_OK");
        } else if (inputBuf.charAt(0) == 'M') {
          // format: Mline1|line2
          String payload = inputBuf.substring(1);
          int sep = payload.indexOf('|');
          String l1 = "";
          String l2 = "";
          if (sep >= 0) {
            l1 = payload.substring(0, sep);
            l2 = payload.substring(sep + 1);
          } else {
            l1 = payload;
          }
          displayMessage(l1, l2);
          Serial.println("MSG_OK");
        } else if (inputBuf.charAt(0) == 'C') {
          lcd.clear();
          Serial.println("CLR_OK");
        }
      }
      inputBuf = "";
    } else {
      inputBuf += c;
      // keep buffer reasonably bounded
      if (inputBuf.length() > 128) inputBuf = inputBuf.substring(inputBuf.length() - 128);
    }
  }
}
