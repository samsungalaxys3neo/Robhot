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
  const camPreview = document.getElementById("camPreview");
  const browserCams = document.getElementById("browserCams");
  const serverCams = document.getElementById("serverCams");
  const applyServerCamBtn = document.getElementById("applyServerCam");
  const refreshServerCamsBtn = document.getElementById("refreshServerCams");
  const stopPreviewBtn = document.getElementById("stopPreviewBtn");
  const startPreviewBtn = document.getElementById("startPreviewBtn");

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

  // Camera preview + server camera management
  let currentStream = null;

  async function enumerateBrowserDevices() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return [];
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cams = devices.filter(d => d.kind === 'videoinput');
      browserCams.innerHTML = cams.map(d => `<option value="${d.deviceId}">${d.label || 'Camera ' + d.deviceId}</option>`).join('');
      return cams;
    } catch (err) {
      console.warn('enumerateDevices failed', err);
      return [];
    }
  }

  async function startBrowserPreview(deviceId) {
    try {
      if (currentStream) {
        currentStream.getTracks().forEach(t => t.stop());
        currentStream = null;
      }
      const constraints = { video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: 'user' } };
      currentStream = await navigator.mediaDevices.getUserMedia(constraints);
      camPreview.srcObject = currentStream;
    } catch (err) {
      console.warn('getUserMedia failed', err);
      toast('Permesso camera negato o dispositivo non disponibile');
    }
  }

  function stopBrowserPreview() {
    try {
      if (currentStream) {
        currentStream.getTracks().forEach(t => t.stop());
        currentStream = null;
      }
      if (camPreview) camPreview.srcObject = null;
      toast('Preview fermata');
    } catch (err) {
      console.warn('stopBrowserPreview failed', err);
    }
  }

  async function fetchServerCams() {
    try {
      const r = await fetch('/api/cameras');
      const j = await r.json();
      const cams = j.cameras || [];
      const parts = [];
      if (j.arduino_camera) parts.push({ value: `arduino:${j.arduino_camera}`, label: `Arduino: ${j.arduino_camera}` });
      for (const i of cams) parts.push({ value: String(i), label: `Camera ${i}` });
      serverCams.innerHTML = parts.map(p => `<option value="${p.value}">${p.label}</option>`).join('');
      if (parts.length === 0) serverCams.innerHTML = '<option value="">(no cameras)</option>';
    } catch (err) {
      serverCams.innerHTML = '<option value="">(error)</option>';
    }
  }

  async function applyServerCamera() {
    const val = serverCams?.value;
    if (!val) return toast('Seleziona una camera server valida');
    try {
      const payload = { index: (val.startsWith('arduino:') ? val : Number(val)) };
      const r = await fetch('/api/gesture/select_camera', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const j = await r.json();
      if (j.ok) toast('Camera server impostata: ' + j.value);
      else toast('Errore impostazione camera server');
    } catch (err) {
      toast('Errore impostazione camera server');
    }
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

  // camera UI wiring
  browserCams?.addEventListener('change', () => startBrowserPreview(browserCams.value));
  applyServerCamBtn?.addEventListener('click', () => applyServerCamera());
  refreshServerCamsBtn?.addEventListener('click', () => fetchServerCams());
  stopPreviewBtn?.addEventListener('click', async () => {
    // Attempt to stop server-side detector first so the device is free
    try {
      await fetch('/api/gesture/stop', { method: 'POST' });
    } catch (e) {
      console.warn('Failed to stop gesture service before releasing camera', e);
    }

    // Always stop browser preview immediately
    stopBrowserPreview();

    // If a numeric server camera is selected, poll the server-side camera check
    const selected = serverCams?.value;
    if (selected && !selected.startsWith('arduino:')) {
      const idx = Number(selected);
      const start = performance.now();
      let freed = false;
      // Poll up to 4s for faster release
      while (performance.now() - start < 4000) {
        try {
          const r = await fetch(`/api/camera/check?index=${idx}`, { cache: 'no-store' });
          const j = await r.json();
          if (j.ok) { freed = true; break; }
        } catch (e) {
          // ignore and retry
        }
        await new Promise(res => setTimeout(res, 200));
      }

      if (freed) {
        toast('Preview fermata — camera rilasciata');
      } else {
        toast('Preview fermata — ma camera ancora occupata');
      }
      return;
    }

    // fallback: just notify preview stopped
    toast('Preview fermata');
  });
  startPreviewBtn?.addEventListener('click', () => startBrowserPreview(browserCams?.value));

  // when starting gesture, include selected server camera so Python uses it
  async function startGesture() {
    try {
      // stop browser preview so the camera device is released and its LED turns off
      stopBrowserPreview();

      // if we have a numeric camera selected on the server, wait up to 3s for it to be openable
      const selected = serverCams?.value;
      if (selected && !selected.startsWith('arduino:')) {
        const idx = Number(selected);
        const start = performance.now();
        let ok = false;
        while (performance.now() - start < 3000) {
          try {
            const r = await fetch(`/api/camera/check?index=${idx}`, { cache: 'no-store' });
            const j = await r.json();
            if (j.ok) { ok = true; break; }
          } catch (e) {}
          // wait a short bit before retrying
          await new Promise(res => setTimeout(res, 200));
        }
        if (!ok) {
          toast('Attenzione: la camera server non è ancora libera. Provo comunque ad avviare.');
        }
      }

      const body = {};
      if (serverCams && serverCams.value) body.camera = (serverCams.value.startsWith('arduino:') ? serverCams.value : Number(serverCams.value));
      await fetch("/api/gesture/start", { method: "POST", headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      toast("Gesture avviate");
      refreshStatus();
    } catch {
      toast("Errore start");
    }
  }

  // initialize camera lists and preview
  (async () => {
    await enumerateBrowserDevices();
    // try to softly request permission to get labels (best-effort)
    try { await navigator.mediaDevices.getUserMedia({ video: true }); await enumerateBrowserDevices(); } catch (e) {}
    if (browserCams && browserCams.value) startBrowserPreview(browserCams.value);
    fetchServerCams();
  })();

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
