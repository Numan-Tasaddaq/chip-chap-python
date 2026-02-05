"""
HIKVision MVS Camera SDK Interface
Replaces Teli SDK with HIKVision Machine Vision SDK (MVS)
"""
import ctypes
from ctypes import (
    c_void_p, c_int, c_uint, c_bool, c_char_p, c_ubyte,
    POINTER, Structure, byref, create_string_buffer
)
from typing import Optional, List, Tuple
import numpy as np
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)


# MVS Error Codes
class MV_OK:
    """MVS Success Code"""
    SUCCESS = 0x00000000


class MVSErrorCode(IntEnum):
    """MVS Error Codes"""
    MV_E_HANDLE = 0x80000000  # Error or invalid handle
    MV_E_SUPPORT = 0x80000001  # Not supported function
    MV_E_BUFOVER = 0x80000002  # Buffer overflow
    MV_E_CALLORDER = 0x80000003  # Function calling order error
    MV_E_PARAMETER = 0x80000004  # Incorrect parameter
    MV_E_RESOURCE = 0x80000005  # Resource allocation error
    MV_E_NODATA = 0x80000006  # No data
    MV_E_PRECONDITION = 0x80000007  # Precondition error
    MV_E_VERSION = 0x80000008  # Version mismatch
    MV_E_NOENOUGH_BUF = 0x80000009  # Insufficient buffer
    MV_E_UNKNOW = 0x800000FF  # Unknown error


# Pixel Type Definitions
class MVSPixelType(IntEnum):
    """MVS Pixel Format Types"""
    PixelType_Gvsp_Mono8 = 0x01080001
    PixelType_Gvsp_Mono10 = 0x01100003
    PixelType_Gvsp_Mono12 = 0x01100005
    PixelType_Gvsp_RGB8_Packed = 0x02180014
    PixelType_Gvsp_BGR8_Packed = 0x02180015
    PixelType_Gvsp_YUV422_Packed = 0x0210001F
    PixelType_Gvsp_YUV422_YUYV_Packed = 0x02100032
    PixelType_Gvsp_BayerGR8 = 0x01080008
    PixelType_Gvsp_BayerRG8 = 0x01080009
    PixelType_Gvsp_BayerGB8 = 0x0108000A
    PixelType_Gvsp_BayerBG8 = 0x0108000B


# Device Information Structure
class MV_CC_DEVICE_INFO(Structure):
    """Device Information Structure"""
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
    """Device Information List"""
    _fields_ = [
        ("nDeviceNum", c_uint),
        ("pDeviceInfo", POINTER(POINTER(MV_CC_DEVICE_INFO)) * 256)
    ]


# Frame Output Structure
class MV_FRAME_OUT_INFO_EX(Structure):
    """Frame Output Information"""
    _fields_ = [
        ("nWidth", c_uint),
        ("nHeight", c_uint),
        ("enPixelType", c_uint),
        ("nFrameNum", c_uint),
        ("nDevTimeStampHigh", c_uint),
        ("nDevTimeStampLow", c_uint),
        ("nReserved0", c_uint),
        ("nHostTimeStamp", c_uint),
        ("nFrameLen", c_uint),
        ("nLostPacket", c_uint),
        ("nReserved", c_uint * 2)
    ]


class MV_FRAME_OUT(Structure):
    """Frame Output Structure"""
    _fields_ = [
        ("pBufAddr", c_void_p),
        ("stFrameInfo", MV_FRAME_OUT_INFO_EX),
        ("nReserved", c_uint * 16)
    ]


# Image Save Parameters
class MV_SAVE_IMAGE_PARAM_EX(Structure):
    """Image Save Parameters"""
    _fields_ = [
        ("pData", c_void_p),
        ("nDataLen", c_uint),
        ("enPixelType", c_uint),
        ("nWidth", c_uint),
        ("nHeight", c_uint),
        ("pImageBuffer", c_void_p),
        ("nImageLen", c_uint),
        ("nBufferSize", c_uint),
        ("enImageType", c_uint),
        ("nJpgQuality", c_uint),
        ("iMethodValue", c_uint),
        ("nReserved", c_uint * 3)
    ]


