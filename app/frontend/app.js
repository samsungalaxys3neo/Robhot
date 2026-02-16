window.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("startGesture");
  const stopBtn = document.getElementById("stopGesture");
  const statusEl = document.getElementById("gestureStatus");
  const logEl = document.getElementById("log");

  const badge = document.getElementById("gestureBadge");
  const badgeName = document.getElementById("gestureName");

  const cmdInput = document.getElementById("cmdInput");
  const sendBtn = document.getElementById("sendCmd");

  const wsPill = document.getElementById("wsPill");
  const clearLogBtn = document.getElementById("clearLog");
  const autoScrollEl = document.getElementById("autoScroll");
  const toastEl = document.getElementById("toast");

  const btnPing = document.getElementById("btnPing");
  const btnHello = document.getElementById("btnHello");

  let badgeTimer = null;
  let ws = null;
  let reconnectTimer = null;
  let reconnectAttempt = 0;

  const WS_PORT = 3000;

  function now() {
    const d = new Date();
    const hh = String(d.getHours()).padStart(2, "0");
    const mm = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");
    return `${hh}:${mm}:${ss}`;
  }

  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.style.display = "block";
    clearTimeout(toastEl.__t);
    toastEl.__t = setTimeout(() => {
      toastEl.style.display = "none";
      toastEl.textContent = "";
    }, 1200);
  }

  function esc(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function pillHtml(label, state, extra = "") {
    const e = esc(extra);
    // determine simple on/off for a colored status dot
    const s = String(state).toLowerCase();
    const isOn = s.includes("open") || s.includes("running") || s.includes("live") || s.includes("connected");
    const dotClass = isOn ? "status-on" : "status-off";
    const dot = `<span class="statusDot ${dotClass}" aria-hidden="true"></span>`;
    return `${dot}<span class="tok tok-typ">${esc(label)}</span><span class="tok tok-op">:</span> ${esc(state)}${e ? ` <span class="tok tok-com">//</span> ${e}` : ""}`;
  }

  function setWsPill(state, extra = "") {
    if (!wsPill) return;
    wsPill.innerHTML = pillHtml("WS", state, extra);
  }

  function setGesturePill(running) {
    if (!statusEl) return;
    statusEl.innerHTML = pillHtml("gesture()", running ? "running" : "stopped");
  }

  function highlight(src) {
    let s = esc(src);

    const rules = [
      [/\b(#include|#import)\b/g, "tok tok-kw"],
      [/\b(import|from|as|def|class|return|async|await|const|let|var|function|new|try|catch|throw)\b/g, "tok tok-kw"],
      [/\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|JOIN|ON|LIMIT)\b/g, "tok tok-kw"],
      [/\b(true|false|null|None)\b/g, "tok tok-num"],
      [/\b([0-9]+)\b/g, "tok tok-num"],
      [/(\"[^\"]*\"|'[^']*')/g, "tok tok-str"],
      [/(&lt;\/?[a-zA-Z][^&]*?&gt;)/g, "tok tok-tag"],
      [/\b(ws|WebSocket|fetch|Arduino|LCD|MOVE)\b/g, "tok tok-typ"],
      [/(\/\/[^\n]*)/g, "tok tok-com"],
      [/(#.*)$/g, "tok tok-com"]
    ];

    for (const [re, cls] of rules) {
      s = s.replace(re, (m) => `<span class="${cls}">${m}</span>`);
    }

    s = s.replace(/([:;=(){}\[\]<>.,])/g, '<span class="tok tok-op">$1</span>');
    return s;
  }

  function log(x, kind = "") {
    if (!logEl) return;
    const t = `<span class="dim">[${now()}]</span>`;
    const prompt = `<span class="prompt">❯</span>`;
    const pipe = `<span class="pipe">│</span>`;

    let k = "";
    if (kind) {
      const map = {
        tx: "tok tok-tx",
        py: "tok tok-py",
        sys: "tok tok-sys",
        arduino: "tok tok-ard",
        ws: "tok tok-ws"
      };
      const cls = map[kind] || "tok";
      k = `<span class="${cls}">${esc(kind.toUpperCase())}</span><span class="tok tok-op">:</span> `;
    }

    const line = `<span class="line">${t} ${prompt} ${pipe} ${k}<span class="typewriter">${highlight(x)}</span></span>`;
    logEl.innerHTML = line + "\n" + logEl.innerHTML;
    if (autoScrollEl?.checked) logEl.scrollTop = 0;
  }

  function showGesture(name) {
    if (!badge || !badgeName) return;
    badgeName.textContent = name;
    badge.style.display = "inline-flex";
    if (badgeTimer) clearTimeout(badgeTimer);
    badgeTimer = setTimeout(() => {
      badge.style.display = "none";
      badgeName.textContent = "";
    }, 650);
  }

  function wsUrl() {
    const host = location.hostname || "localhost";
    return `ws://${host}:${WS_PORT}`;
  }

  function scheduleReconnect() {
    if (reconnectTimer) return;
    reconnectAttempt += 1;
    const delay = Math.min(8000, 500 + reconnectAttempt * 700);
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connectWS();
    }, delay);
  }

  function connectWS() {
    const url = wsUrl();
    setWsPill("connecting", url);

    try {
      ws = new WebSocket(url);
      window.ws = ws;
    } catch {
      setWsPill("error", "bad url");
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      reconnectAttempt = 0;
      setWsPill("open", "live");
      log("WebSocket connected()", "ws");
      log("#include <serial.h>", "ws");
    };

    ws.onclose = () => {
      setWsPill("closed", "reconnecting...");
      log("WS CLOSED", "ws");
      log("// retry()", "ws");
      scheduleReconnect();
    };

    ws.onerror = () => {
      setWsPill("error", "check server");
      log("WS ERROR", "ws");
    };

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);

        if (msg.type === "py") {
          const line = msg.line || "";
          if (line.startsWith("EV GESTURE ")) {
            const g = line.slice("EV GESTURE ".length).trim();
            showGesture(g);
          }
          log(line, "py");
          return;
        }

        if (msg.type === "gesture") {
          log(msg.status, "sys");
          return;
        }

        if (msg.type === "arduino") {
          log(msg.data, "arduino");
          return;
        }

        log(ev.data, "ws");
      } catch {
        log(ev.data, "ws");
      }
    };
  }

  async function refreshStatus() {
    try {
      const r = await fetch("/api/gesture/status", { cache: "no-store" });
      const s = await r.json();
      setGesturePill(!!s.running);
    } catch {
      if (statusEl) statusEl.innerHTML = pillHtml("gesture()", "n/a");
    }
  }

  async function startGesture() {
    try {
      await fetch("/api/gesture/start", { method: "POST" });
      toast("Gesture avviate");
      refreshStatus();
    } catch {
      toast("Errore start");
    }
  }

  async function stopGesture() {
    try {
      await fetch("/api/gesture/stop", { method: "POST" });
      toast("Gesture stoppate");
      refreshStatus();
    } catch {
      toast("Errore stop");
    }
  }

  function sendCmd(value) {
    const v = (value ?? cmdInput?.value ?? "").trim();
    if (!v) return;

    if (!ws || ws.readyState !== 1) {
      log("WS not open", "ws");
      toast("WS non connesso");
      return;
    }

    ws.send(v);
    log(v, "tx");

    if (cmdInput) cmdInput.value = "";
    cmdInput?.focus();
  }

  function runSelfTests() {
    console.assert(esc("<>") === "&lt;&gt;", "esc() should HTML-escape");
    console.assert(highlight("SELECT 1").includes("tok-kw"), "highlight() should tag keywords");
    console.assert(highlight("'x'").includes("tok-str"), "highlight() should tag strings");
    const before = logEl.innerHTML;
    log("SELECT 1", "sys");
    console.assert(logEl.innerHTML !== before, "log() should prepend a line");
  }

  wsPill.innerHTML = pillHtml("WS", "booting");
  statusEl.innerHTML = pillHtml("gesture()", "booting");

  document.body.classList.add("flicker");
  setTimeout(() => document.body.classList.remove("flicker"), 650);

  // shortcut chips removed from UI

  startBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    startGesture();
  });

  stopBtn?.addEventListener("click", (e) => {
    e.preventDefault();
    stopGesture();
  });

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

  clearLogBtn?.addEventListener("click", () => {
    if (!logEl) return;
    logEl.textContent = "";
    toast("Log pulito");
  });

  btnPing?.addEventListener("click", () => sendCmd("PING"));
  btnHello?.addEventListener("click", () => sendCmd("LCD:Hello"));

  document.addEventListener("keydown", (e) => {
    const isMac = navigator.platform.toLowerCase().includes("mac");
    const mod = isMac ? e.metaKey : e.ctrlKey;

    if (mod && e.key.toLowerCase() === "l") {
      e.preventDefault();
      if (logEl) logEl.textContent = "";
      toast("Log pulito");
      return;
    }

    if (mod && e.key.toLowerCase() === "k") {
      e.preventDefault();
      cmdInput?.focus();
      return;
    }

    if (mod && e.key === "Enter") {
      e.preventDefault();
      sendCmd();
      return;
    }

    if (mod && e.key.toLowerCase() === "p") {
      e.preventDefault();
      sendCmd("PING");
      return;
    }

    if (mod && e.key.toLowerCase() === "h") {
      e.preventDefault();
      sendCmd("LCD:Hello");
      return;
    }

    if (mod && e.key.toLowerCase() === "u") {
      e.preventDefault();
      if (autoScrollEl) autoScrollEl.checked = !autoScrollEl.checked;
      toast("Auto-scroll: " + (autoScrollEl?.checked ? "ON" : "OFF"));
      return;
    }

    if (e.key === "Escape") {
      if (cmdInput) cmdInput.value = "";
      cmdInput?.blur();
    }
  });

  connectWS();
  refreshStatus();
  runSelfTests();
});
