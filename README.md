# BABBS — Blink And Bhyve Bunny System

A Python async bridge that detects motion on **Blink security cameras** and automatically waters **Orbit B-hyve** sprinkler zones. Runs entirely on **Render** (free tier) — no extra hardware needed.

## Features

- **Multi-camera support** — configure any number of Blink cameras, each mapped to a different sprinkler zone with its own duration
- **Dashboard UI** — live error/motion log, sidebar with camera arm/disarm toggles, add/edit/delete cameras
- **Poll countdown badge** — shows seconds until next Blink check
- **2FA handling** — enter Blink verification codes from the dashboard
- **Manual watering** — trigger any zone from the UI (seconds or minutes)
- **ESP32/PIR support** — optional `/api/esp32/trigger` endpoint for external motion detectors (bypasses Blink polling)
- **`DISABLE_BLINK_POLLING` mode** — skip Blink entirely and rely on ESP32 triggers only
- **Render env var persistence** — camera changes made via the UI are saved back to Render environment variables (survives restart)

## How it works

```
Blink cameras ──(poll every 30s)──> New clip detected?
                    │                       │ yes
                    │                       ▼
                    │             Look up camera → zone mapping
                    │                       │
                    │                       ▼
                    │             B-hyve start_zone(duration)
                    │                       │
                    │                       ▼
                    │             Wait for duration, then stop
                    │
               Dashboard UI
          (http://your-service.onrender.com)
```

## Files

| File | Purpose |
|---|---|
| `bridge.py` | Main daemon — polls Blink cameras, triggers B-hyve watering with per-zone cooldown |
| `server.py` | Web dashboard — error log, sidebar with camera controls, modal add/edit/delete, manual watering, 2FA, poll badge |
| `errors.py` | Shared error logging (in-memory on Render) |
| `state.py` | Shared state — Blink instance, 2FA pin, poll timestamps |
| `app.py` | Render entry point — merges env vars into config, runs bridge + dashboard in one process |
| `list_devices.py` | Utility to discover your B-hyve device ID and zones |
| `config.yml` | Local credentials and settings (gitignored — generated from env vars in production) |
| `render.yaml` | Render Blueprint for one-click deployment |

## Local usage

```pwsh
pip install -r requirements.txt
```

1. Copy `config.example.yml` to `config.yml` and fill in your credentials.
2. Run `python list_devices.py` to find your B-hyve device ID and zone numbers.
3. Update `config.yml` with the device ID and camera list.

```pwsh
# Single process — bridge + dashboard together
python app.py

# Or separately:
#   Terminal 1: python bridge.py
#   Terminal 2: python server.py
# Open http://localhost:5000
```

## Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Push this repo to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**.
3. Connect this repo.
4. Fill in the secret environment variables (marked `sync: false` in `render.yaml`):

### Required env vars

| Variable | Description |
|---|---|
| `BLINK_EMAIL` | Blink account email |
| `BLINK_PASSWORD` | Blink account password |
| `BHYVE_EMAIL` | Orbit B-hyve account email |
| `BHYVE_PASSWORD` | Orbit B-hyve account password |
| `DEVICE_ID` | Your B-hyve sprinkler device ID |

### Optional env vars

| Variable | Default | Description |
|---|---|---|
| `CAMERAS` | — | JSON array of camera configs (see below). Overrides `cameras` in config.yml |
| `POLL_INTERVAL_SECONDS` | `30` | How often to check Blink for new clips |
| `DISABLE_BLINK_POLLING` | — | Set to `1` to skip Blink polling (use ESP32 triggers only) |
| `RENDER_API_KEY` | — | Render API key with `env_var_write` scope. When set, camera changes made in the UI persist across restarts |

### `CAMERAS` env var format

```json
[
  {"name": "Front Door", "zone": 1, "duration_seconds": 20},
  {"name": "Back yard",  "zone": 2, "duration_seconds": 30}
]
```

## Config

```yaml
blink_email: "your-blink-email@example.com"
blink_password: "your-blink-password"

bhyve_email: "your-bhyve-email@example.com"
bhyve_password: "your-bhyve-password"
device_id: "find-this-by-running-python-list_devices.py"

poll_interval_seconds: 30

cameras:
  - name: "Front Door"
    zone: 1
    duration_seconds: 20
  - name: "Back yard"
    zone: 2
    duration_seconds: 30
```

## Dashboard

The dashboard at `/` shows:

- **Toolbar** — hamburger sidebar toggle, error count, poll countdown, refresh, clear all
- **Camera sidebar** — toggle arm/disarm per camera, add/edit/delete cameras (name, zone, duration)
- **Manual watering** — send any zone to any sprinkler station (minutes or seconds)
- **Error/motion log** — real-time feed of events with copy and traceback support
- **2FA banner** — appears when Blink requires a verification code

## ESP32 / External Trigger

Send a POST to `/api/esp32/trigger` to trigger watering from an external motion sensor:

```json
{"camera": "Back yard", "zone": 2, "duration": 10}
```

This bypasses Blink polling entirely. Useful with `DISABLE_BLINK_POLLING=1`.

## License

MIT