class MVSCamera:
    """
    HIKVision MVS Camera Interface
    
    Main SDK DLL: MvCameraControl.dll
    Path: C:\\Program Files (x86)\\Common Files\\MVS\\Runtime\\Win64_x64\\
    """
    
    # DLL Path
    DLL_PATH = r"C:\Program Files (x86)\Common Files\MVS\Runtime\Win64_x64\MvCameraControl.dll"
    
    def __init__(self):
        """Initialize MVS Camera"""
        self.dll: Optional[ctypes.CDLL] = None
        self.handle: Optional[c_void_p] = None
        self.device_info: Optional[MV_CC_DEVICE_INFO] = None
        self.is_grabbing = False
        self._load_dll()
    
    def _load_dll(self):
        """Load MvCameraControl.dll and define function signatures"""
        try:
            self.dll = ctypes.CDLL(self.DLL_PATH)
            logger.info(f"Loaded MVS SDK: {self.DLL_PATH}")
            
            # Define function signatures
            # MV_CC_EnumDevices
            self.dll.MV_CC_EnumDevices.argtypes = [c_uint, POINTER(MV_CC_DEVICE_INFO_LIST)]
            self.dll.MV_CC_EnumDevices.restype = c_int
            
            # MV_CC_CreateHandle
            self.dll.MV_CC_CreateHandle.argtypes = [POINTER(c_void_p), POINTER(MV_CC_DEVICE_INFO)]
            self.dll.MV_CC_CreateHandle.restype = c_int
            
            # MV_CC_DestroyHandle
            self.dll.MV_CC_DestroyHandle.argtypes = [c_void_p]
            self.dll.MV_CC_DestroyHandle.restype = c_int
            
            # MV_CC_OpenDevice
            self.dll.MV_CC_OpenDevice.argtypes = [c_void_p, c_uint, c_uint]
            self.dll.MV_CC_OpenDevice.restype = c_int
            
            # MV_CC_CloseDevice
            self.dll.MV_CC_CloseDevice.argtypes = [c_void_p]
            self.dll.MV_CC_CloseDevice.restype = c_int
            
            # MV_CC_StartGrabbing
            self.dll.MV_CC_StartGrabbing.argtypes = [c_void_p]
            self.dll.MV_CC_StartGrabbing.restype = c_int
            
            # MV_CC_StopGrabbing
            self.dll.MV_CC_StopGrabbing.argtypes = [c_void_p]
            self.dll.MV_CC_StopGrabbing.restype = c_int
            
            # MV_CC_GetOneFrameTimeout
            self.dll.MV_CC_GetOneFrameTimeout.argtypes = [c_void_p, c_void_p, c_uint, POINTER(MV_FRAME_OUT_INFO_EX), c_uint]
            self.dll.MV_CC_GetOneFrameTimeout.restype = c_int
            
            # MV_CC_GetImageInfo
            self.dll.MV_CC_GetImageInfo.argtypes = [c_void_p, POINTER(MV_FRAME_OUT_INFO_EX)]
            self.dll.MV_CC_GetImageInfo.restype = c_int
            
            # MV_CC_SetEnumValue
            self.dll.MV_CC_SetEnumValue.argtypes = [c_void_p, c_char_p, c_uint]
            self.dll.MV_CC_SetEnumValue.restype = c_int
            
            # MV_CC_GetEnumValue
            self.dll.MV_CC_GetEnumValue.argtypes = [c_void_p, c_char_p, POINTER(c_uint)]
            self.dll.MV_CC_GetEnumValue.restype = c_int
            
            # MV_CC_SetIntValue
            self.dll.MV_CC_SetIntValue.argtypes = [c_void_p, c_char_p, c_uint]
            self.dll.MV_CC_SetIntValue.restype = c_int
            
            # MV_CC_GetIntValue
            self.dll.MV_CC_GetIntValue.argtypes = [c_void_p, c_char_p, POINTER(c_uint)]
            self.dll.MV_CC_GetIntValue.restype = c_int
            
            # MV_CC_SetFloatValue
            self.dll.MV_CC_SetFloatValue.argtypes = [c_void_p, c_char_p, ctypes.c_float]
            self.dll.MV_CC_SetFloatValue.restype = c_int
            
            # MV_CC_GetFloatValue
            self.dll.MV_CC_GetFloatValue.argtypes = [c_void_p, c_char_p, POINTER(ctypes.c_float)]
            self.dll.MV_CC_GetFloatValue.restype = c_int
            
            # MV_CC_SetBoolValue
            self.dll.MV_CC_SetBoolValue.argtypes = [c_void_p, c_char_p, c_bool]
            self.dll.MV_CC_SetBoolValue.restype = c_int
            
            # MV_CC_GetBoolValue
            self.dll.MV_CC_GetBoolValue.argtypes = [c_void_p, c_char_p, POINTER(c_bool)]
            self.dll.MV_CC_GetBoolValue.restype = c_int
            
        except Exception as e:
            logger.error(f"Failed to load MVS SDK: {e}")
            raise
    
    @staticmethod
    def enumerate_cameras() -> List[Tuple[str, str]]:
        """
        Enumerate all connected MVS cameras
        
        Returns:
            List of tuples (serial_number, model_name)
        """
        try:
            dll = ctypes.CDLL(MVSCamera.DLL_PATH)
            dll.MV_CC_EnumDevices.argtypes = [c_uint, POINTER(MV_CC_DEVICE_INFO_LIST)]
            dll.MV_CC_EnumDevices.restype = c_int
            
            device_list = MV_CC_DEVICE_INFO_LIST()
            # 0x00000031 = MV_GIGE_DEVICE | MV_USB_DEVICE | MV_CAMERALINK_DEVICE
            ret = dll.MV_CC_EnumDevices(0x00000031, byref(device_list))
            
            if ret != MV_OK.SUCCESS:
                logger.error(f"Enumerate devices failed: 0x{ret:08X}")
                return []
            
            cameras = []
            for i in range(device_list.nDeviceNum):
                device_info_ptr = device_list.pDeviceInfo[i]
                device_info = device_info_ptr.contents
                
                # Extract serial number
                serial = bytes(device_info.chSerialNumber).decode('utf-8', errors='ignore').strip('\x00')
                
                # Extract model name
                model = bytes(device_info.chModelName).decode('utf-8', errors='ignore').strip('\x00')
                
                cameras.append((serial, model))
                logger.info(f"Found camera: {model} (SN: {serial})")
            
            return cameras
            
        except Exception as e:
            logger.error(f"Failed to enumerate cameras: {e}")
            return []
    
    def open_camera(self, serial_number: str) -> bool:
        """
        Open camera by serial number
        
        Args:
            serial_number: Camera serial number
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Enumerate devices
            device_list = MV_CC_DEVICE_INFO_LIST()
            ret = self.dll.MV_CC_EnumDevices(0x00000031, byref(device_list))
            
            if ret != MV_OK.SUCCESS:
                logger.error(f"Enumerate devices failed: 0x{ret:08X}")
                return False
            
            # Find matching device
            target_device = None
            for i in range(device_list.nDeviceNum):
                device_info_ptr = device_list.pDeviceInfo[i]
                device_info = device_info_ptr.contents
                serial = bytes(device_info.chSerialNumber).decode('utf-8', errors='ignore').strip('\x00')
                
                if serial == serial_number:
                    target_device = device_info
                    break
            
            if target_device is None:
                logger.error(f"Camera with serial {serial_number} not found")
                return False
            
            # Create handle
            handle = c_void_p()
            ret = self.dll.MV_CC_CreateHandle(byref(handle), byref(target_device))
            if ret != MV_OK.SUCCESS:
                logger.error(f"Create handle failed: 0x{ret:08X}")
                return False
            
            self.handle = handle
            self.device_info = target_device
            
            # Open device
            ret = self.dll.MV_CC_OpenDevice(self.handle, 0, 0)
            if ret != MV_OK.SUCCESS:
                logger.error(f"Open device failed: 0x{ret:08X}")
                self.dll.MV_CC_DestroyHandle(self.handle)
                self.handle = None
                return False
            
            logger.info(f"Camera {serial_number} opened successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open camera: {e}")
            return False
    
    def close_camera(self):
        """Close camera and release resources"""
        try:
            if self.is_grabbing:
                self.stop_grabbing()
            
            if self.handle is not None:
                self.dll.MV_CC_CloseDevice(self.handle)
                self.dll.MV_CC_DestroyHandle(self.handle)
                self.handle = None
                logger.info("Camera closed")
        except Exception as e:
            logger.error(f"Failed to close camera: {e}")
    
    def start_grabbing(self) -> bool:
        """
        Start image acquisition
        
        Returns:
            True if successful, False otherwise
        """
        if self.handle is None:
            logger.error("Camera not opened")
            return False
        
        try:
            ret = self.dll.MV_CC_StartGrabbing(self.handle)
            if ret != MV_OK.SUCCESS:
                logger.error(f"Start grabbing failed: 0x{ret:08X}")
                return False
            
            self.is_grabbing = True
            logger.info("Started grabbing")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start grabbing: {e}")
            return False
    
    def stop_grabbing(self) -> bool:
        """
        Stop image acquisition
        
        Returns:
            True if successful, False otherwise
        """
        if self.handle is None:
            return False
        
        try:
            ret = self.dll.MV_CC_StopGrabbing(self.handle)
            if ret != MV_OK.SUCCESS:
                logger.error(f"Stop grabbing failed: 0x{ret:08X}")
                return False
            
            self.is_grabbing = False
            logger.info("Stopped grabbing")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop grabbing: {e}")
            return False
    
    def grab_frame(self, timeout_ms: int = 1000) -> Optional[np.ndarray]:
        """
        Grab one frame
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Numpy array (height, width, channels) or None if failed
        """
        if not self.is_grabbing:
            logger.error("Not grabbing - call start_grabbing() first")
            return None
        
        try:
            # Prepare buffer (allocate large enough buffer)
            buffer_size = 4096 * 3000 * 3  # Max resolution estimate
            buffer = create_string_buffer(buffer_size)
            frame_info = MV_FRAME_OUT_INFO_EX()
            
            # Get frame
            ret = self.dll.MV_CC_GetOneFrameTimeout(
                self.handle,
                byref(buffer),
                buffer_size,
                byref(frame_info),
                timeout_ms
            )
            
            if ret != MV_OK.SUCCESS:
                if ret != MVSErrorCode.MV_E_NODATA:
                    logger.error(f"Get frame failed: 0x{ret:08X}")
                return None
            
            # Convert to numpy array
            width = frame_info.nWidth
            height = frame_info.nHeight
            pixel_type = frame_info.enPixelType
            
            # Handle different pixel formats
            if pixel_type == MVSPixelType.PixelType_Gvsp_Mono8:
                # Mono8 format
                image = np.frombuffer(buffer.raw[:width * height], dtype=np.uint8)
                image = image.reshape((height, width))
                
            elif pixel_type == MVSPixelType.PixelType_Gvsp_RGB8_Packed:
                # RGB8 format
                image = np.frombuffer(buffer.raw[:width * height * 3], dtype=np.uint8)
                image = image.reshape((height, width, 3))
                
            elif pixel_type == MVSPixelType.PixelType_Gvsp_BGR8_Packed:
                # BGR8 format
                image = np.frombuffer(buffer.raw[:width * height * 3], dtype=np.uint8)
                image = image.reshape((height, width, 3))
                
            elif pixel_type in [MVSPixelType.PixelType_Gvsp_BayerGR8,
                                MVSPixelType.PixelType_Gvsp_BayerRG8,
                                MVSPixelType.PixelType_Gvsp_BayerGB8,
                                MVSPixelType.PixelType_Gvsp_BayerBG8]:
                # Bayer format - return as mono for now
                image = np.frombuffer(buffer.raw[:width * height], dtype=np.uint8)
                image = image.reshape((height, width))
                
            else:
                logger.error(f"Unsupported pixel format: 0x{pixel_type:08X}")
                return None
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to grab frame: {e}")
            return None
    
    # Parameter access methods
    def set_exposure(self, exposure_us: float) -> bool:
        """Set exposure time in microseconds"""
        if self.handle is None:
            return False
        ret = self.dll.MV_CC_SetFloatValue(self.handle, b"ExposureTime", ctypes.c_float(exposure_us))
        return ret == MV_OK.SUCCESS
    
    def get_exposure(self) -> Optional[float]:
        """Get exposure time in microseconds"""
        if self.handle is None:
            return None
        value = ctypes.c_float()
        ret = self.dll.MV_CC_GetFloatValue(self.handle, b"ExposureTime", byref(value))
        return value.value if ret == MV_OK.SUCCESS else None
    
    def set_gain(self, gain_db: float) -> bool:
        """Set gain in dB"""
        if self.handle is None:
            return False
        ret = self.dll.MV_CC_SetFloatValue(self.handle, b"Gain", ctypes.c_float(gain_db))
        return ret == MV_OK.SUCCESS
    
    def get_gain(self) -> Optional[float]:
        """Get gain in dB"""
        if self.handle is None:
            return None
        value = ctypes.c_float()
        ret = self.dll.MV_CC_GetFloatValue(self.handle, b"Gain", byref(value))
        return value.value if ret == MV_OK.SUCCESS else None
    
    def set_trigger_mode(self, enabled: bool) -> bool:
        """Enable/disable trigger mode"""
        if self.handle is None:
            return False
        # TriggerMode: 0=Off, 1=On
        value = 1 if enabled else 0
        ret = self.dll.MV_CC_SetEnumValue(self.handle, b"TriggerMode", value)
        return ret == MV_OK.SUCCESS
    
    def software_trigger(self) -> bool:
        """Execute software trigger"""
        if self.handle is None:
            return False
        ret = self.dll.MV_CC_SetEnumValue(self.handle, b"TriggerSoftware", 1)
        return ret == MV_OK.SUCCESS
    
    def __del__(self):
        """Destructor - ensure camera is closed"""
        self.close_camera()


if __name__ == "__main__":
    # Test code
    logging.basicConfig(level=logging.INFO)
    
    print("Enumerating MVS cameras...")
    cameras = MVSCamera.enumerate_cameras()
    
    if cameras:
        print(f"\nFound {len(cameras)} camera(s):")
        for serial, model in cameras:
            print(f"  - {model} (SN: {serial})")
        
        # Test open first camera
        print(f"\nOpening camera {cameras[0][0]}...")
        cam = MVSCamera()
        if cam.open_camera(cameras[0][0]):
            print("Camera opened successfully")
            
            if cam.start_grabbing():
                print("Grabbing started")
                
                # Grab a frame
                frame = cam.grab_frame()
                if frame is not None:
                    print(f"Grabbed frame: {frame.shape}")
                
                cam.stop_grabbing()
            
            cam.close_camera()
    else:
        print("No cameras found")
