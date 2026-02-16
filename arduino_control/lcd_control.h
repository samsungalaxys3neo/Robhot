#pragma once
#include <Arduino.h>

void setupLCD(uint8_t rs, uint8_t en, uint8_t d4, uint8_t d5, uint8_t d6, uint8_t d7);
void clearLCD();
void displayMessage(const String& l1, const String& l2);
