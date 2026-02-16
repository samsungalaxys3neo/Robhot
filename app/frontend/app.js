window.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("startGesture");
  const stopBtn = document.getElementById("stopGesture");
  const statusEl = document.getElementById("gestureStatus");
  const logEl = document.getElementById("log");

  const badge = document.getElementById("gestureBadge");
  const badgeName = document.getElementById("gestureName");

  const cmdInput = document.getElementById("cmdInput");
  const sendBtn = document.getElementById("sendCmd");

  let badgeTimer = null;

  function log(x) {
    if (!logEl) return;
    logEl.textContent = x + "\n" + logEl.textContent;
  }

  function showGesture(name) {
    if (!badge || !badgeName) return;
    badgeName.textContent = name;
    badge.style.display = "block";
    if (badgeTimer) clearTimeout(badgeTimer);
    badgeTimer = setTimeout(() => {
      badge.style.display = "none";
      badgeName.textContent = "";
    }, 600);
  }

  const wsUrl = `ws://${location.hostname || "localhost"}:3000`;
  const ws = new WebSocket(wsUrl);
  window.ws = ws;

  ws.onopen = () => log("WS OPEN " + wsUrl);
  ws.onclose = () => log("WS CLOSED");
  ws.onerror = () => log("WS ERROR");

  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);

      if (msg.type === "py") {
        const line = msg.line || "";
        if (line.startsWith("EV GESTURE ")) {
          const g = line.slice("EV GESTURE ".length).trim();
          showGesture(g);
        }
        log("PY: " + line);
        return;
      }

      if (msg.type === "gesture") {
        log("SYS: " + msg.status);
        return;
      }

      if (msg.type === "arduino") {
        log("ARDUINO: " + msg.data);
        return;
      }

      log("WS: " + ev.data);
    } catch {
      log("RAW: " + ev.data);
    }
  };

  async function refreshStatus() {
    const r = await fetch("/api/gesture/status");
    const s = await r.json();
    if (statusEl) statusEl.textContent = "Status: " + (s.running ? "running" : "stopped");
  }

  startBtn?.addEventListener("click", async () => {
    await fetch("/api/gesture/start", { method: "POST" });
    refreshStatus();
  });

  stopBtn?.addEventListener("click", async () => {
    await fetch("/api/gesture/stop", { method: "POST" });
    refreshStatus();
  });

  function sendCmd() {
    const v = (cmdInput?.value || "").trim();
    if (!v) return;
    if (ws.readyState !== 1) {
      log("WS not open");
      return;
    }
    ws.send(v);
    log("TX: " + v);
    cmdInput.value = "";
  }

  sendBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    sendCmd();
  });

  cmdInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendCmd();
    }
  });

  refreshStatus();
});
