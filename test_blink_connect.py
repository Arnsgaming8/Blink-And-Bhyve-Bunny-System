"""One-shot Blink connection test — runs connect() once and exits."""
import asyncio
import os
import sys
import traceback

import aiohttp
import yaml

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import state  # needed for state.blink_instance check below
from state import get_config_path
from cameras.blink import BlinkCameraProvider


async def main():
    cfg_path = get_config_path()
    print(f"Reading config from: {cfg_path}")
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f) or {}
    email = cfg.get('blink_email') or ''
    if '@' in email:
        domain = email.split('@', 1)[1]
        masked = f"***@{domain}"
    else:
        masked = '***'
    print(f"Blink email: {masked}")
    print(f"Blink password: {'***set***' if cfg.get('blink_password') else 'MISSING'}")

    pconf = {
        "email": cfg.get("blink_email"),
        "password": cfg.get("blink_password"),
        "motion_interval": cfg.get("motion_interval", 360),
    }
    if not pconf["email"] or not pconf["password"]:
        print("ERROR: blink_email or blink_password missing in config.yml")
        return 1

    async with aiohttp.ClientSession() as session:
        provider = BlinkCameraProvider(pconf, session=session)
        print("\nAttempting Blink connect()...")
        try:
            ok = await asyncio.wait_for(provider.connect(), timeout=45)
        except asyncio.TimeoutError:
            print("RESULT: TIMEOUT — connect() did not finish within 45s")
            return 2
        except Exception as e:
            print(f"RESULT: EXCEPTION — {type(e).__name__}: {e}")
            traceback.print_exc()
            return 3

        if ok and provider.blink:
            n_cams = len(provider.blink.cameras or {})
            n_homes = len(provider.blink.account or [])
            print(f"\nRESULT: CONNECTED ✓")
            print(f"  Homes: {n_homes}")
            print(f"  Cameras seen: {n_cams}")
            for name, cam in (provider.blink.cameras or {}).items():
                print(f"   - {name}")
            return 0

        if state.blink_instance is not None:
            print("\nRESULT: 2FA REQUIRED")
            print("  Blink accepted your credentials but needs a 2FA code.")
            print("  Start the dashboard (python app.py) and enter the code on the 2FA form.")
            return 5

        print("\nRESULT: NOT CONNECTED (no 2FA pending — check credentials or rate-limit)")
        return 4


if __name__ == "__main__":
    rc = asyncio.run(main())
    sys.exit(rc)
