# config/alert_messages.py
from dataclasses import dataclass, field

@dataclass
class AlertMessages:
    alerts: dict[str, dict[str, int | bool]] = field(default_factory=dict)

    def __post_init__(self):
        # Default alert items and thresholds
        default_items = [
            "Pocket Location", "Package Location", "Alignment",
            "Body Length", "Body Width", "Terminal Length",
            "Terminal Width", "Term To Term", "Body Smear",
            "Body Stain", "Edge Chipoff", "Terminal Pogo",
            "Terminal Incomplete", "Oxidation", "Terminal Chipoff",
            "Terminal Color", "Body Color", "Mark", "Mark Color",
            "Re-Inspect", "Others", "Body Scratch",
            "Peel Termination", "Body Crack", "Fail Yield"
        ]

        for name in default_items:
            if name not in self.alerts:
                self.alerts[name] = {"enabled": False, "threshold": 20}
