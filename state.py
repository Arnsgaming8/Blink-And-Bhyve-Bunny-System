import asyncio

blink_instance = None
twofa_event = asyncio.Event()
twofa_pin = None
