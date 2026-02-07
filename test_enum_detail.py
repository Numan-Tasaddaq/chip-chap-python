"""
Detailed diagnostic - trace enumerate_cameras step by step
"""
import ctypes
from ctypes import c_void_p, c_uint, c_ubyte, c_int, POINTER, Structure, byref
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Structures
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
print("Detailed Camera Enumeration Diagnostic")
print("=" * 70)

DLL_PATH = r"C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64\MvCameraControl.dll"

# Step 1: Load DLL
print(f"\n[1] Loading DLL...")
try:
    dll = ctypes.CDLL(DLL_PATH)
    print("    ✅ DLL loaded")
except Exception as e:
    print(f"    ❌ Failed to load DLL: {e}")
    exit(1)

# Step 2: Define function
print(f"\n[2] Defining MV_CC_EnumDevices...")
try:
    dll.MV_CC_EnumDevices.argtypes = [c_uint, POINTER(MV_CC_DEVICE_INFO_LIST)]
    dll.MV_CC_EnumDevices.restype = c_int
    print("    ✅ Function defined")
except Exception as e:
    print(f"    ❌ Failed: {e}")
    exit(1)

# Step 3: Call with mask 0xFF
print(f"\n[3] Calling MV_CC_EnumDevices(0xFF)...")
device_list = MV_CC_DEVICE_INFO_LIST()
ret = dll.MV_CC_EnumDevices(0x000000FF, byref(device_list))
print(f"    Return code: 0x{ret:08X}")
print(f"    Device count: {device_list.nDeviceNum}")

if ret == 0:
    print("    ✅ Call succeeded")
else:
    print(f"    ⚠️  Return code {ret:08X} (0 = success)")

# Step 4: Iterate devices
print(f"\n[4] Iterating {device_list.nDeviceNum} device(s)...")
for i in range(device_list.nDeviceNum):
    print(f"\n    Device {i}:")
    
    try:
        device_info_ptr = device_list.pDeviceInfo[i]
        print(f"      Pointer: {device_info_ptr}")
        
        if device_info_ptr is None:
            print(f"      ❌ Pointer is NULL")
            continue
            
        device_info = device_info_ptr.contents
        print(f"      ✅ Pointer dereferences")
        
        # Try each field
        try:
            serial_bytes = bytes(device_info.chSerialNumber)
            serial = serial_bytes.decode('utf-8', errors='ignore').strip('\x00')
            print(f"      chSerialNumber: '{serial}' (bytes: {serial_bytes[:16]})")
        except Exception as e:
            print(f"      chSerialNumber: ❌ {type(e).__name__}: {e}")
        
        try:
            model_bytes = bytes(device_info.chModelName)
            model = model_bytes.decode('utf-8', errors='ignore').strip('\x00')
            print(f"      chModelName: '{model}' (bytes: {model_bytes[:16]})")
        except Exception as e:
            print(f"      chModelName: ❌ {type(e).__name__}: {e}")
            
        try:
            ntlayer = device_info.nTLayerType
            print(f"      nTLayerType: 0x{ntlayer:08X}")
        except Exception as e:
            print(f"      nTLayerType: ❌ {type(e).__name__}")
            
    except Exception as e:
        print(f"      ❌ Error iterating device {i}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Now let's test the actual enumerate_cameras() function...")
print("=" * 70)

# Import and test
try:
    from device.mvs_camera import MVSCamera
    print("\n✅ MVSCamera module imported")
    
    cameras = MVSCamera.enumerate_cameras()
    print(f"\nResult: {len(cameras)} camera(s) found")
    for serial, model in cameras:
        print(f"  - {model} (SN: {serial})")
        
except Exception as e:
    print(f"\n❌ Error calling MVSCamera.enumerate_cameras(): {e}")
    import traceback
    traceback.print_exc()
