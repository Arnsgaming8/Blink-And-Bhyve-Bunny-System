"""One-shot: connect Blink and BHyve using deployed code, print simple OK/PENDING."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aiohttp, yaml
import state
from cameras.blink import BlinkCameraProvider
from sprinklers.bhyve import BHyveSprinkler


async def main():
    with open(state.get_config_path()) as f:
        cfg = yaml.safe_load(f) or {}
    out = {}
    async with aiohttp.ClientSession() as session:
        # Blink
        bl = BlinkCameraProvider(
            {"email": cfg.get("blink_email"), "password": cfg.get("blink_password"),
             "motion_interval": 360}, session=session)
        try:
            ok = await asyncio.wait_for(bl.connect(), timeout=30)
        except Exception as e:
            out["blink"] = f"ERROR: {type(e).__name__}: {e}"
            ok = False
        else:
            bl_state = state.blink_instance
            if ok and bl.blink:
                out["blink"] = f"CONNECTED ({len(bl.blink.cameras or {})} cameras)"
            elif bl_state is not None:
                out["blink"] = "2FA PENDING (credentials accepted, awaiting code)"
            else:
                out["blink"] = "NOT CONNECTED (rejected)"

        # BHyve
        bh = BHyveSprinkler(
            {"email": cfg.get("bhyve_email"), "password": cfg.get("bhyve_password"),
             "device_id": cfg.get("device_id")}, session=session)
        try:
            ok = await asyncio.wait_for(bh.connect(), timeout=20)
        except Exception as e:
            out["bhyve"] = f"ERROR: {type(e).__name__}: {e}"
            ok = False
        if ok and not out.get("bhyve"):
            try:
                await asyncio.wait_for(bh._connect_ws(), timeout=15)
                out["bhyve"] = "CONNECTED (ws open)" if bh.ws and not bh.ws.closed else "WS CLOSED"
            except Exception as e:
                out["bhyve"] = f"WS ERROR: {type(e).__name__}: {e}"
            try:
                await bh.disconnect()
            except Exception:
                pass

    print()
    print(f"Blink : {out.get('blink')}")
    print(f"BHyve : {out.get('bhyve')}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
