// per ora questo file serve ad avviare il server, stampare in console
// che è attivo e prepararci al websocket dopo.

const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const path = require("path");
const { SerialPort } = require("serialport");
const { ReadlineParser } = require("@serialport/parser-readline");

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = 3000;

// ---- SERVE WEB ----
app.use(express.static(path.join(__dirname, "../../frontend")));

// ---- SERIAL SETUP ----
const serial = new SerialPort({
  path: "/dev/tty.usbmodem1301",
  baudRate: 115200
});

const parser = serial.pipe(new ReadlineParser({ delimiter: "\n" }));

serial.on("open", () => {
  console.log("Seriale connessa ✅");
});

serial.on("error", (err) => {
  console.error("Errore seriale:", err.message);
});

// Quando Arduino manda dati
parser.on("data", (line) => {
  console.log("Arduino:", line);

  // Inoltra al browser
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ type: "arduino", data: line }));
    }
  });
});

// ---- WEBSOCKET ----
wss.on("connection", (ws) => {
  console.log("Browser connesso via WS ✅");

  ws.on("message", (msg) => {
    console.log("Dal browser:", msg.toString());

    // Invia ad Arduino
    serial.write(msg.toString() + "\n");
  });
});

server.listen(PORT, () => {
  console.log(`Server attivo su http://localhost:${PORT}`);
});



// in terminale: node src/index.js
// di base sto creando un server http, apro la porta
// 3000 e creo backend locale del robot
// http://localhost:3000/

// aggiornato con ws: 
// 1. browser si collega
// 2. connessione resta aperta
// 3. server può mandare dati quando vuole
// 4. browser può mandare dati quando vuole
// diverso da http che è request/response, ws è full duplex (comunicazione bidirezionale) e realtime (dati in tempo reale)

// aggiorato con serial:
// 1. mi connetto ad arduino tramite seriale
// 2. quando arduino manda dati, li inoltro al browser via ws
// 3. quando il browser manda dati, li inoltro ad arduino via seriale