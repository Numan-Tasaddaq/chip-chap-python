"""
Pocket Shift Log Manager
Handles storage and retrieval of pocket shift data for quality monitoring.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import asdict


class PocketShiftLogManager:
    """Manages pocket shift log data persistence"""
    
    DEFAULT_LOG_FILE = "pocket_shift_log.json"
    
    def __init__(self, log_file: str = DEFAULT_LOG_FILE):
        self.log_file = log_file
        self.data = self._load_log()
    
    def _load_log(self) -> Dict:
        """Load existing pocket shift log from file"""
        if not os.path.exists(self.log_file):
            return {
                "creation_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "device_count": 0,
                "sessions": [],
                "current_session": None
            }
        
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load pocket shift log: {e}")
            return {
                "creation_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "device_count": 0,
                "sessions": [],
                "current_session": None
            }
    
    def _save_log(self) -> bool:
        """Save pocket shift log to file"""
        try:
            self.data["last_updated"] = datetime.now().isoformat()
            with open(self.log_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save pocket shift log: {e}")
            return False
    
    def start_session(self, session_name: str = None) -> Dict:
        """Start a new pocket shift tracking session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = {
            "id": session_id,
            "name": session_name or session_id,
            "start_time": datetime.now().isoformat(),
            "device_count": 0,
            "measurements": [],
            "alerts": [],
            "status": "active"
        }
        
        self.data["current_session"] = session
        self._save_log()
        
        print(f"[INFO] Pocket shift session started: {session_id}")
        return session
    
    def end_session(self) -> bool:
        """End current pocket shift tracking session"""
        if self.data["current_session"] is None:
            print("[WARN] No active session to end")
            return False
        
        session = self.data["current_session"]
        session["end_time"] = datetime.now().isoformat()
        session["status"] = "completed"
        
        # Add to historical sessions
        self.data["sessions"].append(session)
        self.data["current_session"] = None
        
        print(f"[INFO] Pocket shift session ended: {session['id']}")
        print(f"       Device count: {session['device_count']}")
        print(f"       Alerts: {len(session['alerts'])}")
        
        return self._save_log()
    
    def log_measurement(self, shift_x: float, shift_y: float, 
                       avg_x: float, avg_y: float,
                       tolerance_x: tuple, tolerance_y: tuple,
                       valid: bool = True) -> bool:
        """Log a single pocket shift measurement"""
        if self.data["current_session"] is None:
            print("[WARN] No active session for logging measurement")
            return False
        
        session = self.data["current_session"]
        measurement = {
            "timestamp": datetime.now().isoformat(),
            "device_number": session["device_count"] + 1,
            "shift": {"x": shift_x, "y": shift_y},
            "average": {"x": avg_x, "y": avg_y},
            "tolerance": {
                "x": {"pos": tolerance_x[0], "neg": tolerance_x[1]},
                "y": {"pos": tolerance_y[0], "neg": tolerance_y[1]}
            },
            "valid": valid
        }
        
        session["measurements"].append(measurement)
        session["device_count"] += 1
        self.data["device_count"] += 1
        
        return self._save_log()
    
    def log_alert(self, alert_message: str, severity: str = "warning") -> bool:
        """Log an alert for pocket shift"""
        if self.data["current_session"] is None:
            print("[WARN] No active session for logging alert")
            return False
        
        session = self.data["current_session"]
        alert = {
            "timestamp": datetime.now().isoformat(),
            "device_number": session["device_count"],
            "message": alert_message,
            "severity": severity
        }
        
        session["alerts"].append(alert)
        
        print(f"[ALERT] {alert_message}")
        return self._save_log()
    
    def get_current_session(self) -> Optional[Dict]:
        """Get current session info"""
        return self.data.get("current_session")
    
    def get_session_summary(self, session_id: str = None) -> Optional[Dict]:
        """Get summary of a specific session"""
        if session_id is None:
            session = self.data.get("current_session")
        else:
            # Find session by ID in history
            session = None
            for s in self.data["sessions"]:
                if s["id"] == session_id:
                    session = s
                    break
        
        if session is None:
            return None
        
        return {
            "session_id": session["id"],
            "name": session.get("name", ""),
            "device_count": session["device_count"],
            "alert_count": len(session.get("alerts", [])),
            "status": session.get("status", "unknown"),
            "start_time": session.get("start_time", ""),
            "end_time": session.get("end_time", "")
        }
    
    def get_statistics(self, session_id: str = None) -> Optional[Dict]:
        """Calculate statistics for a session"""
        if session_id is None:
            session = self.data.get("current_session")
        else:
            session = None
            for s in self.data["sessions"]:
                if s["id"] == session_id:
                    session = s
                    break
        
        if session is None or not session.get("measurements"):
            return None
        
        measurements = session["measurements"]
        shifts_x = [m["shift"]["x"] for m in measurements]
        shifts_y = [m["shift"]["y"] for m in measurements]
        
        return {
            "device_count": len(measurements),
            "shift_x": {
                "min": min(shifts_x),
                "max": max(shifts_x),
                "mean": sum(shifts_x) / len(shifts_x),
                "std_dev": self._calc_std_dev(shifts_x)
            },
            "shift_y": {
                "min": min(shifts_y),
                "max": max(shifts_y),
                "mean": sum(shifts_y) / len(shifts_y),
                "std_dev": self._calc_std_dev(shifts_y)
            },
            "alert_count": len(session.get("alerts", []))
        }
    
    @staticmethod
    def _calc_std_dev(values: List[float]) -> float:
        """Calculate standard deviation"""
        if not values or len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def export_session(self, session_id: str = None, output_file: str = None) -> bool:
        """Export session data to CSV or JSON file"""
        if session_id is None:
            session = self.data.get("current_session")
            if session is None:
                print("[ERROR] No active session to export")
                return False
            session_id = session["id"]
        else:
            session = None
            for s in self.data["sessions"]:
                if s["id"] == session_id:
                    session = s
                    break
        
        if session is None:
            print(f"[ERROR] Session {session_id} not found")
            return False
        
        if output_file is None:
            output_file = f"pocket_shift_log_{session_id}.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(session, f, indent=2)
            print(f"[INFO] Session exported to {output_file}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to export session: {e}")
            return False


# Global instance
_shift_log_manager = None


def get_shift_log_manager(log_file: str = PocketShiftLogManager.DEFAULT_LOG_FILE) -> PocketShiftLogManager:
    """Get or create global shift log manager instance"""
    global _shift_log_manager
    if _shift_log_manager is None:
        _shift_log_manager = PocketShiftLogManager(log_file)
    return _shift_log_manager


def start_pocket_shift_session(session_name: str = None) -> Dict:
    """Start a new pocket shift tracking session"""
    manager = get_shift_log_manager()
    return manager.start_session(session_name)


def end_pocket_shift_session() -> bool:
    """End current pocket shift tracking session"""
    manager = get_shift_log_manager()
    return manager.end_session()


def log_pocket_shift(shift_x: float, shift_y: float,
                     avg_x: float, avg_y: float,
                     tolerance_x: tuple, tolerance_y: tuple,
                     valid: bool = True) -> bool:
    """Log a pocket shift measurement"""
    manager = get_shift_log_manager()
    return manager.log_measurement(shift_x, shift_y, avg_x, avg_y, 
                                   tolerance_x, tolerance_y, valid)


def log_pocket_shift_alert(alert_message: str, severity: str = "warning") -> bool:
    """Log a pocket shift alert"""
    manager = get_shift_log_manager()
    return manager.log_alert(alert_message, severity)
