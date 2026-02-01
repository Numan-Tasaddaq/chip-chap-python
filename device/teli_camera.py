"""
Toshiba Teli USB3 Vision Camera SDK Wrapper
Provides Python interface to TeliCamApi64.dll for camera control
"""

import ctypes
import os
import sys
from ctypes import (
    POINTER, c_void_p, c_char_p, c_char, c_int, c_int64, c_uint, c_uint32, c_uint64,
    c_float, c_double, Structure, byref, create_string_buffer
)
from typing import Optional, Dict, List, Tuple
import numpy as np


# Add SDK directory to DLL search path
SDK_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sdk', 'teli')
if os.path.exists(SDK_DIR):
    os.add_dll_directory(SDK_DIR)


# Teli SDK return codes
CAM_SUCCESS = 0
CAM_API_STS_FAILURE = -1
CAM_API_STS_TIMEOUT = -2
CAM_API_STS_NOT_SUPPORTED = -3


# Camera information structure (based on TeliCamApi.h)
class CAM_INFO(Structure):
    _fields_ = [
        ("szVendorName", c_char * 64),
        ("szModelName", c_char * 64),
        ("szSerialNumber", c_char * 64),
        ("szUserDefinedName", c_char * 64),
        ("szDeviceVersion", c_char * 64),
        ("uiCamType", c_uint32),
    ]

# Image information structure
class CAM_IMAGE_INFO(Structure):
    _fields_ = [
        ("ullTimestamp", c_uint64),
        ("uiPixelFormat", c_uint32),
        ("uiSizeX", c_uint32),
        ("uiSizeY", c_uint32),
        ("uiOffsetX", c_uint32),
        ("uiOffsetY", c_uint32),
        ("uiPaddingX", c_uint32),
        ("ullBlockId", c_uint64),
        ("pvBuf", c_void_p),
        ("uiSize", c_uint32),
        ("ullImageId", c_uint64),
        ("uiStatus", c_int),
    ]


