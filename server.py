import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

import aiohttp
import yaml
from aiohttp import web

import errors
import state

try:
    CONFIG = yaml.safe_load(open(state.get_config_path())) or {}
except Exception:
    CONFIG = {}

HOST = CONFIG.get("host", "0.0.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("ERROR_PORT", 5000)))

SETUP_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BABBS Setup</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
.container { width: 100%; max-width: 520px; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 32px; }
h1 { font-size: 1.5rem; color: #f0f6fc; margin-bottom: 4px; }
.subtitle { color: #8b949e; margin-bottom: 24px; font-size: 0.9rem; }
.form-row { margin-bottom: 16px; }
label { display: block; font-size: 0.8rem; color: #8b949e; margin-bottom: 4px; font-weight: 500; }
input, select { width: 100%; padding: 10px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 0.9rem; }
input:focus { border-color: #58a6ff; outline: none; box-shadow: 0 0 0 2px #58a6ff20; }
.hint { font-size: 0.75rem; color: #8b949e; margin-top: 4px; }
.hint a { color: #58a6ff; }
.btn { margin-top: 8px; padding: 10px 20px; background: #238636; border: none; border-radius: 6px; color: #fff; font-size: 0.9rem; cursor: pointer; width: 100%; font-weight: 500; }
.btn:hover { background: #2ea043; }
.status { margin-top: 12px; font-size: 0.85rem; text-align: center; padding: 8px; border-radius: 6px; }
.status.info { color: #3fb950; background: #23863610; }
.status.err { color: #f85149; background: #da363310; }
hr { border: none; border-top: 1px solid #21262d; margin: 20px 0; }
.section-title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.8px; color: #8b949e; margin-bottom: 16px; font-weight: 600; }
</style>
</head>
<body>
<div class="container">
  <div class="card">
    <h1>BABBS Setup</h1>
    <p class="subtitle">Connect your Blink cameras and B-hyve sprinkler system.</p>

    <div class="section-title">Blink Account</div>
    <div class="form-row">
      <label>Email</label>
      <input type="email" id="blink_email" value="ajusunaina@gmail.com" required>
    </div>
    <div class="form-row">
      <label>Password</label>
      <input type="password" id="blink_password" required>
    </div>

    <hr>

    <div class="section-title">B-hyve Account</div>
    <div class="form-row">
      <label>Email</label>
      <input type="email" id="bhyve_email" value="ajusunaina@gmail.com" required>
    </div>
    <div class="form-row">
      <label>Password</label>
      <input type="password" id="bhyve_password" required>
    </div>

    <hr>

    <div class="section-title">Sprinkler Setup</div>
    <div class="form-row">
      <label>Device ID</label>
      <input type="text" id="device_id" placeholder="e.g. 607220244f0c161d5a0d1648" required>
      <div class="hint">Run <code>list_devices.py</code> to find your device ID.</div>
    </div>
    <div style="display:flex;gap:12px;">
      <div class="form-row" style="flex:1;">
        <label>Zone Number</label>
        <input type="number" id="zone_number" value="1" min="1">
      </div>
      <div class="form-row" style="flex:1;">
        <label>Duration (seconds)</label>
        <input type="number" id="duration_seconds" value="180" min="1">
      </div>
    </div>
    <div class="form-row">
      <label>Camera Name</label>
      <input type="text" id="camera_name" placeholder="e.g. Back yard">
      <div class="hint">Leave blank to configure cameras later in the dashboard.</div>
    </div>

    <hr>

    <div class="section-title">Advanced</div>
    <div style="display:flex;gap:12px;">
      <div class="form-row" style="flex:1;">
        <label>Poll Interval (seconds)</label>
        <input type="number" id="poll_interval_seconds" value="30" min="5">
      </div>
    </div>
    <div class="form-row">
      <label>Render API Key <span class="hint">(optional)</span></label>
      <input type="password" id="render_api_key" placeholder="Leave blank for local-only">
      <div class="hint">Required to save credentials on Render. Get one from <a href="https://dashboard.render.com" target="_blank" rel="noopener">Render dashboard</a> &rarr; Account &rarr; API Keys.</div>
    </div>

    <button type="submit" class="btn" id="saveBtn">Save &amp; Start</button>
    <div class="status" id="setupStatus"></div>
  </div>
</div>
<script>
document.getElementById("saveBtn").onclick = async () => {
  const ids = ["blink_email","blink_password","bhyve_email","bhyve_password","device_id","zone_number","duration_seconds","camera_name","poll_interval_seconds","render_api_key"];
  const data = {};
  ids.forEach(id => { const el = document.getElementById(id); if (el) data[id] = el.value; });
  const status = document.getElementById("setupStatus");
  status.className = "status";
  status.textContent = "Saving...";
  try {
    const r = await fetch("/api/setup", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data) });
    const d = await r.json();
    if (d.ok) {
      status.textContent = "Saved! Redirecting to dashboard...";
      status.className = "status info";
      setTimeout(() => { location.href = "/"; }, 1500);
    } else {
      status.textContent = "Error: " + (d.error || "unknown");
      status.className = "status err";
    }
  } catch (e) {
    status.textContent = "Network error: " + e.message;
    status.className = "status err";
  }
};
document.addEventListener("keydown", e => { if (e.key === "Enter") document.getElementById("saveBtn").click(); });
</script>
</body>
</html>"""

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BABBS Dashboard</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; min-height: 100vh; }

/* Layout */
.sidebar { width: 300px; background: #161b22; border-right: 1px solid #30363d; padding: 20px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; }
.main { flex: 1; padding: 24px; overflow-y: auto; }

/* Typography */
.app-title { font-size: 1.4rem; font-weight: 700; color: #f0f6fc; letter-spacing: -0.5px; }
.app-subtitle { font-size: 0.75rem; color: #8b949e; margin-top: 2px; }
.section-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.8px; color: #8b949e; margin-bottom: 10px; font-weight: 600; }

/* Cards */
.card { background: #0d1117; border: 1px solid #21262d; border-radius: 8px; padding: 14px; }
.card-title { font-size: 0.8rem; color: #8b949e; margin-bottom: 8px; }

/* Status grid */
.status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.stat { text-align: center; padding: 10px 6px; background: #161b22; border-radius: 6px; }
.stat-value { font-size: 1.1rem; font-weight: 600; color: #f0f6fc; }
.stat-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.5px; color: #8b949e; margin-top: 2px; }
.stat-value.green { color: #3fb950; }
.stat-value.red { color: #f85149; }
.stat-value.yellow { color: #d29922; }
.stat-value.blue { color: #58a6ff; }

/* Forms */
label { display: block; font-size: 0.75rem; color: #8b949e; margin-bottom: 4px; margin-top: 10px; }
input, select { width: 100%; padding: 8px 10px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 0.85rem; }
input:focus { border-color: #58a6ff; outline: none; box-shadow: 0 0 0 2px #58a6ff20; }

/* Buttons */
.btn { padding: 7px 16px; border: none; border-radius: 6px; font-size: 0.8rem; cursor: pointer; font-weight: 500; display: inline-flex; align-items: center; gap: 4px; }
.btn-primary { background: #238636; color: #fff; }
.btn-primary:hover { background: #2ea043; }
.btn-danger { background: #da3633; color: #fff; }
.btn-danger:hover { background: #f85149; }
.btn-outline { background: transparent; color: #c9d1d9; border: 1px solid #30363d; }
.btn-outline:hover { border-color: #8b949e; }
.btn-sm { padding: 4px 10px; font-size: 0.75rem; }
.btn-group { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }

/* Badges */
.badge { display: inline-flex; align-items: center; gap: 3px; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; }
.badge-green { background: #23863620; color: #3fb950; border: 1px solid #3fb950; }
.badge-red { background: #da363320; color: #f85149; border: 1px solid #f85149; }
.badge-yellow { background: #d2992220; color: #d29922; border: 1px solid #d29922; }

/* Cameras */
.camera-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #21262d; }
.camera-row:last-child { border-bottom: none; }
.camera-info { display: flex; flex-direction: column; gap: 2px; }
.camera-name { font-weight: 500; font-size: 0.9rem; }
.camera-zone { color: #8b949e; font-size: 0.75rem; }
.camera-controls { display: flex; gap: 6px; align-items: center; }

/* Errors */
.error-entry { padding: 8px 0; border-bottom: 1px solid #21262d; display: flex; gap: 8px; align-items: flex-start; }
.error-entry:last-child { border-bottom: none; }
.error-content { flex: 1; min-width: 0; }
.error-time { color: #8b949e; font-size: 0.7rem; }
.error-source { color: #58a6ff; font-weight: 500; font-size: 0.75rem; }
.error-msg { color: #c9d1d9; font-size: 0.8rem; word-break: break-word; margin-top: 2px; }
.error-del { cursor: pointer; color: #484f58; font-size: 0.8rem; padding: 2px 4px; border-radius: 4px; flex-shrink: 0; }
.error-del:hover { color: #f85149; background: #da363320; }
#errorList { max-height: 500px; overflow-y: auto; }

/* 2FA */
.twofa-row { display: flex; gap: 6px; }
.twofa-row input { flex: 1; }
.twofa-status { margin-top: 6px; font-size: 0.8rem; }

/* Utility */
.mt-8 { margin-top: 8px; }
.mt-12 { margin-top: 12px; }
.text-muted { color: #8b949e; font-size: 0.8rem; }
.text-sm { font-size: 0.75rem; }
</style>
</head>
<body>
<div class="sidebar">
  <div>
    <div class="app-title">BABBS</div>
    <div class="app-subtitle">Blink &rarr; B-hyve Bridge</div>
  </div>

  <div>
    <div class="section-label">System Status</div>
    <div class="card">
      <div class="status-grid">
        <div class="stat">
          <div class="stat-value" id="statBridge">-</div>
          <div class="stat-label">Bridge</div>
        </div>
        <div class="stat">
          <div class="stat-value" id="statCameras">-</div>
          <div class="stat-label">Cameras</div>
        </div>
        <div class="stat">
          <div class="stat-value" id="statWater">-</div>
          <div class="stat-label">Water</div>
        </div>
        <div class="stat">
          <div class="stat-value" id="statErrors">0</div>
          <div class="stat-label">Errors</div>
        </div>
      </div>
      <div class="mt-8 text-sm text-muted">Last poll: <span id="lastPoll">-</span></div>
    </div>
  </div>

  <div>
    <div class="section-label">Cameras</div>
    <div class="card" id="cameraList">
      <div class="text-muted text-sm">Loading...</div>
    </div>
  </div>

  <div>
    <div class="section-label">Two-Factor Auth</div>
    <div class="card">
      <div class="twofa-row">
        <input type="text" id="twofaInput" placeholder="6-digit code">
        <button class="btn btn-primary btn-sm" onclick="submit2FA()">Send</button>
      </div>
      <div class="btn-group">
        <button class="btn btn-outline btn-sm" onclick="resend2FA()">Resend Code</button>
      </div>
      <div class="twofa-status text-muted mt-8" id="twofaStatus"></div>
    </div>
  </div>

  <div>
    <div class="section-label">Manual Watering</div>
    <div class="card">
      <div style="display:flex;gap:8px;align-items:end;">
        <div style="flex:1">
          <label>Zone</label>
          <input type="number" id="manualZone" value="1" min="1">
        </div>
        <div style="flex:1">
          <label>Duration (s)</label>
          <input type="number" id="manualDuration" value="60" min="1">
        </div>
      </div>
      <button class="btn btn-primary mt-8" onclick="manualWater()" style="width:100%">Start Watering</button>
      <div class="text-sm text-muted mt-8" id="manualStatus"></div>
    </div>
  </div>

  <div>
    <button class="btn btn-danger btn-sm" onclick="clearErrors()" style="width:100%">Clear Error Log</button>
  </div>
</div>

<div class="main">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
    <div class="section-label" style="margin-bottom:0">Error Log</div>
    <span class="text-sm text-muted">Last 50 errors</span>
  </div>
  <div id="errorList" class="card">
    <div class="text-muted text-sm">No errors logged.</div>
  </div>
</div>

<script>
function _nocache() { return "?_=" + Date.now(); }

function setStat(id, text, color) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = "stat-value" + (color ? " " + color : "");
}

async function poll() {
  try {
    const r = await fetch("/api/status" + _nocache());
    const d = await r.json();
    const status = d.status || "Unknown";
    const running = status === "running";
    setStat("statBridge", running ? "Online" : "Offline", running ? "green" : "red");
    setStat("statCameras", d.blink_connected ? "Online" : "Offline", d.blink_connected ? "green" : "red");
    setStat("statWater", d.water_active ? "Active" : "Idle", d.water_active ? "yellow" : "blue");
    setStat("statErrors", d.error_count ?? "?");
    document.getElementById("lastPoll").textContent = d.last_poll ? new Date(d.last_poll).toLocaleString() : "-";
  } catch (e) {
    setStat("statBridge", "Offline", "red");
    setStat("statCameras", "-", "");
  }
}

async function loadCameras() {
  try {
    const r = await fetch("/api/cameras" + _nocache());
    const list = await r.json();
    const el = document.getElementById("cameraList");
    if (list.length === 0) {
      el.innerHTML = '<div class="text-muted text-sm">No cameras configured.</div>';
      return;
    }
    el.innerHTML = "";
    for (const c of list) {
      const row = document.createElement("div");
      row.className = "camera-row";
      row.innerHTML = `<div class="camera-info">
          <div class="camera-name">${c.name}</div>
          <div class="camera-zone">Zone ${c.zone}</div>
        </div>
        <div class="camera-controls">
          <span class="badge ${c.arm ? 'badge-green' : 'badge-red'}">${c.arm ? 'Armed' : 'Disarmed'}</span>
          <button class="btn btn-outline btn-sm" onclick="toggleArm('${c.name}', ${!c.arm})">${c.arm ? 'Disarm' : 'Arm'}</button>
        </div>`;
      el.appendChild(row);
    }
  } catch (e) {
    document.getElementById("cameraList").innerHTML = '<div class="text-muted text-sm">Failed to load cameras.</div>';
  }
}

async function loadErrors() {
  try {
    const r = await fetch("/api/errors" + _nocache());
    const list = await r.json();
    const el = document.getElementById("errorList");
    el.innerHTML = "";
    if (list.length === 0) {
      el.innerHTML = '<div class="text-muted text-sm">No errors logged.</div>';
      return;
    }
    for (const e of list) {
      const div = document.createElement("div");
      div.className = "error-entry";
      div.innerHTML = `<div class="error-content">
          <div><span class="error-time">${new Date(e.timestamp).toLocaleString()}</span> <span class="error-source">[${e.source}]</span></div>
          <div class="error-msg">${e.message}</div>
        </div>
        <span class="error-del" onclick="deleteError(${e.id})" title="Delete">&times;</span>`;
      el.appendChild(div);
    }
  } catch (e) {}
}

async function toggleArm(name, arm) {
  try {
    await fetch("/api/cameras/arm", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({name, arm}) });
    loadCameras();
  } catch (e) {}
}

async function submit2FA() {
  const pin = document.getElementById("twofaInput").value.trim();
  const status = document.getElementById("twofaStatus");
  if (!pin) { status.textContent = "Enter the code from your email."; status.style.color = "#f85149"; return; }
  status.textContent = "Submitting...";
  status.style.color = "#8b949e";
  try {
    const r = await fetch("/api/blink/2fa", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({pin}) });
    const d = await r.json();
    if (d.ok) {
      status.textContent = "Code submitted, verifying...";
      status.style.color = "#d29922";
    } else {
      status.textContent = "Error: " + (d.error || "unknown");
      status.style.color = "#f85149";
    }
  } catch (e) {
    status.textContent = "Network error: " + e.message;
    status.style.color = "#f85149";
  }
}

async function resend2FA() {
  const status = document.getElementById("twofaStatus");
  status.textContent = "Requesting new code...";
  status.style.color = "#8b949e";
  try {
    const r = await fetch("/api/blink/2fa/resend", { method: "POST" });
    const d = await r.json();
    if (d.ok) {
      status.textContent = "New code sent to your email";
      status.style.color = "#58a6ff";
    } else {
      status.textContent = JSON.stringify(d);
      status.style.color = "#f85149";
    }
  } catch (e) {
    status.textContent = "Network error: " + e.message;
    status.style.color = "#f85149";
  }
}

async function manualWater() {
  const zone = parseInt(document.getElementById("manualZone").value);
  const duration = parseInt(document.getElementById("manualDuration").value);
  const status = document.getElementById("manualStatus");
  status.textContent = "Starting watering...";
  try {
    const r = await fetch("/api/water", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({zone, duration}) });
    const d = await r.json();
    status.textContent = d.message || "Done";
    status.style.color = "#3fb950";
  } catch (e) {
    status.textContent = "Error: " + e.message;
    status.style.color = "#f85149";
  }
}

async function clearErrors() {
  await fetch("/api/clear", { method: "POST" });
  loadErrors();
}

async function deleteError(id) {
  await fetch("/api/errors/delete", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({id}) });
  loadErrors();
}

poll(); loadCameras(); loadErrors();
setInterval(poll, 5000);
setInterval(loadErrors, 5000);
setInterval(loadCameras, 10000);
</script>
</body>
</html>"""


async def handle_index(request):
    cfg = _load_config()
    if not cfg or not cfg.get("bhyve_email"):
        return web.Response(text=SETUP_PAGE, content_type="text/html")
    return web.Response(text=PAGE, content_type="text/html")


def _load_config():
    try:
        return yaml.safe_load(open(state.get_config_path())) or {}
    except Exception:
        return {}


async def handle_setup(request):
    global CONFIG
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid JSON"}, status=400)
    required = ["blink_email", "blink_password", "bhyve_email", "bhyve_password", "device_id"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return web.json_response({"ok": False, "error": f"Missing: {missing}"}, status=400)

    cfg = {
        "bhyve_email": data["bhyve_email"],
        "bhyve_password": data["bhyve_password"],
        "blink_email": data["blink_email"],
        "blink_password": data["blink_password"],
        "device_id": data["device_id"],
        "zone_number": int(data.get("zone_number", 1)),
        "duration_seconds": int(data.get("duration_seconds", 180)),
        "poll_interval_seconds": int(data.get("poll_interval_seconds", 30)),
        "cameras": [],
    }
    camera_name = data.get("camera_name", "").strip()
    if camera_name:
        cfg["cameras"].append({
            "name": camera_name,
            "zone": cfg["zone_number"],
            "duration_seconds": cfg["duration_seconds"],
            "arm": True,
            "no_water": False,
        })
    if data.get("render_api_key"):
        cfg["render_api_key"] = data["render_api_key"]
        os.environ["RENDER_API_KEY"] = data["render_api_key"]
    try:
        with open(state.get_config_path(), "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)
        CONFIG = cfg
        os.environ.pop("SETUP_MODE", None)
        return web.json_response({"ok": True, "message": "Saved to config.yml."})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_status(request):
    error_list = errors.get_errors(1)
    error_count = len(errors.get_errors(999))
    active = getattr(state, "water_active", False)
    bc = state.active_blink is not None and state.active_blink.available
    bhyve_token = getattr(state, "bhyve_token", None)
    return web.json_response({
        "status": "running",
        "error_count": error_count,
        "last_poll": (state.last_poll.isoformat() if hasattr(state.last_poll, "isoformat") else state.last_poll) if state.last_poll else None,
        "poll_interval": 30,
        "water_active": active,
        "blink_connected": bc,
        "bhyve_connected": bhyve_token is not None,
    })


async def handle_errors(request):
    return web.json_response(errors.get_errors(50))


async def handle_clear(request):
    errors.clear_errors()
    return web.json_response({"ok": True})


async def handle_delete_error(request):
    try:
        data = await request.json()
        errors.delete_error(int(data["id"]))
    except Exception:
        pass
    return web.json_response({"ok": True})


async def handle_cameras(request):
    cfg = _load_config()
    cameras = []
    for cam in cfg.get("cameras", []):
        cameras.append({
            "name": cam["name"],
            "zone": cam.get("zone", "?"),
            "arm": cam.get("arm", True),
        })
    return web.json_response(cameras)


async def handle_arm(request):
    try:
        data = await request.json()
        name = data["name"]
        arm = data["arm"]
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid request"}, status=400)
    try:
        with open(state.get_config_path()) as f:
            cfg = yaml.safe_load(f) or {}
        for cam in cfg.get("cameras", []):
            if cam["name"] == name:
                cam["arm"] = arm
                break
        with open(state.get_config_path(), "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_2fa(request):
    try:
        data = await request.json()
        pin = data.get("pin", "").strip()
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid request"}, status=400)
    if not pin:
        return web.json_response({"ok": False, "error": "Pin is required"}, status=400)
    blink = state.blink_instance
    if blink is None:
        return web.json_response({"ok": False, "error": "No pending 2FA request"}, status=400)
    state.twofa_pin = pin
    state.twofa_pending = True
    return web.json_response({"ok": True})


async def handle_2fa_resend(request):
    blink = state.blink_instance
    if blink is None:
        return web.json_response({"ok": False, "error": "No active Blink session"}, status=400)
    try:
        new_blink = Blink(motion_interval=30)
        with open(state.get_config_path()) as f:
            cfg = yaml.safe_load(f) or {}
        auth_data = {
            "username": cfg["blink_email"],
            "password": cfg["blink_password"],
        }
        import json as _json
        raw = os.environ.get("BLINK_AUTH")
        if raw:
            try:
                auth_data.update(_json.loads(raw))
            except _json.JSONDecodeError:
                pass
        from blinkpy.auth import Auth
        async with aiohttp.ClientSession() as session:
            new_blink.auth = Auth(auth_data, session=session)
            try:
                await new_blink.start()
            except Exception:
                pass
            state.blink_instance = new_blink
            return web.json_response({"ok": True, "message": "New code sent. Check your email."})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_2fa_status(request):
    blink = state.blink_instance
    if blink is None:
        return web.json_response({"pending": False, "completed": True})
    try:
        if blink.urls is not None:
            state.blink_instance = None
            state.active_blink = blink
            return web.json_response({"ok": True, "pending": False, "completed": True})
    except Exception:
        pass
    return web.json_response({"pending": state.twofa_pending, "completed": False, "pin_set": state.twofa_pin is not None})


async def handle_water(request):
    try:
        data = await request.json()
        zone = int(data["zone"])
        duration = int(data.get("duration", 60))
    except Exception:
        return web.json_response({"ok": False, "error": "Invalid request"}, status=400)
    blink = state.active_blink
    if blink is None:
        return web.json_response({"ok": False, "error": "Bridge not ready"}, status=400)
    from bridge import BHyveClient
    async with aiohttp.ClientSession() as session:
        bhyve = BHyveClient(session)
        try:
            await bhyve.login()
            state.bhyve_token = bhyve.token
            await bhyve.start_zone(zone, max(duration / 60, 1 / 60))
            state.water_active = True
            asyncio.ensure_future(_stop_after(bhyve, zone, duration))
            return web.json_response({"ok": True, "message": f"Zone {zone} watering for {duration}s"})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=500)


async def _stop_after(bhyve, zone, duration):
    await asyncio.sleep(duration)
    try:
        await bhyve.stop_zone()
    except Exception:
        pass
    state.water_active = False


async def handle_reauth(request):
    blink = state.active_blink
    if blink is None:
        return web.json_response({"ok": False, "error": "Bridge not ready"}, status=400)
    try:
        await blink.start()
        return web.json_response({"ok": True, "message": "Re-authenticated"})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


def create_app():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_post("/api/setup", handle_setup)
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/api/errors", handle_errors)
    app.router.add_post("/api/clear", handle_clear)
    app.router.add_post("/api/errors/delete", handle_delete_error)
    app.router.add_get("/api/cameras", handle_cameras)
    app.router.add_post("/api/cameras/arm", handle_arm)
    app.router.add_post("/api/blink/2fa", handle_2fa)
    app.router.add_post("/api/blink/2fa/resend", handle_2fa_resend)
    app.router.add_get("/api/blink/2fa/status", handle_2fa_status)
    app.router.add_post("/api/water", handle_water)
    app.router.add_post("/api/reauth", handle_reauth)
    return app


async def _start_pinger(app, url):
    async def ping():
        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    await asyncio.sleep(300)
                    try:
                        await session.get(url, timeout=5)
                    except Exception:
                        pass
        except asyncio.CancelledError:
            pass
    app["ping_task"] = asyncio.create_task(ping())


def _maybe_start_pinger(app, url):
    if url:
        asyncio.ensure_future(_start_pinger(app, url))
