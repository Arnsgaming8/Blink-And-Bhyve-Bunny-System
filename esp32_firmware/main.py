import network
import urequests
import ujson
import time
import gc

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE) as f:
        return ujson.load(f)

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi:", ssid)
        wlan.connect(ssid, password)
        timeout = 30
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        print("WiFi OK, IP:", wlan.ifconfig()[0])
        return True
    print("WiFi FAILED")
    return False

def poll_sync_module(ip, path):
    url = "http://" + ip + path
    try:
        resp = urequests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            resp.close()
            return data
        resp.close()
    except Exception as e:
        print("Poll error:", e)
    return None

def get_clip_count(data, json_path):
    if json_path == "clips" and isinstance(data, list):
        return len(data)
    if json_path and isinstance(data, dict):
        parts = json_path.split(".")
        val = data
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                return None
        if isinstance(val, list):
            return len(val)
        return val
    return None

def trigger_render(render_url, camera, zone, duration):
    url = render_url.rstrip("/") + "/api/esp32/trigger"
    payload = ujson.dumps({
        "camera": camera,
        "zone": zone,
        "duration": duration
    })
    try:
        resp = urequests.post(url, data=payload, headers={"Content-Type": "application/json"}, timeout=10)
        print("Render response:", resp.status_code)
        resp.close()
    except Exception as e:
        print("Render POST error:", e)

def main():
    config = load_config()
    ssid = config["wifi_ssid"]
    password = config["wifi_password"]
    render_url = config["render_url"]
    poll_interval = config.get("poll_interval_seconds", 3)
    cameras = config.get("cameras", [])

    if not connect_wifi(ssid, password):
        print("Cannot connect to WiFi, restarting...")
        import machine
        machine.reset()

    last_counts = {}
    for cam in cameras:
        last_counts[cam["name"]] = None

    print("Starting poll loop...")
    while True:
        for cam in cameras:
            name = cam["name"]
            ip = cam["sync_module_ip"]
            path = cam.get("poll_url", "/")
            json_path = cam.get("json_path", "")
            zone = cam["zone"]
            duration = cam["duration_seconds"]

            data = poll_sync_module(ip, path)
            if data is None:
                print("  " + name + ": no response")
                continue

            count = get_clip_count(data, json_path)
            prev = last_counts.get(name)
            print("  " + name + ": clips=" + str(count))

            if count is not None and prev is not None and count != prev:
                print("  " + name + ": NEW CLIP! count=" + str(count) + " prev=" + str(prev))
                trigger_render(render_url, name, zone, duration)

            last_counts[name] = count

        time.sleep(poll_interval)
        gc.collect()

main()