class TeliCamera:
    """Wrapper for Toshiba Teli USB3 Vision Camera SDK"""
    
    def __init__(self):
        self._dll = None
        self._cam_handle = None
        self._strm_handle = None
        self._is_grabbing = False
        self._load_dll()
    
    def _load_dll(self):
        """Load TeliCamApi64.dll and set up function prototypes"""
        try:
            dll_path = os.path.join(SDK_DIR, 'TeliCamApi64.dll')
            if not os.path.exists(dll_path):
                raise FileNotFoundError(f"Teli SDK not found at: {dll_path}")
            
            # Use WinDLL for __stdcall convention
            self._dll = ctypes.WinDLL(dll_path)
            
            # Sys_GetNumOfCameras - Get count of connected cameras
            # CAM_API_STATUS Sys_GetNumOfCameras(uint32_t *puiNum)
            self._dll.Sys_GetNumOfCameras.argtypes = [POINTER(c_uint32)]
            self._dll.Sys_GetNumOfCameras.restype = c_int
            
            # Cam_GetInformation - Get camera information by index
            # CAM_API_STATUS Cam_GetInformation(CAM_HANDLE hCam, uint32_t uiCamIdx, CAM_INFO *psCamInfo)
            # Note: hCam=0 for getting info without opening
            self._dll.Cam_GetInformation.argtypes = [c_uint64, c_uint32, POINTER(CAM_INFO)]
            self._dll.Cam_GetInformation.restype = c_int
            
            # Cam_Open - Open camera by index
            # CAM_API_STATUS Cam_Open(uint32_t uiCamIdx, CAM_HANDLE *phCam, ...)
            self._dll.Cam_Open.argtypes = [c_uint32, POINTER(c_uint64)]
            self._dll.Cam_Open.restype = c_int
            
            # Cam_OpenFromInfo - Open camera by serial number
            # CAM_API_STATUS Cam_OpenFromInfo(const char *pszSerialNo, const char *pszModelName, 
            #                                 const char *pszUserDefinedName, CAM_HANDLE *phCam, ...)
            self._dll.Cam_OpenFromInfo.argtypes = [c_char_p, c_char_p, c_char_p, POINTER(c_uint64)]
            self._dll.Cam_OpenFromInfo.restype = c_int
            
            # Cam_Close - Close camera handle
            # CAM_API_STATUS Cam_Close(CAM_HANDLE hCam)
            self._dll.Cam_Close.argtypes = [c_uint64]
            self._dll.Cam_Close.restype = c_int
            
            # Strm_OpenSimple - Open stream (simplified)
            # CAM_API_STATUS Strm_OpenSimple(CAM_HANDLE hCam, CAM_STRM_HANDLE *phStrm, uint32_t *puiMaxPayloadSize, ...)
            self._dll.Strm_OpenSimple.argtypes = [c_uint64, POINTER(c_uint64), POINTER(c_uint32)]
            self._dll.Strm_OpenSimple.restype = c_int
            
            # Strm_Close - Close stream
            # CAM_API_STATUS Strm_Close(CAM_STRM_HANDLE hStrm)
            self._dll.Strm_Close.argtypes = [c_uint64]
            self._dll.Strm_Close.restype = c_int
            
            # Strm_Start - Start image acquisition
            # CAM_API_STATUS Strm_Start(CAM_STRM_HANDLE hStrm, CAM_ACQ_MODE_TYPE eAcqMode)
            self._dll.Strm_Start.argtypes = [c_uint64, c_int]
            self._dll.Strm_Start.restype = c_int
            
            # Strm_Stop - Stop image acquisition
            # CAM_API_STATUS Strm_Stop(CAM_STRM_HANDLE hStrm)
            self._dll.Strm_Stop.argtypes = [c_uint64]
            self._dll.Strm_Stop.restype = c_int
            
            # Strm_ReadCurrentImage - Read current frame
            # CAM_API_STATUS Strm_ReadCurrentImage(CAM_STRM_HANDLE hStrm, void *pvBuf, uint32_t *puiSize, CAM_IMAGE_INFO *psImageInfo)
            self._dll.Strm_ReadCurrentImage.argtypes = [c_uint64, c_void_p, POINTER(c_uint32), POINTER(CAM_IMAGE_INFO)]
            self._dll.Strm_ReadCurrentImage.restype = c_int
            
            # GetCamWidth - Get image width
            # CAM_API_STATUS GetCamWidth(CAM_HANDLE hCam, uint32_t *puiWidth)
            self._dll.GetCamWidth.argtypes = [c_uint64, POINTER(c_uint32)]
            self._dll.GetCamWidth.restype = c_int
            
            # GetCamHeight - Get image height
            # CAM_API_STATUS GetCamHeight(CAM_HANDLE hCam, uint32_t *puiHeight)
            self._dll.GetCamHeight.argtypes = [c_uint64, POINTER(c_uint32)]
            self._dll.GetCamHeight.restype = c_int
            
            # Nd_GetIntValue - Get integer parameter (GenICam)
            # CAM_API_STATUS Nd_GetIntValue(CAM_HANDLE hCam, const char *szFeatureName, int64_t *piValue)
            self._dll.Nd_GetIntValue.argtypes = [c_uint64, c_char_p, POINTER(c_int64)]
            self._dll.Nd_GetIntValue.restype = c_int
            
            # Nd_SetIntValue - Set integer parameter (GenICam)
            # CAM_API_STATUS Nd_SetIntValue(CAM_HANDLE hCam, const char *szFeatureName, int64_t iValue)
            self._dll.Nd_SetIntValue.argtypes = [c_uint64, c_char_p, c_int64]
            self._dll.Nd_SetIntValue.restype = c_int
            
            # Nd_GetFloatValue - Get float parameter (GenICam)
            # CAM_API_STATUS Nd_GetFloatValue(CAM_HANDLE hCam, const char *szFeatureName, double *pdValue)
            self._dll.Nd_GetFloatValue.argtypes = [c_uint64, c_char_p, POINTER(c_double)]
            self._dll.Nd_GetFloatValue.restype = c_int
            
            # Nd_SetFloatValue - Set float parameter (GenICam)
            # CAM_API_STATUS Nd_SetFloatValue(CAM_HANDLE hCam, const char *szFeatureName, double dValue)
            self._dll.Nd_SetFloatValue.argtypes = [c_uint64, c_char_p, c_double]
            self._dll.Nd_SetFloatValue.restype = c_int
            
            print(f"✓ Teli SDK loaded: {dll_path}")
            
        except Exception as e:
            print(f"✗ Failed to load Teli SDK: {e}")
            raise
    
    def get_camera_count(self) -> int:
        """Get number of connected cameras"""
        count = c_uint32(0)
        ret = self._dll.Sys_GetNumOfCameras(byref(count))
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to get camera count (error: {ret})")
        return count.value
    
    def get_camera_info(self, index: int) -> Dict[str, str]:
        """Get camera information by index"""
        info = CAM_INFO()
        # Call with hCam=0 to get info without opening camera
        ret = self._dll.Cam_GetInformation(0, index, byref(info))
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to get camera info for index {index} (error: {ret})")
        
        return {
            'model': info.szModelName.decode('utf-8').strip('\x00'),
            'serial': info.szSerialNumber.decode('utf-8').strip('\x00'),
            'vendor': info.szVendorName.decode('utf-8').strip('\x00'),
            'user_name': info.szUserDefinedName.decode('utf-8').strip('\x00'),
            'version': info.szDeviceVersion.decode('utf-8').strip('\x00'),
            'camera_type': info.uiCamType
        }
    
    def list_cameras(self) -> List[Dict[str, str]]:
        """List all connected cameras with their information"""
        cameras = []
        count = self.get_camera_count()
        for i in range(count):
            try:
                info = self.get_camera_info(i)
                info['index'] = i
                cameras.append(info)
            except Exception as e:
                print(f"Warning: Could not get info for camera {i}: {e}")
        return cameras
    
    def find_camera_by_serial(self, serial_number: str) -> Optional[int]:
        """Find camera index by serial number"""
        cameras = self.list_cameras()
        for cam in cameras:
            if cam['serial'] == serial_number:
                return cam['index']
        return None
    
    def open(self, index: int):
        """Open camera by index"""
        if self._cam_handle is not None:
            raise RuntimeError("Camera already open")
        
        handle = c_uint64()
        ret = self._dll.Cam_Open(index, byref(handle))
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to open camera at index {index} (error: {ret})")
        
        self._cam_handle = handle.value
        print(f"✓ Camera opened at index {index}")
    
    def open_by_serial(self, serial_number: str):
        """Open camera by serial number (matches old C++ behavior)"""
        if self._cam_handle is not None:
            raise RuntimeError("Camera already open")
        
        handle = c_uint64()
        # Cam_OpenFromInfo(serial, model, user_name, handle)
        # Use NULL for model and user_name to match only by serial
        ret = self._dll.Cam_OpenFromInfo(
            serial_number.encode('utf-8'),
            None,  # Any model
            None,  # Any user name
            byref(handle)
        )
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to open camera with serial '{serial_number}' (error: {ret})")
        
        self._cam_handle = handle.value
        print(f"✓ Camera opened by serial: {serial_number}")
    
    def close(self):
        """Close camera and stream"""
        if self._is_grabbing:
            self.stop_grab()
        
        if self._strm_handle is not None:
            ret = self._dll.Strm_Close(self._strm_handle)
            if ret != CAM_SUCCESS:
                print(f"Warning: Failed to close stream (error: {ret})")
            self._strm_handle = None
        
        if self._cam_handle is not None:
            ret = self._dll.Cam_Close(self._cam_handle)
            if ret != CAM_SUCCESS:
                print(f"Warning: Failed to close camera (error: {ret})")
            self._cam_handle = None
            print("✓ Camera closed")
    
    def start_grab(self):
        """Start image acquisition"""
        if self._cam_handle is None:
            raise RuntimeError("Camera not open")
        
        # Open stream if not already open
        if self._strm_handle is None:
            strm_handle = c_uint64()
            max_payload_size = c_uint32()
            ret = self._dll.Strm_OpenSimple(self._cam_handle, byref(strm_handle), byref(max_payload_size))
            if ret != CAM_SUCCESS:
                raise RuntimeError(f"Failed to open stream (error: {ret})")
            self._strm_handle = strm_handle.value
        
        # Start acquisition (CAM_ACQ_MODE_CONTINUOUS = 8)
        ret = self._dll.Strm_Start(self._strm_handle, 8)
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to start grab (error: {ret})")
        
        self._is_grabbing = True
    
    def stop_grab(self):
        """Stop image acquisition"""
        if self._strm_handle is None or not self._is_grabbing:
            return
        
        ret = self._dll.Strm_Stop(self._strm_handle)
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to stop grab (error: {ret})")
        
        self._is_grabbing = False
    
    def grab_image(self, timeout_ms: int = 1000) -> Optional[np.ndarray]:
        """Grab single image and return as numpy array"""
        if self._cam_handle is None:
            raise RuntimeError("Camera not open")
        
        if not self._is_grabbing:
            raise RuntimeError("Acquisition not started. Call start_grab() first")
        
        # Get image dimensions
        width = c_uint32()
        height = c_uint32()
        ret = self._dll.GetCamWidth(self._cam_handle, byref(width))
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to get width (error: {ret})")
        ret = self._dll.GetCamHeight(self._cam_handle, byref(height))
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to get height (error: {ret})")
        
        w = width.value
        h = height.value
        
        # Allocate buffer (assume Mono8 format, 1 byte per pixel)
        buffer_size = w * h
        buffer = np.zeros(buffer_size, dtype=np.uint8)
        buffer_size_c = c_uint32(buffer_size)
        
        # Image info structure
        img_info = CAM_IMAGE_INFO()
        
        # Read current image
        ret = self._dll.Strm_ReadCurrentImage(
            self._strm_handle,
            buffer.ctypes.data_as(c_void_p),
            byref(buffer_size_c),
            byref(img_info)
        )
        
        if ret == CAM_API_STS_TIMEOUT:
            return None
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to grab image (error: {ret})")
        
        # Reshape to 2D image
        image = buffer.reshape((h, w))
        return image
    
    def get_parameter_int(self, param_name: str) -> int:
        """Get integer parameter via GenICam"""
        if self._cam_handle is None:
            raise RuntimeError("Camera not open")
        
        value = ctypes.c_int64()
        ret = self._dll.Nd_GetIntValue(self._cam_handle, param_name.encode('utf-8'), byref(value))
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to get parameter '{param_name}' (error: {ret})")
        return value.value
    
    def set_parameter_int(self, param_name: str, value: int):
        """Set integer parameter via GenICam"""
        if self._cam_handle is None:
            raise RuntimeError("Camera not open")
        
        ret = self._dll.Nd_SetIntValue(self._cam_handle, param_name.encode('utf-8'), ctypes.c_int64(value))
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to set parameter '{param_name}' to {value} (error: {ret})")
    
    def set_parameter_float(self, param_name: str, value: float):
        """Set float parameter via GenICam"""
        if self._cam_handle is None:
            raise RuntimeError("Camera not open")
        
        ret = self._dll.Nd_SetFloatValue(self._cam_handle, param_name.encode('utf-8'), ctypes.c_double(value))
        if ret != CAM_SUCCESS:
            raise RuntimeError(f"Failed to set parameter '{param_name}' to {value} (error: {ret})")
    
    def apply_settings(self, settings: Dict[str, any]):
        """Apply camera settings from .cam file format"""
        if self._cam_handle is None:
            raise RuntimeError("Camera not open")
        
        try:
            # Exposure time (shutter_1 in microseconds)
            if 'shutter_1' in settings:
                self.set_parameter_float('ExposureTime', float(settings['shutter_1']))
            
            # Gain
            if 'gain' in settings:
                self.set_parameter_float('Gain', float(settings['gain']))
            
            # Brightness (BlackLevel)
            if 'brightness' in settings:
                self.set_parameter_float('BlackLevel', float(settings['brightness']))
            
            # AOI (Region of Interest)
            if all(k in settings for k in ['width', 'height', 'x', 'y']):
                self.set_parameter_int('Width', int(settings['width']))
                self.set_parameter_int('Height', int(settings['height']))
                self.set_parameter_int('OffsetX', int(settings['x']))
                self.set_parameter_int('OffsetY', int(settings['y']))
            
            # Packet size
            if 'BytesPerPacket' in settings:
                try:
                    self.set_parameter_int('GevSCPSPacketSize', int(settings['BytesPerPacket']))
                except:
                    pass  # Not all cameras support this
            
            print("✓ Camera settings applied")
            
        except Exception as e:
            print(f"Warning: Failed to apply some settings: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def test_sdk():
    """Test SDK loading and camera enumeration"""
    print("\n=== Teli Camera SDK Test ===\n")
    
    try:
        teli = TeliCamera()
        print(f"Camera count: {teli.get_camera_count()}")
        
        cameras = teli.list_cameras()
        print(f"\nFound {len(cameras)} camera(s):\n")
        for cam in cameras:
            print(f"  Index {cam['index']}:")
            print(f"    Vendor: {cam['vendor']}")
            print(f"    Model: {cam['model']}")
            print(f"    Serial: {cam['serial']}")
            print(f"    User Name: {cam['user_name']}")
            print(f"    Version: {cam['version']}")
            print(f"    Type: {cam['camera_type']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"✗ SDK test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_sdk()
