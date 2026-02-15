window.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("startGesture");
  const stopBtn = document.getElementById("stopGesture");
  const statusEl = document.getElementById("gestureStatus");
  const logEl = document.getElementById("log");

  const badge = document.getElementById("gestureBadge");
  const badgeName = document.getElementById("gestureName");

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

  const ws = new WebSocket(`ws://${location.hostname}:3000`);

  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);

      if (msg.type === "py") {
        const line = msg.line || "";

        if (line.startsWith("EV GESTURE ")) {
          const g = line.slice("EV GESTURE ".length).trim();
          showGesture(g);
        }
      } else if (msg.type === "gesture") {
        log("GESTURE STATUS: " + msg.status);
      } else if (msg.type === "arduino") {
        log("ARDUINO: " + msg.data);
      } else {
        log("WS: " + ev.data);
      }
    } catch (e) {
      log("RAW: " + ev.data);
    }
  };

  async function refreshStatus() {
    const r = await fetch("/api/gesture/status");
    const s = await r.json();
    statusEl.textContent = "Status: " + (s.running ? "running" : "stopped");
  }

  startBtn.addEventListener("click", async () => {
    await fetch("/api/gesture/start", { method: "POST" });
    refreshStatus();
  });

  stopBtn.addEventListener("click", async () => {
    await fetch("/api/gesture/stop", { method: "POST" });
    refreshStatus();
  });

  refreshStatus();
});
