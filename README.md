# RobHOT Project 

Questo sarà il mio cazzo di robot comandato da Arduino!!!!!!!!
Per ora gli step sono solo:

1.  Creare uno script `Gesture_Detector` scritto in Python usando MediaPipe e OpenCV per la rilevazione dei gesti della mano (palmo aperto, saluto, dito medio, yolo, peace, count numeri). ✅

2.  Robhot costruito in cartone che:
    * risponde ai gesti con piccolo messaggio su schermo LCD; ✅
    * piccolo braccio robotico che saluta! 

3. Creazione dello script `arduino_control`sia come file principale per Arduino IDE che `arduino_control.py` per il gesture detector. ✅

4. Sviluppo dell'applicazione per gestirlo 

5. Brainstorming di idee: radar posizione (con sensore ultrasonico + servo motor); progetto del cazzo; rilevamento del volto (con registrazione tramite applicazione)

## Struttura del progetto

```
Robhot/

   gesture_detector/
     main.py
     camera.py
     hand_detector.py
     gesture_detector.py
     gestures.py
     arduino_control.py
     
   arduino_control/ //frame
      lcd/
         lcd_control.h
         lcd_control.cpp
      servo/
         servo_control.h
         servo_control.cpp
```

## Per le implementazioni future

- Ora la camera preferita è quella del pc (da cambiare successivamente in fase di automazione robhot)

- Ora LCD16 (da cambiare con schermo Oled)


