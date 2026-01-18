# config/alert_messages_io.py
import json
from pathlib import Path
from dataclasses import asdict
from .alert_messages import AlertMessages

ALERT_FILE = Path("alert_messages.json")

def save_alert_messages(alerts: AlertMessages):
    with ALERT_FILE.open("w") as f:
        json.dump(asdict(alerts), f, indent=4)

def load_alert_messages() -> AlertMessages:
    if not ALERT_FILE.exists():
        return AlertMessages()
    with ALERT_FILE.open("r") as f:
        data = json.load(f)
    return AlertMessages(**data)
