# ESP32 Blink Local Poller

MicroPython firmware that polls your Blink Sync Module 2 locally (no cloud API, no rate limits) and triggers watering via Render.

## Architecture

```
ESP32 ──local HTTP──> Blink Sync Module 2 (every 3s)
  │
  └──POST /api/esp32/trigger──> Render (cloud)
                                 └──B-hyve WebSocket watering
```

## Prerequisites

- Xiao ESP32S3 (or any ESP32 with WiFi)
- MicroPython installed on the ESP32
- Blink Sync Module 2 on the same WiFi network
- Render app deployed and running

## Setup

### 1. Install MicroPython on ESP32

Download the latest MicroPython firmware for ESP32S3 from:
https://micropython.org/download/

Flash it using `esptool.py` or Thonny IDE.

### 2. Configure

Edit `config.json`:

```json
{
  "wifi_ssid": "your-home-wifi",
  "wifi_password": "your-wifi-password",
  "render_url": "https://your-app.onrender.com",
  "poll_interval_seconds": 3,
  "cameras": [
    {
      "name": "Patio",
      "sync_module_ip": "192.168.1.100",
      "zone": 7,
      "duration_seconds": 3,
      "poll_url": "/api/v1/accounts/.../local_storage/manifest/request/MANIFEST_ID",
      "json_path": "clips"
    }
  ]
}
```

### 3. Find the Sync Module IP

Methods:
- **Router admin page** — look for "BLINK" or "SyncModule" in DHCP clients
- **Blink app** → Device Settings → Network → shows the local IP
- **mDNS** — `ping blink_sync_module.lan` (if your network supports it)
- **nmap** — `nmap -p 80 192.168.1.0/24` and look for open port 80

### 4. Find the Local Storage API Endpoints

The sync module exposes a local API at:
```
http://<sync-module-ip>/api/v1/accounts/{account_id}/networks/{network_id}/sync_modules/{sync_id}/local_storage/
```

You need `account_id`, `network_id`, and `sync_id`. Get them from:
- Run `blinkpy` locally and print `blink.homescreen` JSON
- Or enable Blink polling on Render briefly and check logs for "Available cameras"

The flow:
1. POST to `/manifest/request` to create a manifest
2. GET `/manifest/request/{request_id}` to get the manifest (contains clip list)
3. Store the manifest ID, compare clip counts on each poll

### 5. Upload to ESP32

Using Thonny IDE (easiest):
1. Open Thonny, select MicroPython (ESP32) interpreter
2. Copy `boot.py`, `main.py`, `config.json` to the device
3. Press Reset — watch the output in the Shell

Or using `ampy`:
```bash
pip install adafruit-ampy
ampy --port COM3 put boot.py
ampy --port COM3 put main.py
ampy --port COM3 put config.json
```

### 6. On Render

Set the `DISABLE_BLINK_POLLING` env var to `1` so the cloud doesn't also poll Blink.

## Debugging

Check the ESP32 serial output for:
- `WiFi OK, IP: 192.168.x.x` — connection successful
- `Patio: clips=5` — current clip count
- `Patio: NEW CLIP!` — motion detected
- `Render response: 200` — trigger sent successfully
