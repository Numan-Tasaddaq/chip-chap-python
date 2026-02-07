# inspection/alert_tracker.py
"""
Alert Messages Tracker - Monitors failure rates and triggers alerts
when defect percentages exceed configured thresholds.

Matches old C++ implementation:
- Tracks failure counts per defect type
- Calculates failure percentage (fails / total * 100)
- Shows alert popup when threshold exceeded
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from PySide6.QtWidgets import QMessageBox
from config.alert_messages_io import load_alert_messages


@dataclass
class DefectCounter:
    """Tracks total and fail counts for a specific defect type"""
    total: int = 0
    fails: int = 0
    
    def add_result(self, is_pass: bool):
        """Record inspection result"""
        self.total += 1
        if not is_pass:
            self.fails += 1
    
    def get_failure_rate(self) -> float:
        """Calculate failure percentage (0-100)"""
        if self.total == 0:
            return 0.0
        return (self.fails / self.total) * 100.0
    
    def reset(self):
        """Reset counters"""
        self.total = 0
        self.fails = 0


class AlertTracker:
    """
    Monitors defect failure rates and triggers alerts.
    
    Matches C++ behavior:
    - Increments counters for each inspection
    - Checks if failure rate exceeds threshold
    - Shows MessageBox alert when threshold exceeded
    - Resets counters when acknowledged
    """
    
    # Map Python defect names to alert message keys
    DEFECT_TO_ALERT_MAP = {
        "Pocket Location": "Pocket Location",
        "Package Location": "Package Location",
        "Body Length": "Body Length",
        "Body Width": "Body Width",
        "Terminal Width": "Terminal Width",
        "Terminal Length": "Terminal Length",
        "Term-Term Length": "Term To Term",
        "Body Smear": "Body Smear",
        "Body Stain": "Body Stain",
        "Edge Chipoff": "Edge Chipoff",
        "Terminal Pogo": "Terminal Pogo",
        "Terminal Incomplete": "Terminal Incomplete",
        "Terminal Oxidation": "Oxidation",
        "Terminal Chipoff": "Terminal Chipoff",
        "Terminal Color": "Terminal Color",
        "Body Color": "Body Color",
        "Mark": "Mark",
        "Mark Color": "Mark Color",
        "Body Crack": "Body Crack",
        "Body Scratch": "Body Scratch",
        "Peel Termination": "Peel Termination",
        # Add more mappings as needed
    }
    
    def __init__(self):
        self.counters: Dict[str, DefectCounter] = {}
        self.alerts_config = load_alert_messages()
        self._initialize_counters()
    
    def _initialize_counters(self):
        """Initialize counters for all defect types"""
        for defect_name in self.DEFECT_TO_ALERT_MAP.keys():
            self.counters[defect_name] = DefectCounter()
    
    def reload_config(self):
        """Reload alert configuration from file"""
        self.alerts_config = load_alert_messages()
    
    def record_result(self, defect_name: str, is_pass: bool, parent_widget=None) -> bool:
        """
        Record inspection result and check for alert.
        
        Args:
            defect_name: Name of the defect (e.g., "Body Length")
            is_pass: True if inspection passed, False if failed
            parent_widget: Parent widget for alert dialog
            
        Returns:
            True if alert was triggered, False otherwise
        """
        # Get alert message key
        alert_key = self.DEFECT_TO_ALERT_MAP.get(defect_name)
        if not alert_key:
            return False
        
        # Get counter for this defect
        if defect_name not in self.counters:
            self.counters[defect_name] = DefectCounter()
        
        counter = self.counters[defect_name]
        counter.add_result(is_pass)
        
        # Check if alert is enabled for this defect
        alert_config = self.alerts_config.alerts.get(alert_key)
        if not alert_config or not alert_config.get("enabled", False):
            return False
        
        # Calculate failure rate
        failure_rate = counter.get_failure_rate()
        threshold = alert_config.get("threshold", 20)
        
        # Check if threshold exceeded
        if failure_rate >= threshold:
            self._show_alert(defect_name, failure_rate, threshold, counter, parent_widget)
            return True
        
        return False
    
    def _show_alert(self, defect_name: str, failure_rate: float, threshold: float, 
                    counter: DefectCounter, parent_widget=None):
        """
        Show alert message box (matches C++ MessageBox behavior)
        """
        message = (
            f"⚠️ ALERT: {defect_name}\n\n"
            f"Failure Rate: {failure_rate:.1f}%\n"
            f"Threshold: {threshold:.1f}%\n"
            f"Failed: {counter.fails} / {counter.total}\n\n"
            f"The failure percentage has exceeded the configured alert threshold.\n"
            f"Please check the inspection parameters or device quality."
        )
        
        QMessageBox.warning(
            parent_widget,
            f"Alert Message - {defect_name}",
            message
        )
        
        # Reset counter after alert (matches C++ behavior)
        counter.reset()
        print(f"[ALERT] {defect_name} exceeded threshold - Counter reset")
    
    def reset_counter(self, defect_name: str):
        """Reset counter for a specific defect"""
        if defect_name in self.counters:
            self.counters[defect_name].reset()
    
    def reset_all_counters(self):
        """Reset all defect counters"""
        for counter in self.counters.values():
            counter.reset()
    
    def get_status(self, defect_name: str) -> Optional[tuple[int, int, float]]:
        """
        Get current status for a defect.
        
        Returns:
            Tuple of (total, fails, failure_rate) or None if not tracked
        """
        if defect_name not in self.counters:
            return None
        
        counter = self.counters[defect_name]
        return (counter.total, counter.fails, counter.get_failure_rate())
    
    def get_all_status(self) -> Dict[str, tuple[int, int, float]]:
        """Get status for all tracked defects"""
        status = {}
        for defect_name, counter in self.counters.items():
            status[defect_name] = (counter.total, counter.fails, counter.get_failure_rate())
        return status
