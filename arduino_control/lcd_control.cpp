#include "lcd_control.h"
#include <LiquidCrystal.h>

static LiquidCrystal* lcdPtr = nullptr;

void setupLCD(uint8_t rs, uint8_t en, uint8_t d4, uint8_t d5, uint8_t d6, uint8_t d7) {
  static LiquidCrystal lcd(rs, en, d4, d5, d6, d7);
  lcdPtr = &lcd;
  lcdPtr->begin(16, 2);
  lcdPtr->clear();
}

void clearLCD() {
  if (!lcdPtr) return;
  lcdPtr->clear();
}

void displayMessage(const String& l1, const String& l2) {
  if (!lcdPtr) return;
  lcdPtr->clear();
  lcdPtr->setCursor(0, 0);
  lcdPtr->print(l1);
  lcdPtr->setCursor(0, 1);
  lcdPtr->print(l2);
}
