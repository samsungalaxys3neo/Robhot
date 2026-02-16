const express = require("express");
const http = require("http");
const WebSocket = require("ws");
const path = require("path");
const { SerialPort } = require("serialport");
const { ReadlineParser } = require("@serialport/parser-readline");
const { startGestureService } = require("./gesture_service");

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

const PORT = Number(process.env.PORT || 3000);
const SERIAL_PATH = process.env.SERIAL_PATH || "/dev/cu.usbmodem1301";
const SERIAL_BAUD = Number(process.env.SERIAL_BAUD || 115200);

app.use(express.json());
app.use(express.static(path.join(__dirname, "../../frontend")));

const serial = new SerialPort({ path: SERIAL_PATH, baudRate: SERIAL_BAUD });
const parser = serial.pipe(new ReadlineParser({ delimiter: "\n" }));

serial.on("open", () => console.log("Seriale connessa ✅", SERIAL_PATH, SERIAL_BAUD));
serial.on("error", (err) => console.error("Errore seriale:", err.message));

function broadcast(obj) {
  const msg = JSON.stringify(obj);
  wss.clients.forEach((c) => {
    if (c.readyState === WebSocket.OPEN) c.send(msg);
  });
}

parser.on("data", (line) => {
  const clean = String(line).replace(/\r/g, "").trim();
  if (!clean) return;
  console.log("RX SERIAL <", clean);
  broadcast({ type: "arduino", data: clean });
});

wss.on("connection", (ws) => {
  console.log("Browser connesso via WS ✅");
  ws.send(JSON.stringify({ type: "gesture", status: "ws_connected" }));

  ws.on("message", (data) => {
    const msg = data.toString().trim();
    if (!msg) return;
    console.log("TX SERIAL >", msg);
    serial.write(msg + "\n");
  });

  ws.on("close", () => {
    console.log("Browser WS disconnesso ❌");
  });
});

let gestureProc = null;

let lastGesture = null;
let lastTriggerTime = 0;
const COOLDOWN_MS = Number(process.env.GESTURE_COOLDOWN_MS || 1000);

const gestureMap = {
  wave: "W\n",
  saluto: "W\n",
  open_hand: "MCiao|Principessa\n",
  fist: "C\n",
};

app.get("/api/gesture/status", (req, res) => {
  res.json({ running: !!gestureProc, pid: gestureProc ? gestureProc.pid : null });
});

app.post("/api/gesture/start", (req, res) => {
  if (gestureProc) return res.json({ ok: true, running: true, pid: gestureProc.pid });

  gestureProc = startGestureService((line) => {
    const clean = String(line).replace(/\r/g, "").trim();
    if (!clean) return;

    console.log("PY:", clean);
    broadcast({ type: "py", line: clean });

    if (!clean.startsWith("EV GESTURE ")) return;

    const g = clean.slice("EV GESTURE ".length).trim();
    if (!g || g === "count") return;

    const now = Date.now();
    if (g === lastGesture && now - lastTriggerTime < COOLDOWN_MS) return;

    lastGesture = g;
    lastTriggerTime = now;

    const cmd = gestureMap[g];
    if (!cmd) {
      console.log("Gesture non mappata:", g);
      return;
    }

    console.log("GESTURE >", g, "-> TX SERIAL >", cmd.trim());
    serial.write(cmd);
  });

  gestureProc.onExit((code) => {
    broadcast({ type: "gesture", status: "stopped", code });
    gestureProc = null;
  });

  broadcast({ type: "gesture", status: "running", pid: gestureProc.pid });
  res.json({ ok: true, running: true, pid: gestureProc.pid });
});

app.post("/api/gesture/stop", (req, res) => {
  if (!gestureProc) return res.json({ ok: true, running: false });
  gestureProc.stop();
  res.json({ ok: true, running: false });
});

server.listen(PORT, () => {
  console.log(`Server attivo su http://localhost:${PORT}`);
});
