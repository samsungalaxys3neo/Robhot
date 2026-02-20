const { spawn } = require("child_process");
const path = require("path");

function startGestureService(onLine) {
  const scriptPath = path.join(__dirname, "../../../gesture_control/main.py");

  const proc = spawn("python3", ["-u", scriptPath, "--headless", "--emit-popup-debug"], {
    stdio: ["ignore", "pipe", "pipe"]
  });

  proc.stdout.on("data", (buf) => {
    buf.toString().split("\n").forEach((line) => {
      const s = line.trim();
      if (s) onLine(s);
    });
  });

  proc.stderr.on("data", (buf) => {
    buf.toString().split("\n").forEach((line) => {
      const s = line.trim();
      if (s) onLine("PY_ERR " + s);
    });
  });

  return {
    stop: () => proc.kill("SIGTERM"),
    pid: proc.pid,
    onExit: (cb) => proc.on("exit", cb)
  };
}

module.exports = { startGestureService };
