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
    app/
        backend/
            src/
                index.js
            node_modules/
                ...
            package-lock.json
            package.json
        frontend/
            app.js
            index.html
    .gitignore
    DEVLOG.md
    README.md
```


# RobHot

RobHot è un progetto di robotica modulare basato su Arduino, con componente di visione artificiale in Python e un sistema di controllo via web eseguito in locale su Mac.

Il progetto nasce con l’obiettivo di integrare computer vision, controllo hardware e architettura software scalabile in un unico sistema coerente. L’idea non è costruire solo un robot che funziona, ma costruire un’architettura che possa crescere nel tempo senza dover essere riscritta da zero.

## Obiettivo del progetto

RobHot attualmente:

* rileva gesti della mano tramite MediaPipe e OpenCV

* comunica con Arduino tramite seriale USB

* controlla LCD e servo motor

* espone una dashboard web locale per monitoraggio e gestione

In futuro il sistema verrà migrato verso ESP32 per sostituire la comunicazione USB con Wi-Fi diretto, mantenendo invariata la struttura logica del progetto.

## Architettura generale

L’architettura è divisa in tre livelli principali:

1. Frontend web

2. Backend di controllo (Node.js su Mac)

3. Firmware Arduino

Il flusso dei dati è il seguente:

Browser (frontend) comunica in tempo reale con il backend tramite WebSocket.
Il backend comunica con Arduino tramite seriale USB.
Arduino controlla direttamente l’hardware (LCD, servo, sensori).

Il browser non parla direttamente con Arduino.
Il Mac funge da orchestratore.
Arduino resta un controller hardware semplice e deterministico.

Questa separazione permette di sostituire il livello di trasporto (USB oggi, Wi-Fi con ESP32 domani) senza modificare l’interfaccia o la logica generale.

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
    app/
        backend/
            src/
                index.js
            node_modules/
                ...
            package-lock.json
            package.json
        frontend/
            app.js
            index.html
    .gitignore
    DEVLOG.md
    README.md
```

Il backend serve i file del frontend e mantiene una connessione WebSocket bidirezionale per la comunicazione realtime. In parallelo apre la porta seriale verso Arduino e inoltra i messaggi in entrambe le direzioni.

## Componenti principali

### Gesture Detection
Sistema scritto in Python che utilizza MediaPipe e OpenCV per rilevare gesti della mano e tradurli in comandi inviati ad Arduino.

### Firmware Arduino
Struttura modulare con gestione separata di LCD e servo motor. Riceve comandi via seriale e attiva l’hardware.

### Control Server
Applicazione Node.js che:

* serve la dashboard web su localhost

* mantiene una connessione WebSocket realtime

* fa da ponte tra browser e Arduino tramite seriale

## Stato attuale

* Gesture detection funzionante

* Comunicazione Python ⇄ Arduino via seriale

* Dashboard web locale attiva

* Bridge Web ⇄ Arduino operativo

## Evoluzione prevista

* Implementazione di un protocollo strutturato per comandi ed eventi

* Telemetria in tempo reale (es. radar con sensore ultrasonico)

* Gestione servizi da dashboard (avvio e arresto gesture detector)

* Migrazione a ESP32 per comunicazione Wi-Fi

* Sostituzione LCD con display OLED

* Output vocale

Per il dettaglio tecnico degli step di sviluppo e delle decisioni architetturali, consultare DEVLOG.md.