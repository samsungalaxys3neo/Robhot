# RobHot - DEV LOG

Questo file contiene tutti gli step del progetto. Che sennò mi rincoglinisco!

## Visione 

Robhot è il mio Robot Hot (perchè è mio) che:
- rileva gesti tramite MediaPipe + OpenCV (Python)
- reagisce mostrando messaggi su LCD
- muove un piccolo braccio robotico
- verrà gestito tramite dashboard web locale
- appena mi arriva passerà a ESP32 per comunicazione Wi-Fi diretta.

L'obiettivo è costruire tutto in modo modulare e scalabile così che alla fine Nicola Tesla mi bacerà.

## Architettura

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

## Fase 1 - Gesture detection 

Ho creato uno script `gesture_detector`in Python usando MediaPipe e OpenCV che rileva i seguenti gesti:
- palmo aperto
- saluto
- dito medio
- yolo
- pace
- count numeri 
Per ora è fin troppo sensibile (sopratutto per il wave), ma sarà un problema futuro. 
Se collego API chatgpt con telecamera probabilmente non sarà necessaria tutta questa manfrina.

## Fase 2 - RobHot fisico

Non l'ho ancora fatto ma vorrei al più presto fare un primo prototipino brutto del cazzo in cartone che:
- mostra messaggi su LCD 16x2 (in teoria sul busto, ma poi con schermo oled farò solo la faccia e i messaggi li dice direttamente a voce).
- piccolo braccio con servo motore che saluta (down).

## Fase 3 - Collegamento Python ⇄ Arduino 

Arduino riceve i comandi via Serial e attiva i moduli.
Per ora la comunicazione seriale avviene via Serial USB (sarà tutto diverso con questo dannato ESP32).
Ho creato:
- `arduino_controller.py` = Python 
- `arduino_control` = Sketch ArduinoIDE

Il serial monitor deve essere chiuso quando usa la porta Node o Python.

## Fase 4 - Web Control Architecture (da Mac)

L'obiettivo è quello di creare una dashboard web locale per:
- servizi
- centealizzare log
- preparare migrazione a ESP32
- visualizzare telemetria in real time 
- ma anche visualizzare da telefono per esempio tutte le funzionalità che implementerò (es. progetto del cazzo)

Per ora il Mac fa da bridge

### Architettura: 

Browser (frontend)
⇅ WebSocket (realtime)
Control Server (Node.js su Mac) 
⇅ Serial USB
Arduino (Firmware)
⇅ Hardware (LCD, servo, sensori)

### Websocket: 
- HTTP è request/response, quindi si chiederebbe le cose ogni volta
- usando WS lo lasciamo aperto e permette push realtime per telemetria eventi e log

### Setup Node.js su Mac:
- installato dal sito ufficiale
- verificato con:  
    - node -v
    - npm - v
- Node serve per il runtime del control server (backend), mentre npm per la gestione dipendenze (ws, serial, express)

### Creazione backend: 
- Situato dentro `Robhot/app/`
- Comandi: 
    - npm init -y
    - npm i express ws serialport
    - npm i @serialport/parses-readline
- File importanti:
    - `package.json` è il dna del backend con dipendenze e config
    - `package-lock.json` blocca le versioni (riproducibilità)
    - `node_modules/` sono librerie installate (messo in .gitignore)

### Creazione frontend: 
- ho creato il frontend (molto basico lol)

### Collegamento Arduino via seriale (bridge vero):
- Arduino collegato via usb al mac tramite porta seriale `/dev/tty.usbmodem1301`
- baud rate -> 115200
- Nota: sempre chiudere serial monitor di arduino (un solo programma alla volta può usare la porta seriale)



