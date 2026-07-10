# BABBS — Blink → B-hyve Bridge

<p align="left">
  <a href="https://render.com/deploy"><img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render"></a>
</p>

A Python async bridge that detects motion on **Blink cameras** and automatically waters **B-hyve sprinkler** zones. Runs entirely on **Render** (free tier) — no extra hardware needed.

## Supported Providers

| Type | Package | Auth |
|---|---|---|
| **Blink** (camera) | blinkpy 0.25.5 | email + password + 2FA |
| **B-hyve** (sprinkler) | aiohttp (custom Orbit API) | email + password + device ID |

## How it works

```
Blink camera ──(poll every Ns)──> Motion detected?
       │                    │           │ yes
       │                    │           ▼
       │                    │  Look up rule: camera → sprinkler zone
       │                    │           │
       │                    │           ▼
       │                    │  B-hyve start_zone(duration)
       │                    │           │
       │                    │           ▼
       │                    │  Wait, then stop_zone()
       │                    │
  Dashboard UI (http://your-service.onrender.com)
```

## Files

| File | Purpose |
|---|---|
| `bridge.py` | Main daemon — polls Blink, triggers B-hyve with per-zone cooldown |
| `server.py` | Web dashboard — setup form, error log, sidebar, manual watering, 2FA |
| `cameras/blink.py` | Blink camera provider |
| `sprinklers/bhyve.py` | B-hyve sprinkler provider |
| `errors.py` | Shared error logging |
| `state.py` | Shared state |
| `app.py` | Render entry point |
| `config.yml` | Local credentials and settings (gitignored) |
| `render.yaml` | Render Blueprint for one-click deployment |

## Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Click the Deploy to Render button
2. In "Specified configurations" click "Create all as new services"
3. After creation, go to Resources → click your web service
4. Once deployed, open the service URL → the setup form will prompt for credentials

## Local usage

```pwsh
pip install -r requirements.txt
python app.py
# Open http://localhost:5000 → /setup to configure
```

## License

CC BY-NC-SA 4.0
