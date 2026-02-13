#include "lcd/lcd_control.h"
#include "servo/servo_control.h"

void setup() {
  // Inizializza la comunicazione seriale per ricevere comandi
  Serial.begin(9600);
  
  // Inizializza l'LCD e il servo
  setupLCD();
  setupServoControl();
}

void loop() {
  // Verifica se ci sono dati disponibili sulla seriale
  while (Serial.available() > 0) {
    char c = Serial.read();  // Leggi il carattere ricevuto
    
    // Se si riceve un carattere di fine linea, elabora il comando
    if (c == '\n') {
      // Se ci sono comandi nella variabile inputBuf, processali
      if (inputBuf.length() > 0) {
        if (inputBuf.charAt(0) == 'W') {
          // Comando per eseguire il movimento di onda del servo
          doWave();
          Serial.println("WAVE_OK");  // Rispondi alla seriale con successo
        } else if (inputBuf.charAt(0) == 'M') {
          // Comando per visualizzare un messaggio sull'LCD (Mline1|line2)
          String payload = inputBuf.substring(1);  // Estrai il payload (linea1|linea2)
          int sep = payload.indexOf('|');  // Trova la separazione tra le due linee
          String l1 = "";
          String l2 = "";
          if (sep >= 0) {
            l1 = payload.substring(0, sep);  // Prima parte del messaggio
            l2 = payload.substring(sep + 1);  // Seconda parte del messaggio
          } else {
            l1 = payload;  // Se non c'è separazione, usa tutto come prima linea
          }
          displayMessage(l1, l2);  // Visualizza il messaggio sull'LCD
          Serial.println("MSG_OK");  // Rispondi con successo
        } else if (inputBuf.charAt(0) == 'C') {
          // Comando per pulire lo schermo LCD
          clearLCD();
          Serial.println("CLR_OK");  // Rispondi con successo
        }
      }
      inputBuf = "";  // Resetta il buffer dopo aver elaborato il comando
    } else {
      inputBuf += c;  // Aggiungi il carattere al buffer
      // Limita la lunghezza del buffer per evitare che diventi troppo lungo
      if (inputBuf.length() > 128) inputBuf = inputBuf.substring(inputBuf.length() - 128);
    }
  }
}
