"""
Diagnostic script to check MVS SDK and camera detection
"""
import ctypes
from ctypes import c_void_p, c_uint, c_ubyte, c_int, POINTER, Structure, byref

# Device Information Structure
class MV_CC_DEVICE_INFO(Structure):
    _fields_ = [
        ("nMajorVer", c_uint),
        ("nMinorVer", c_uint),
        ("nMacAddrHigh", c_uint),
        ("nMacAddrLow", c_uint),
        ("nTLayerType", c_uint),
        ("Reserved", c_uint * 4),
        ("chSerialNumber", c_ubyte * 16),
        ("chModelName", c_ubyte * 32),
        ("chDeviceVersion", c_ubyte * 32),
        ("chManufacturerName", c_ubyte * 32),
        ("chUserDefinedName", c_ubyte * 32),
        ("SpecialInfo", c_ubyte * 232)
    ]

class MV_CC_DEVICE_INFO_LIST(Structure):
    _fields_ = [
        ("nDeviceNum", c_uint),
        ("pDeviceInfo", POINTER(POINTER(MV_CC_DEVICE_INFO)) * 256)
    ]

print("=" * 70)
print("MVS SDK Diagnostic")
print("=" * 70)

# Step 1: Check DLL
dll_path = r"C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64\MvCameraControl.dll"
print(f"\n[1] Checking DLL at: {dll_path}")
try:
    dll = ctypes.CDLL(dll_path)
    print("    ✅ DLL loaded successfully")
except Exception as e:
    print(f"    ❌ Failed to load DLL: {e}")
    exit(1)

# Step 2: Try to enumerate devices
print("\n[2] Attempting to enumerate devices...")
try:
    dll.MV_CC_EnumDevices.argtypes = [c_uint, POINTER(MV_CC_DEVICE_INFO_LIST)]
    dll.MV_CC_EnumDevices.restype = c_int
    
    device_list = MV_CC_DEVICE_INFO_LIST()
    
    # Try with different device type masks
    masks = [
        (0x00000001, "GigE"),
        (0x00000010, "USB3"),
        (0x00000031, "GigE | USB3 | CameraLink"),
        (0x000000FF, "All types"),
    ]
    
    for mask, name in masks:
        device_list = MV_CC_DEVICE_INFO_LIST()
        ret = dll.MV_CC_EnumDevices(mask, byref(device_list))
        print(f"    Mask 0x{mask:08X} ({name}): ret=0x{ret:08X}, devices={device_list.nDeviceNum}")
        
        if device_list.nDeviceNum > 0:
            print(f"    ✅ Found {device_list.nDeviceNum} device(s)!")
            for i in range(device_list.nDeviceNum):
                try:
                    # Get pointer to device info
                    device_info_ptr = device_list.pDeviceInfo[i]
                    print(f"      Device {i}:")
                    print(f"        Pointer: {device_info_ptr}")
                    
                    # Try to access as the normal structure
                    try:
                        device_info = device_info_ptr.contents
                        print(f"        Structure accessible ✓")
                        
                        # Try each field individually with error handling
                        try:
                            val = device_info.nMajorVer
                            print(f"        nMajorVer: {val}")
                        except:
                            pass
                        
                        try:
                            val = device_info.nTLayerType
                            print(f"        nTLayerType: 0x{val:08X}")
                            
                            # Decode device type
                            device_types = {
                                0x00000000: "Unknown",
                                0x00000001: "GigE",
                                0x00000010: "USB3",
                                0x00000100: "CameraLink",
                                0x00010000: "CoaXPress",
                            }
                            device_type = device_types.get(val, "Custom/Unknown")
                            print(f"        Device Type: {device_type}")
                        except:
                            pass
                            
                        # Try model and serial
                        try:
                            model = bytes(device_info.chModelName).decode('utf-8', errors='ignore').strip('\x00')
                            serial = bytes(device_info.chSerialNumber).decode('utf-8', errors='ignore').strip('\x00')
                            print(f"        Model: {model}, Serial: {serial}")
                        except Exception as e:
                            print(f"        Could not read model/serial: {type(e).__name__}")
                    except Exception as e:
                        print(f"        Error accessing structure: {e}")
                        
                except Exception as e:
                    print(f"      Device {i}: Error - {e}")
    
except Exception as e:
    print(f"    ❌ Enumeration failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
print("""
If no devices found above:
  → Your camera is likely NOT a HIKVision/HikRobot camera
  → It's probably a generic USB3 Vision camera
  → You need a different SDK (check your camera manual)

If devices found:
  → The MVS SDK is working
  → setup_cameras.py should detect them
  → Run: python setup_cameras.py
""")
