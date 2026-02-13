// funzioni per controllare il servo

#include <Servo.h>

const int SERVO_PIN = 9;  // Pin a cui è collegato il servo

Servo servoMotor;

void setup() {
  // Inizializzazione del servo
  servoMotor.attach(SERVO_PIN);  // Collega il servo al pin definito
  servoMotor.write(90);  // Posiziona il servo a 90 gradi (posizione centrale)
}

void loop() {
  // Comando per eseguire il movimento di "ondeggiamento" del servo
  for (int i = 0; i < 3; i++) {
    servoMotor.write(0);  // Imposta il servo a 0 gradi
    delay(200);  // Aspetta 200 millisecondi
    servoMotor.write(90);  // Imposta il servo a 90 gradi
    delay(200);  // Aspetta 200 millisecondi
  }
  servoMotor.write(90);  // Posizione finale a 90 gradi
  delay(1000);  // Pausa di 1 secondo prima di ripartire
}
