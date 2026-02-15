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

const PORT = 3000;

app.use(express.json());
app.use(express.static(path.join(__dirname, "../../frontend")));

const serial = new SerialPort({
  path: "/dev/tty.usbmodem1301",
  baudRate: 115200
});

const parser = serial.pipe(new ReadlineParser({ delimiter: "\n" }));

serial.on("open", () => console.log("Seriale connessa ✅"));
serial.on("error", (err) => console.error("Errore seriale:", err.message));

function broadcast(obj) {
  const msg = JSON.stringify(obj);
  wss.clients.forEach((c) => {
    if (c.readyState === WebSocket.OPEN) c.send(msg);
  });
}

parser.on("data", (line) => {
  console.log("Arduino:", line);
  broadcast({ type: "arduino", data: line });
});

wss.on("connection", (ws) => {
  console.log("Browser connesso via WS ✅");

  ws.on("message", (msg) => {
    const s = msg.toString();
    console.log("Dal browser:", s);
    serial.write(s + "\n");
  });
});

// ---- START/STOP GESTURE ----
let gestureProc = null;

app.get("/api/gesture/status", (req, res) => {
  res.json({ running: !!gestureProc, pid: gestureProc ? gestureProc.pid : null });
});

app.post("/api/gesture/start", (req, res) => {
  if (gestureProc) return res.json({ ok: true, running: true, pid: gestureProc.pid });

  gestureProc = startGestureService((line) => {
    console.log("PY:", line);
    broadcast({ type: "py", line });

    if (line.startsWith("EV GESTURE ")) {
      const g = line.slice("EV GESTURE ".length).trim();
      if (g === "count") return;
      serial.write(`GESTURE ${g}\n`);
    }
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
