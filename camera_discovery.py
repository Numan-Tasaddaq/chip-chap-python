"""
Camera Discovery and Diagnostic Tool
=====================================

This script helps you:
1. Discover all available cameras on your system
2. Test each camera for GRAB (single frame) and LIVE (continuous) operations
3. Generate a properly configured camera_settings.json file

Run this before configuring your camera_settings.json file.
"""

import cv2
import json
from pathlib import Path
from typing import List, Dict, Optional
import time


class CameraDiscovery:
    """Discover and test available cameras."""

    def __init__(self):
        self.cameras_found = []
        self.test_results = {}

    def discover_cameras(self, max_index: int = 10) -> List[Dict]:
        """
        Scan system for available cameras by testing indices 0-max_index.
        
        Args:
            max_index: Maximum camera index to test (default: 10)
            
        Returns:
            List of discovered camera configurations
        """
        print("\n" + "="*70)
        print("SCANNING FOR AVAILABLE CAMERAS")
        print("="*70)
        
        discovered = []
        
        for idx in range(max_index):
            print(f"\nTesting camera index {idx}...", end=" ", flush=True)
            
            # Try opening with default backend
            cap = cv2.VideoCapture(idx)
            
            if not cap.isOpened():
                print("❌ NOT AVAILABLE")
                cap.release()
                continue
            
            print("✓ FOUND", end=" - ", flush=True)
            
            # Try to read a frame to verify it's actually working
            ret, frame = cap.read()
            
            if not ret:
                print("⚠ Cannot read frames")
                cap.release()
                continue
            
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            camera_info = {
                "cv_index": idx,
                "width": width,
                "height": height,
                "fps": fps,
                "channels": frame.shape[2] if len(frame.shape) == 3 else 1,
                "camera_type": "Color" if frame.shape[2] == 3 else "Mono",
                "status": "working"
            }
            
            print(f"Resolution: {width}x{height} | FPS: {fps} | Type: {camera_info['camera_type']}")
            
            discovered.append(camera_info)
            cap.release()
            
            # Small delay to avoid resource conflicts
            time.sleep(0.1)
        
        self.cameras_found = discovered
        
        if not discovered:
            print("\n⚠ No cameras found! Check USB connections.")
        else:
            print(f"\n✓ Found {len(discovered)} camera(s)")
        
        return discovered

    def test_grab_operation(self, cv_index: int, attempts: int = 3) -> bool:
        """
        Test GRAB operation (single frame capture).
        
        Args:
            cv_index: Camera index to test
            attempts: Number of attempts before giving up
            
        Returns:
            True if GRAB works, False otherwise
        """
        print(f"  Testing GRAB on index {cv_index}...", end=" ", flush=True)
        
        for attempt in range(attempts):
            try:
                cap = cv2.VideoCapture(cv_index)
                
                if not cap.isOpened():
                    cap.release()
                    continue
                
                ret, frame = cap.read()
                cap.release()
                
                if ret and frame is not None:
                    print(f"✓ GRAB OK (attempt {attempt + 1})")
                    return True
                    
            except Exception as e:
                print(f"⚠ Error: {e}")
            
            time.sleep(0.2)
        
        print("❌ GRAB FAILED")
        return False

    def test_live_operation(self, cv_index: int, duration: float = 2.0) -> bool:
        """
        Test LIVE operation (continuous capture for N seconds).
        
        Args:
            cv_index: Camera index to test
            duration: How long to capture in seconds
            
        Returns:
            True if LIVE works, False otherwise
        """
        print(f"  Testing LIVE on index {cv_index}...", end=" ", flush=True)
        
        try:
            cap = cv2.VideoCapture(cv_index)
            
            if not cap.isOpened():
                cap.release()
                print("❌ LIVE FAILED (cannot open)")
                return False
            
            start_time = time.time()
            frame_count = 0
            
            while (time.time() - start_time) < duration:
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    frame_count += 1
                else:
                    cap.release()
                    print("❌ LIVE FAILED (frames dropped)")
                    return False
                
                time.sleep(0.033)  # ~30 FPS
            
            cap.release()
            
            fps = frame_count / duration
            print(f"✓ LIVE OK ({frame_count} frames in {duration}s = {fps:.1f} FPS)")
            return True
            
        except Exception as e:
            print(f"❌ LIVE FAILED ({e})")
            return False

    def test_all_cameras(self):
        """Test GRAB and LIVE on all discovered cameras."""
        
        if not self.cameras_found:
            print("\n⚠ No cameras to test. Run discover_cameras() first.")
            return
        
        print("\n" + "="*70)
        print("TESTING GRAB AND LIVE OPERATIONS")
        print("="*70)
        
        for cam in self.cameras_found:
            idx = cam["cv_index"]
            print(f"\nCamera Index {idx} ({cam['camera_type']}):")
            
            grab_ok = self.test_grab_operation(idx)
            live_ok = self.test_live_operation(idx)
            
            cam["grab_works"] = grab_ok
            cam["live_works"] = live_ok
            cam["fully_working"] = grab_ok and live_ok
        
        return self.cameras_found

    def generate_config_template(self) -> Dict:
        """
        Generate a camera_settings.json template based on discovered cameras.
        
        Returns:
            Dictionary ready to be saved as JSON
        """
        config = {
            "cameras": [],
            "preferred": {
                "index": 0  # Fallback to laptop camera
            }
        }
        
        # Map fully working cameras to stations
        stations = [
            {"station": "TOP", "description": "Top inspection", "model": "USB3CT", "type": 0},
            {"station": "BOTTOM", "description": "Bottom inspection", "model": "USB3CT", "type": 0},
            {"station": "FEED", "description": "Feed", "model": "USB4CT", "type": 1},
            {"station": "PICKUP1", "description": "Pick-up 1", "model": "USB3CT", "type": 0},
            {"station": "PICKUP2", "description": "Pick-up 2", "model": "USB3CT", "type": 0},
            {"station": "BOTTOM_SEAL", "description": "Bottom Sealing", "model": "USB3CT", "type": 0},
            {"station": "TOP_SEAL", "description": "Top Sealing", "model": "USB3CT", "type": 0},
        ]
        
        working_cameras = [cam for cam in self.cameras_found if cam.get("fully_working")]
        
        for i, cam in enumerate(working_cameras):
            doc_index = i + 1
            station_info = stations[i] if i < len(stations) else {"station": f"STATION_{i+1}"}
            
            camera_entry = {
                "doc_index": doc_index,
                "station": station_info.get("station", f"STATION_{i+1}"),
                "description": station_info.get("description", ""),
                "model": station_info.get("model", "USB3CT"),
                "type": station_info.get("type", 0),
                "dshow_name": "",  # Optional: Add DirectShow name if needed
                "index": cam["cv_index"]  # THIS IS THE CORRECT INDEX FOR THIS CAMERA
            }
            
            config["cameras"].append(camera_entry)
        
        return config

    def save_config(self, filename: str = "camera_settings.json"):
        """
        Save the generated configuration to a JSON file.
        
        Args:
            filename: Output filename (default: camera_settings.json)
        """
        config = self.generate_config_template()
        
        filepath = Path(filename)
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n✓ Configuration saved to: {filepath.absolute()}")
        print(f"  Configured {len(config['cameras'])} cameras")
        
        return filepath

    def print_summary(self):
        """Print a summary of all findings."""
        
        print("\n" + "="*70)
        print("CAMERA DISCOVERY SUMMARY")
        print("="*70)
        
        if not self.cameras_found:
            print("\n❌ No cameras found on this system!")
            return
        
        print(f"\nTotal cameras found: {len(self.cameras_found)}\n")
        
        for cam in self.cameras_found:
            print(f"Index {cam['cv_index']}: {cam['camera_type']} camera")
            print(f"  Resolution: {cam['width']}x{cam['height']}")
            print(f"  FPS: {cam['fps']}")
            if "grab_works" in cam:
                grab = "✓" if cam["grab_works"] else "❌"
                live = "✓" if cam["live_works"] else "❌"
                print(f"  GRAB: {grab}  |  LIVE: {live}")
            print()
        
        fully_working = [cam for cam in self.cameras_found if cam.get("fully_working")]
        print(f"Fully working cameras: {len(fully_working)}")
        
        if fully_working:
            print("\nYou can use the following indices in your camera_settings.json:")
            for cam in fully_working:
                print(f"  - Index {cam['cv_index']} ({cam['camera_type']} camera)")


def main():
    """Run the camera discovery tool."""
    
    discovery = CameraDiscovery()
    
    # Step 1: Discover cameras
    discovery.discover_cameras(max_index=10)
    
    # Step 2: Test discovered cameras
    discovery.test_all_cameras()
    
    # Step 3: Print summary
    discovery.print_summary()
    
    # Step 4: Generate and save configuration
    if discovery.cameras_found:
        print("\n" + "="*70)
        response = input("Generate camera_settings.json from discovered cameras? (y/n): ")
        
        if response.lower() == 'y':
            discovery.save_config()
            print("\n✓ Next steps:")
            print("  1. Review the generated camera_settings.json")
            print("  2. Update station names if needed")
            print("  3. Verify indices match your physical camera setup")
            print("  4. Run your application with the new configuration")


if __name__ == "__main__":
    main()
