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

## Fase 5: Node.js diventa il boss della seriale 

Vorrei questo:
Frontend ⇄ WS ⇄ Node (unico owner seriale) ⇄ Serial ⇄ Arduino
Python gesture_detector → (eventi) → Node

### Modificare Python (non usa più seriale)
– Dentro `main.py` invece di chiamare `arduino_control.py` faccio si che il programma stampi su **stdout** gli eventi
    – Esempio: quando riconosce un gesto stampa una riga tipo
    `EV GESTURE WAVE`
    `EV GESTURE OPEN_PALM`

### Node avvia Python e legge le righe 

- Creo file `app/backend/src/gesture_service.js`
- Importo in `index.js`
- Aggiungo una funzione broadcast e avvio il servizio 
Node lancia python, legge quello che stampa, manda al browser (log in realtime) e se è una gesture, la inoltra ad arduino come GESTURE

### Rendo controllabile il gesture service

- Modifico il file `gesture_service.js` per far ritornare anche isRunning e gestire stop bene
- Aggiungo API Start/Stop/Status in `index.js`, adesso Python non parte più da solo!

## Fase 6: miglioro gesture_detector

- Non gli faccio spammare count se non vede nessuna mano 
- Non deve spammare i gesti più di una volta quando li detecta (ancor meglio: bottone che visualizza il gesto per tot tempo che appare)
- Migliorato wave: se lo detecta aspetta 1,5 secondi prima di dirmi "open palm"

Quindi -> **Recap architettura**:
Browser ⇄ WebSocket ⇄ Node ⇄ Serial ⇄ Arduino ⇄ Servo
*Python Gesture ⇄ Node ⇄ Browser

## Fase 7/8: upgrade html 
- fatto carino sito
- ho rotto tutto e sono tornata indietro non mi va di appuntarmi ciò che ho perso.

## Fase 9: Lista spesa

* base con ruoote (la prendo già pronta- kit chassis 2wd)
    * 2 motori DC
    * 2 ruote
    * 1 ruota folle
    * piastra superiore

* Driver motori (compatto)
    - TB6612FNG

* cervello 
    - ESP32 DevKitV1 (x2)

* camera
    - esp32-cam (FTDI USB-TTL)

* schermo testa
    - OLED 0.96” SSD1306 I2C

* audio 
    - microfono: INMP441 (I2S)
    - amplificatore: MAX98357A (I2S)
    - speaker: 8Ω 3W

* braccia
    - SG90 Micro Servo (x2)

* alimentazione
    - 4 x 18650
    - porta batterie 2s
    - bms 2s
    - buck converter LM2596
    - interruttore

* cablaggio
    - kit JST (2pin+3pin)
    - cavo silicone 22awg
    - guaina termorestringente
    - basetta millefori piccola
    - distanziali m3+ viti
    - fascette
    - saldatrice (chat dice saldatore 60w regolabile, punta fine intercambiabile, con supporto + spugnetta)
    - stagno 0.6-0.8mm, con anima flussante (rosin core)
    - teonchesina piccola 
    - pinzette
    - spellafili
    - cacciavite di precisione (m2/m3)
    - multimetro 

* extra
    - pulsanti (power,mode, talk)
    - LED RGB WS2812
    - buzzer passive
    - sensore ultrasuoni HC-SR04

Spesa fatta, 42,48€ da Aliexpress!
+ 11.41€ perchè ho sbagliato e invece di prendere esp32 ho preso due breakout boards :D
= 53,99€
(spoiler, potevo prendere un solo microcontrollore ma vabbe)

