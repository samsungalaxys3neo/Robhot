const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const msgEl = document.getElementById("msg");
const sendBtn = document.getElementById("send");

function log(x) {
  logEl.textContent = x + "\n" + logEl.textContent;
}

const ws = new WebSocket(`ws://${location.hostname}:3000`);

ws.onopen = () => {
  statusEl.textContent = "WS Connected ✅";
  log("WS open");
};

ws.onmessage = (ev) => {
  log("RECV: " + ev.data);
};

ws.onclose = () => {
  statusEl.textContent = "WS Closed ❌";
  log("WS close");
};

sendBtn.onclick = () => {
  const t = msgEl.value.trim();
  if (!t) return;
  ws.send(t);
  log("SEND: " + t);
  msgEl.value = "";
};
