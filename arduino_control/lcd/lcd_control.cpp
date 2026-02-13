#include "lcd_control.h"

const int RS = 12;
const int E_PIN = 11;
const int D4 = 5;
const int D5 = 4;
const int D6 = 3;
const int D7 = 2;

LiquidCrystal lcd(RS, E_PIN, D4, D5, D6, D7);

void setupLCD() {
  lcd.begin(16, 2);  // Imposta un LCD 16x2
  lcd.clear();       // Pulisce lo schermo
  lcd.setCursor(0, 0);  // Imposta il cursore nella posizione iniziale
  lcd.print("RobHot Ready");  // Visualizza un messaggio iniziale
}

void displayMessage(const String &l1, const String &l2) {
  lcd.clear();       // Pulisce lo schermo
  lcd.setCursor(0, 0);  // Imposta il cursore sulla prima linea
  String a = l1;
  String b = l2;
  if (a.length() > 16) a = a.substring(0, 16);  // Limita la lunghezza a 16 caratteri
  if (b.length() > 16) b = b.substring(0, 16);  // Limita la lunghezza a 16 caratteri
  lcd.print(a);  // Stampa la prima linea
  lcd.setCursor(0, 1);  // Passa alla seconda linea
  lcd.print(b);  // Stampa la seconda linea
}

void clearLCD() {
  lcd.clear();  // Pulisce lo schermo LCD
}
