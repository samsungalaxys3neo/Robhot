#include <Arduino.h>
#include "lcd_control.h"
#include "servo_control.h"

String inputBuf = "";

void setup() {
  Serial.begin(115200);

  setupLCD(12, 11, 5, 4, 3, 2);
  setupServoControl(9);

  Serial.println("BOOT");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == '\n') {
      inputBuf.trim();

      if (inputBuf.length() > 0) {
        char cmd = inputBuf.charAt(0);

        if (cmd == 'W') {
          doWave();
          Serial.println("WAVE_OK");
        } else if (cmd == 'M') {
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
        } else if (cmd == 'C') {
          clearLCD();
          Serial.println("CLR_OK");
        } else if (inputBuf == "PING") {
          Serial.println("PONG");
        } else {
          Serial.print("ERR:");
          Serial.println(inputBuf);
        }
      }

      inputBuf = "";
    } else if (c != '\r') {
      inputBuf += c;
      if (inputBuf.length() > 128) inputBuf.remove(0, inputBuf.length() - 128);
    }
  }
}
