// Polls the Flask API and draws a half-circle radar on the canvas.
const canvas = document.getElementById("radar");
const ctx = canvas.getContext("2d");
const W = canvas.width, H = canvas.height;
const CX = W / 2, CY = H - 20;          // radar origin at bottom centre
const R = Math.min(W / 2, H) - 30;      // radius in pixels
const POLL_MS = 100;
let alertCm = 30;                       // readings closer than the LED threshold show red
let ledSynced = false;                  // fill the LED controls from the server once

const $ = (id) => document.getElementById(id);

// angle 0 = right, 180 = left (as the servo turns)
function polar(angleDeg, radiusPx) {
  const a = (angleDeg * Math.PI) / 180;
  return [CX + radiusPx * Math.cos(a), CY - radiusPx * Math.sin(a)];
}

function drawGrid(maxCm) {
  ctx.strokeStyle = "#1a7a33";
  ctx.fillStyle = "#1a7a33";
  ctx.lineWidth = 1;
  ctx.font = "12px Courier New";

  // range rings
  for (let i = 1; i <= 4; i++) {
    const r = (R * i) / 4;
    ctx.beginPath();
    ctx.arc(CX, CY, r, Math.PI, 2 * Math.PI);
    ctx.stroke();
    ctx.fillText(`${Math.round((maxCm * i) / 4)} cm`, CX + r - 44, CY + 14);
  }
  // angle lines every 30 degrees
  for (let a = 0; a <= 180; a += 30) {
    const [x, y] = polar(a, R);
    ctx.beginPath();
    ctx.moveTo(CX, CY);
    ctx.lineTo(x, y);
    ctx.stroke();
    const [lx, ly] = polar(a, R + 14);
    ctx.fillText(`${a}°`, lx - 10, ly + 4);
  }
}

let lastAngle = 0, direction = 1;

function drawSweep(angle) {
  if (angle !== lastAngle) direction = angle > lastAngle ? 1 : -1;
  lastAngle = angle;

  // fading wedge behind the beam (the trail sits on the side it came from)
  for (let i = 1; i <= 15; i++) {
    const a = angle - direction * i;
    if (a < 0 || a > 180) break;
    const [tx, ty] = polar(a, R);
    ctx.strokeStyle = `rgba(51,255,102,${0.25 * (1 - i / 15)})`;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(CX, CY);
    ctx.lineTo(tx, ty);
    ctx.stroke();
  }

  const [x, y] = polar(angle, R);
  const grad = ctx.createLinearGradient(CX, CY, x, y);
  grad.addColorStop(0, "rgba(51,255,102,0.9)");
  grad.addColorStop(1, "rgba(51,255,102,0.2)");
  ctx.strokeStyle = grad;
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(CX, CY);
  ctx.lineTo(x, y);
  ctx.stroke();
}

function drawPoints(points, maxCm) {
  for (const p of points) {
    if (p.distance >= maxCm) continue;   // nothing detected at this angle
    const [x, y] = polar(p.angle, (p.distance / maxCm) * R);
    ctx.fillStyle = p.distance < alertCm ? "#ff4040" : "#ff9933";
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, 2 * Math.PI);
    ctx.fill();
  }
}

function render(data) {
  alertCm = data.led.threshold;
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, W, H);
  drawGrid(data.max_distance);
  drawPoints(data.points, data.max_distance);
  drawSweep(data.angle);

  $("angle").textContent = `${data.angle}°`;
  const d = data.distance;
  const dEl = $("distance");
  if (d == null || d >= data.max_distance) {
    dEl.textContent = "out of range";
    dEl.classList.remove("alert");
  } else {
    dEl.textContent = `${d} cm`;
    dEl.classList.toggle("alert", d < alertCm);
  }
  $("nearest").textContent = data.nearest
    ? `${data.nearest.distance} cm @ ${data.nearest.angle}°`
    : "none";
  $("status").textContent = data.running ? "scanning" : "stopped";

  $("ledDot").classList.toggle("on", data.led.on);
  $("ledState").textContent = !data.led.enabled ? "disabled" : data.led.on ? "ON: object too close" : "off";
  if (!ledSynced) {
    $("ledEnabled").checked = data.led.enabled;
    $("ledThreshold").value = data.led.threshold;
    $("speed").value = data.step;
    $("speedVal").textContent = data.step;
    ledSynced = true;
  }

  const mode = $("mode");
  mode.textContent = data.simulated ? "SIMULATION" : "LIVE SENSOR";
  mode.classList.toggle("sim", data.simulated);
}

async function poll() {
  try {
    const res = await fetch(`${window.API_BASE}/api/scan`);
    render(await res.json());
  } catch (e) {
    $("status").textContent = "offline";
  }
  setTimeout(poll, POLL_MS);
}

async function control(body) {
  await fetch(`${window.API_BASE}/api/control`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

$("startBtn").onclick = () => control({ action: "start" });
$("stopBtn").onclick = () => control({ action: "stop" });
$("speed").oninput = (e) => {
  $("speedVal").textContent = e.target.value;
  control({ action: "speed", step: Number(e.target.value) });
};

$("ledEnabled").onchange = (e) => control({ action: "led", enabled: e.target.checked });
$("ledThreshold").onchange = (e) => control({ action: "led", threshold: Number(e.target.value) });

poll();
