#ifndef LCD_CONTROL_H
#define LCD_CONTROL_H

#include <LiquidCrystal.h>

extern const int RS;
extern const int E_PIN;
extern const int D4;
extern const int D5;
extern const int D6;
extern const int D7;

extern LiquidCrystal lcd;

void setupLCD();
void displayMessage(const String &l1, const String &l2);
void clearLCD();

#endif
