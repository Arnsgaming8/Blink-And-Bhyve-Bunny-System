import os
import asyncio


blink_instance = None
active_blink = None
twofa_pending = False
twofa_pin = None
reauth_in_progress = False
last_poll = None
last_user_arm = {}
handle_2fa_task: "asyncio.Task | None" = None
sprinkler_instances_by_name: dict = {}


# Lazily-created asyncio.Event used to wake the 2FA background handler the
# instant a PIN is submitted (handle_2fa_submit) instead of polling every
# second. Created on first access so the module is safe to import before the
# event loop exists (Python 3.10+ events are lazy-bound).
_twofa_event: "asyncio.Event | None" = None


def get_twofa_event() -> "asyncio.Event":
    """Return the 2FA wake-up event, creating it on first use from inside the running loop."""
    global _twofa_event
    if _twofa_event is None:
        _twofa_event = asyncio.Event()
    return _twofa_event


def get_config_path():
    override = os.environ.get("BABBS_CONFIG_DIR")
    if override:
        return os.path.join(override, "config.yml")
    return os.path.join(os.path.dirname(__file__), "config.yml")
