# RobHOT Project 

Questo sarà il mio cazzo di robot comandato da Arduino!!!!!!!!
Per ora gli step sono solo:

1.  Creare uno script `Gesture_Detector` scritto in Python usando MediaPipe e OpenCV per la rilevazione dei gesti della mano (palmo aperto, saluto, dito medio, rock n'roll, yolo, numeri). ✅

2.  Robhot costruito in cartone che:
    * risponde ai gesti con sequenze di "BEEEEP" e piccolo messaggio su schermo LED;
    * piccolo braccio robotico che saluta! 

3. Sviluppo dell'applicazione per gestirlo 

4. Brainstorming di idee: radar posizione (con sensore ultrasonico + servo motor); progetto del cazzo; rilevamento del volto (con registrazione tramite applicazione)

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
     
   arduino_control/
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


