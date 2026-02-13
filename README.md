# RobHOT Project 

Questo sarà il mio cazzo di robot comandato da Arduino!!!!!!!!
Per ora gli step sono solo:

1.  Creare uno script `Gesture_Detector` scritto in Python usando MediaPipe e OpenCV per la rilevazione dei gesti della mano (palmo aperto, saluto, dito medio, rock n'roll, yolo, numeri).
2.  Robhot costruito in cartone che:
    * risponde ai gesti con sequenze di "BEEEEP" e piccolo messaggio su schermo LED;
    * piccolo braccio robotico che saluta!

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

Per ora: camera preferita quella del pc (da cambiare successivamente in fase di automazione robhot)

