///////////////////////////////////////////////////////////////////////////////
// file    : TeliCamApi.h
// brief   : Main header file
// version : 3.0.5.1
// author  : (C)2014 TOSHIBA TELI CORPORATION
// date    : 2017/05/31

#ifndef _TELICAMAPI_H_
#define _TELICAMAPI_H_

///////////////////////////////////////////////////////////////////////////////
// Include
#include <stddef.h>

#include "TeliTypes.h"
#include "TeliCamNode.h"

namespace Teli {

	#ifdef __cplusplus
		#ifndef EXTERN_C
			#define EXTERN_C extern "C"
		#endif
	#else
		#ifndef EXTERN_C
			#define EXTERN_C
		#endif
	#endif

	#if defined (_WIN32)
		#ifdef TELICAMAPI_EXPORTS
			#define TELICAMAPI_API
		#else
			#define TELICAMAPI_API __declspec(dllimport)
		#endif

		#define CAMAPI EXTERN_C TELICAMAPI_API CAM_API_STATUS _stdcall
	#else
		#define TELICAMAPI_API

		#define CAMAPI EXTERN_C TELICAMAPI_API CAM_API_STATUS
	#endif

	#define MAX_CAMERA_NUM			(64)
	#define MAX_INFO_STR			(64)
	#define DEFAULT_API_BUFFER_CNT	(8)
	#define NODE_NAME_LENGTH_MAX	(64)

	typedef enum
	{
		CAM_TYPE_UNKNOWN						= 0x00,
		CAM_TYPE_U3V							= 0x01,		// USB3 Vision Camera
		CAM_TYPE_GEV							= 0x02,		// GigE Vision Camera
		CAM_TYPE_ALL							= 0xFFFF,
	} CAM_TYPE;

	// Interface definition for AbortPipe and ResetPipe to specify which interface to be reset
	typedef enum _CAM_IF_FLG
	{
		CAM_DCI,       // Device Control Interface
		CAM_DSI,       // Device Streaming Interface
		CAM_DEI,       // Device Event Interface
	} CAM_IF_FLG;

	// Access mode
	typedef enum
	{
		CAM_ACCESS_MODE_OPEN					= 0,		// Open access
		CAM_ACCESS_MODE_CONTROL					= 1,		// Control access
		CAM_ACCESS_MODE_EXCLUSIVE				= 3,		// Exclusive access
	} CAM_ACCESS_MODE;

	typedef enum
	{
		CAM_ACQ_MODE_CONTINUOUS					= 8,		// Continuous
		CAM_ACQ_MODE_MULTI_FRAME				= 9,		// MultiFrame
		CAM_ACQ_MODE_IMAGE_BUFFER_READ			= 10,		// Camera Image Buffer Mode
	} CAM_ACQ_MODE_TYPE;

	typedef enum
	{
		IMAGE_FORMAT0							= 0,		// Format0
		IMAGE_FORMAT1							= 1,		// Format1
		IMAGE_FORMAT2							= 2,		// Format2
	} CAM_IMAGE_FORMAT_SELECTOR_TYPE;

	typedef enum
	{
		CAM_TEST_PATTERN_OFF					= 0,		// Off
		CAM_TEST_PATTERN_BLACK					= 1,		// Black
		CAM_TEST_PATTERN_WHITE					= 2,		// White
		CAM_TEST_PATTERN_GREY_A					= 3,		// GrayA(BrightGrey)
		CAM_TEST_PATTERN_GREY_B					= 4,		// GreyB(DarkGrey)
		CAM_TEST_PATTERN_GREY_HORIZONTAL_RAMP	= 5,		// GreyHorizontalRamp
		CAM_TEST_PATTERN_GREY_SCALE				= 6,		// GreyScale
		CAM_TEST_PATTERN_COLOR_BAR				= 7,		// ColorBar
		CAM_TEST_PATTERN_GREY_VERTICAL_RAMP		= 8,		// GreyVerticalRamp
	} CAM_TEST_PATTERN_TYPE;

	typedef enum
	{
		CAM_ACQ_FRAME_RATE_CTRL_NO_SPECIFY		= 0,		// NoSpecify
		CAM_ACQ_FRAME_RATE_CTRL_MANUAL			= 1,		// Manual
	} CAM_ACQ_FRAME_RATE_CTRL_TYPE;

	typedef enum
	{
		CAM_IMAGE_BUFFER_MODE_OFF				= 0,		// ImageBufferMode Off
		CAM_IMAGE_BUFFER_MODE_ON				= 1,		// ImageBufferMode On
	} CAM_IMAGE_BUFFER_MODE_TYPE;

	typedef enum
	{
		CAM_TRIGGER_SEQUENCE0					= 0,		// Edge mode
															// USB3 Vision Camera : Trigger Sequence register = TriggerSequence0
															// GigE Vision Camera : ExposureMode     register = Timed
															//                      TriggerSelector  register = FrameStart
		CAM_TRIGGER_SEQUENCE1					= 1,		// Level mode
															// USB3 Vision Camera : Trigger Sequence register = TriggerSequence1
															// GigE Vision Camera : ExposureMode     register = TriggerWidth
															//                      TriggerSelector  register = FrameStart
		CAM_TRIGGER_SEQUENCE6					= 6,		// Bulk (FrameBurst) mode
															// USB3 Vision Camera : Trigger Sequence register = TriggerSequence6
															// GigE Vision Camera : ExposureMode     register = Timed
															//                      TriggerSelector  register = FrameBurstStart
	} CAM_TRIGGER_SEQUENCE_TYPE;

	typedef enum
	{
		CAM_TRIGGER_LINE0						= 0,		// IO Line0(Hardware Trigger)
		CAM_TRIGGER_LINE1						= 1,		// IO Line1
		CAM_TRIGGER_LINE2						= 2,		// IO Line2
		CAM_TRIGGER_SOFTWARE					= 64,		// Software trigger mode
	} CAM_TRIGGER_SOURCE_TYPE;

	typedef enum
	{
		CAM_TRIGGER_FALLING_EDGE				= 0,		// Falling edge
		CAM_TRIGGER_RISING_EDGE					= 1,		// Rising edge
	} CAM_TRIGGER_ACTIVATION_TYPE;

	typedef enum
	{
		CAM_EXPOSURE_TIME_CONTROL_NO_SPECIFY	= 0,		// USB3 Vision Camera : ExposureTimeControl register = NoSpecify
															// GigE Vision Camera : ExposureAuto        register ... Not Abailable
		CAM_EXPOSURE_TIME_CONTROL_MANUAL		= 1,		// USB3 Vision Camera : ExposureTimeControl register = Manual
															// GigE Vision Camera : ExposureAuto        register = Off
		CAM_EXPOSURE_TIME_CONTROL_AUTO			= 2,		// USB3 Vision Camera : ExposureTimeControl register = Auto
															// GigE Vision Camera : ExposureAuto        register = Continuous
	} CAM_EXPOSURE_TIME_CONTROL_TYPE;

	typedef enum
	{
		CAM_LINE_SELECTOR_LINE0					= 0,		// Line0
		CAM_LINE_SELECTOR_LINE1					= 1,		// Line1
		CAM_LINE_SELECTOR_LINE2					= 2,		// Line2
	} CAM_LINE_SELECTOR_TYPE;

	typedef enum
	{
		CAM_LINE_SOURCE_OFF						= 0,		// OFF
		CAM_LINE_SOURCE_VD						= 17,		// VD (Gig-E)
		CAM_LINE_SOURCE_USER_OUTPUT				= 32,		// UserOutput (U3v)
		CAM_LINE_SOURCE_TIMER0_ACTIIVE			= 64,		// Timer0Active
		CAM_LINE_SOURCE_ACQUISITION_ACTIVE		= 99,		// AcquisitionActive (U3v)
		CAM_LINE_SOURCE_FRAME_TRIGGER_WAIT		= 106,		// FrameTriggerWait
		CAM_LINE_SOURCE_FRAME_ACTIVE			= 107,		// FrameActive
		CAM_LINE_SOURCE_FRAME_TRANSFER_ACTIVE	= 115,		// FrameTransferActive (U3v) or FrameTransfer (Gig-E)
		CAM_LINE_SOURCE_EXPOSURE_ACTIVE			= 123,
	} CAM_LINE_SOURCE_TYPE;

	typedef enum
	{
		CAM_TIMER_TRIGGER_SOURCE_OFF			= 0,		// Off
		CAM_TIMER_TRIGGER_SOURCE_LINE0_ACTIVE	= 32,		// Line0Active
		CAM_TIMER_TRIGGER_SOURCE_FRAME_TRIGGER	= 104,		// FrameTrigger
		CAM_TIMER_TRIGGER_SOURCE_EXPOSURE_START	= 124,		// ExposureStart
		CAM_TIMER_TRIGGER_SOURCE_EXPOSURE_END	= 125,		// ExposureEnd
	} CAM_TIMER_TRIGGER_SOURCE_TYPE;

	typedef enum
	{
		CAM_GAIN_AUTO_OFF						= 1,		// GainAuto = Manual(Off)
		CAM_GAIN_AUTO_AUTO						= 2,		// GainAuto = Auto(Continuous)
	} CAM_GAIN_AUTO_TYPE;

	typedef enum
	{
		//CAM_BALANCE_RATIO_SELECTOR_NONE		= 0,
		CAM_BALANCE_RATIO_SELECTOR_RED			= 1,		// Red (R)
		CAM_BALANCE_RATIO_SELECTOR_BLUE			= 2,		// Blue (B)
	} CAM_BALANCE_RATIO_SELECTOR_TYPE;

	typedef enum
	{
		CAM_BALANCE_WHITE_AUTO_OFF				= 1,		// Off (Manual)
		CAM_BALANCE_WHITE_AUTO_CONTINUOUS		= 2,		// Continuous (Auto)
		CAM_BALANCE_WHITE_AUTO_ONCE				= 3,		// Once (AutoOnce)
	} CAM_BALANCE_WHITE_AUTO_TYPE;

	typedef enum
	{
		CAM_COLOR_CORRECTION_MATRIX_RG			= 0,		// SelectorI = R , SelectorJ = G
		CAM_COLOR_CORRECTION_MATRIX_RB			= 1,		// SelectorI = R , SelectorJ = B
		CAM_COLOR_CORRECTION_MATRIX_GR			= 2,		// SelectorI = G , SelectorJ = R
		CAM_COLOR_CORRECTION_MATRIX_GB			= 3,		// SelectorI = G , SelectorJ = B
		CAM_COLOR_CORRECTION_MATRIX_BR			= 4,		// SelectorI = B , SelectorJ = R
		CAM_COLOR_CORRECTION_MATRIX_BG			= 5,		// SelectorI = B , SelectorJ = G
	} CAM_COLOR_CORRECTION_MATRIX_TYPE;

	typedef enum
	{
		CAM_USER_SET_SELECTOR_DEFAULT			= 0,
		CAM_USER_SET_SELECTOR_USER_SET1			= 1,
		CAM_USER_SET_SELECTOR_USER_SET2			= 2,
		CAM_USER_SET_SELECTOR_USER_SET3			= 3,
		CAM_USER_SET_SELECTOR_USER_SET4			= 4,
		CAM_USER_SET_SELECTOR_USER_SET5			= 5,
		CAM_USER_SET_SELECTOR_USER_SET6			= 6,
		CAM_USER_SET_SELECTOR_USER_SET7			= 7,
		CAM_USER_SET_SELECTOR_USER_SET8			= 8,
		CAM_USER_SET_SELECTOR_USER_SET9			= 9,
		CAM_USER_SET_SELECTOR_USER_SET10		= 10,
		CAM_USER_SET_SELECTOR_USER_SET11		= 11,
		CAM_USER_SET_SELECTOR_USER_SET12		= 12,
		CAM_USER_SET_SELECTOR_USER_SET13		= 13,
		CAM_USER_SET_SELECTOR_USER_SET14		= 14,
		CAM_USER_SET_SELECTOR_USER_SET15		= 15,
	} CAM_USER_SET_SELECTOR_TYPE;

	typedef enum
	{
		CAM_FRAME_SYNCHRONIZATION_OFF			= 0,
		CAM_FRAME_SYNCHRONIZATION_BUS			= 1,
	} CAM_FRAME_SYNCHRONIZATION_TYPE;


	///////////////////////////////////////////////////////////
	// Handles
	typedef uint64_t  CAM_HANDLE;				// Camera handle
	typedef uint64_t  CAM_NODE_HANDLE;			// Node handle
	typedef uint64_t  CAM_STRM_HANDLE;			// Stream handle
	typedef uint64_t  CAM_STRM_REQUEST_HANDLE;	// Stream request handle
	typedef uint64_t  CAM_EVT_HANDLE;			// Event handle
	typedef uint64_t  CAM_EVT_REQUEST_HANDLE;	// Event request handle
	typedef uint64_t  CAM_IMG_HANDLE;			// Image handle


	// API return status codes
	enum _CAM_API_STATUS
	{
		// Operation completed successfully.
		CAM_API_STS_SUCCESS                  = 0x00000000,

		// API have not been made ready by Sys_Initialize.
		CAM_API_STS_NOT_INITIALIZED          = 0x00000001,

		// API is already in ready state.
		CAM_API_STS_ALREADY_INITIALIZED      = 0x00000002,

		// Camera is not found.
		CAM_API_STS_NOT_FOUND                = 0x00000003,

		// Specified handle is already opened.
		CAM_API_STS_ALREADY_OPENED           = 0x00000004,

		// Specified event is already registered.
		CAM_API_STS_ALREADY_ACTIVATED        = 0x00000005,

		// The specified camera index was not valid.
		CAM_API_STS_INVALID_CAMERA_INDEX     = 0x00000006,

		// The specified camera handle was not valid.
		CAM_API_STS_INVALID_CAMERA_HANDLE    = 0x00000007,

		// The specified node handle was not valid.
		CAM_API_STS_INVALID_NODE_HANDLE      = 0x00000008,

		// The specified stream handle was not valid.
		CAM_API_STS_INVALID_STREAM_HANDLE    = 0x00000009,

		// The specified buffer handle was not valid.
		CAM_API_STS_INVALID_REQUEST_HANDLE    = 0x0000000A,

		// The specified event handle was not valid.
		CAM_API_STS_INVALID_EVENT_HANDLE     = 0x0000000B,

		// The specified image handle was not valid.
		CAM_API_STS_INVALID_IMAGE_HANDLE     = 0x0000000C,

		// The specified parameter was not valid.
		CAM_API_STS_INVALID_PARAMETER        = 0x0000000D,

		// Buffer size specified by user was too small to complete the request.
		CAM_API_STS_BUFFER_TOO_SMALL         = 0x0000000E,

		// Request cannot be completed because insufficient memory resource.
		CAM_API_STS_NO_MEMORY                = 0x0000000F,

		// Memory location specified by user was not valid.
		CAM_API_STS_MEMORY_NO_ACCESS         = 0x00000010,

		// Feature is not implemented in the camera or API.
		CAM_API_STS_NOT_IMPLEMENTED          = 0x00000011,

		// Timeout expired.
		CAM_API_STS_TIMEOUT                  = 0x00000012,

		// The opened camera may be lost. You should re-enum the camera to confirm whether it exist.
		CAM_API_STS_CAMERA_NOT_RESPONDING    = 0x00000013,

		// Stream or event "get request" is failed because there is no complete queue.
		CAM_API_STS_EMPTY_COMPLETE_QUEUE     = 0x00000014,

		// Information is not yet ready.
		CAM_API_STS_NOT_READY                = 0x00000015,

		// Failed to set the access mode.
		CAM_API_STS_ACCESS_MODE_SET_ERR      = 0x00000016,

		// Controller caused an I/O error.
		CAM_API_STS_IO_DEVICE_ERROR          = 0x00000020,

		// Failed to load the XML.
		CAM_API_STS_XML_LOAD_ERR             = 0x00000101,

		// GenICam error occurred.
		CAM_API_STS_GENICAM_ERR              = 0x00000102,

		// Failed to load the dll file.
		CAM_API_STS_DLL_LOAD_ERR             = 0x00000103,

		// Attempt to access a not existing register address.
		CAM_API_STS_INVALID_ADDRESS          = 0x00000801,

		// Attempt to write to a read only register.
		CAM_API_STS_WRITE_PROTECT            = 0x00000802,

		// Access registers with an address which is not aligned according to the underlying technology.
		CAM_API_STS_BAD_ALIGNMENT            = 0x00000803,

		// Read a non-readable or write a non-writable register address.
		CAM_API_STS_ACCESS_DENIED            = 0x00000804,

		// Camera is currently busy.
		CAM_API_STS_BUSY                     = 0x00000805,

		// Not readable.
		CAM_API_STS_NOT_READABLE             = 0x00000806,

		// Not writable.
		CAM_API_STS_NOT_WRITABLE             = 0x00000807,

		// Function or the camera of the register is not currently available.
		CAM_API_STS_NOT_AVAILABLE		     = 0x00000808,

		// User request had not be able to complete while user specified timeoout limit.
		CAM_API_STS_REQUEST_TIMEOUT          = 0x00001001,

		// Stream resend request timeoout.
		CAM_API_STS_RESEND_TIMEOUT           = 0x00001002,

		// Stream resend data receive timeoout.
		CAM_API_STS_RESPONSE_TIMEOUT         = 0x00001003,

		// Transferred frame data was larger than user specified max payload size.
		CAM_API_STS_BUFFER_FULL              = 0x00001004,

		// Actual received payload size was not equal to the size notified by Trailer.
		CAM_API_STS_UNEXPECTED_BUFFER_SIZE   = 0x00001005,

		// Exceeded the MAX number of packets that is realized by Leader or Trailer.
		CAM_API_STS_UNEXPECTED_NUMBER        = 0x00001006,

		// Any error was notified by stream or event status on transaction header.
		CAM_API_STS_PACKET_STATUS_ERROR      = 0x00001007,

		// Packet resend command is not supported by the camera.
		CAM_API_STS_RESEND_NOT_IMPLEMENTED   = 0x00001008,

		// The requested packet is not available anymore.
		CAM_API_STS_PACKET_UNAVAILABLE       = 0x00001009,

		// Frame data is terminated with next Leader or Trailer's BlockId is different from Leader's.
		// Some packets may be lost.
		CAM_API_STS_MISSING_PACKETS          = 0x0000100A,

		// Requests were flushed by user request.
		CAM_API_STS_FLUSH_REQUESTED          = 0x0000100B,

		// The loss of packet exceeded the specified value.
		CAM_API_STS_TOO_MANY_PACKET_MISSING  = 0x0000100C,

		// Requests were flushed because power state was chaned into save mode.
		CAM_API_STS_FLUSHED_BY_D0EXIT        = 0x0000100D,

		// Requests were flushed by camera remove event.
		CAM_API_STS_FLUSHED_BY_CAMERA_REMOVE = 0x0000100E,

		// Failed to load the driver.
		CAM_API_STS_DRIVER_LOAD_ERR          = 0x0000100F,

		// Failed to open file.
		CAM_API_STS_FILE_OPEN_ERROR			 = 0x00002001,

		// Failed to write data to file.
		CAM_API_STS_FILE_WRITE_ERROR		 = 0x00002002,

		// Failed to read data from file.
		CAM_API_STS_FILE_READ_ERROR			 = 0x00002003,

		// Failed to find file.
		CAM_API_STS_FILE_NOT_FOUND			 = 0x00002004,

		// At least one command parameter of CCD or SCD is invalid or out of range. 
		CAM_API_STS_INVALID_PARAMETER_FROM_CAM = 0x00008002,

		// The value written to the SI streaming size registers is not aligned
		// to Payload Size Alignment value of the SI Info register.
		CAM_API_STS_SI_PAYLOAD_SIZE_NOT_ALIGNED = 0x0000A003,

		// Some data in the block has been discarded.
		CAM_API_STS_DATA_DISCARDED           = 0x0000A100,

		// Unspecified error occurred.
		CAM_API_STS_UNSUCCESSFUL             = 0xFFFFFFFF
	};
	typedef uint32_t CAM_API_STATUS;


	// Pixel format
	enum _CAM_PIXEL_FORMAT
	{
		PXL_FMT_Unknown    = 0x00000000,
											//  Grouping  Padding
											//   Pixels    Bits
		PXL_FMT_Mono8      = 0x01080001,    //     1        0       8-bit pixel in one byte
		PXL_FMT_Mono10     = 0x01100003,    //     1        6       10-bit pixel padded to 16 bits
		PXL_FMT_Mono12     = 0x01100005,    //     1        4       12-bit pixel padded to 16 bits
		PXL_FMT_Mono16     = 0x01100007,    //     1        0       16-bit pixel in two bytes
		PXL_FMT_BayerGR8   = 0x01080008,    //     1        0       8-bit pixel in one byte
		PXL_FMT_BayerGR10  = 0x0110000C,    //     1        6       10-bit pixel padded to 16 bits
		PXL_FMT_BayerGR12  = 0x01100010,    //     1        4       12-bit pixel padded to 16 bits
		PXL_FMT_BayerRG8   = 0x01080009,    //     1        0       8-bit pixel in one byte
		PXL_FMT_BayerRG10  = 0x0110000D,    //     1        6       10-bit pixel padded to 16 bits
		PXL_FMT_BayerRG12  = 0x01100011,    //     1        4       12-bit pixel padded to 16 bits
		PXL_FMT_BayerGB8   = 0x0108000A,    //     1        0       8-bit pixel in one byte
		PXL_FMT_BayerGB10  = 0x0110000E,    //     1        6       10-bit pixel padded to 16 bits
		PXL_FMT_BayerGB12  = 0x01100012,    //     1        4       12-bit pixel padded to 16 bits
		PXL_FMT_BayerBG8   = 0x0108000B,    //     1        0       8-bit pixel in one byte
		PXL_FMT_BayerBG10  = 0x0110000F,    //     1        6       10-bit pixel padded to 16 bits
		PXL_FMT_BayerBG12  = 0x01100013,    //     1        4       12-bit pixel padded to 16 bits
		PXL_FMT_RGB8       = 0x02180014,    //     1        0       8-bit color component in one byte
		PXL_FMT_BGR8       = 0x02180015,    //     1        0       8-bit color component in one byte
		PXL_FMT_BGR10      = 0x02300019,    //     1        6       10-bit color component padded to 16 bits
		PXL_FMT_BGR12      = 0x0230001B,    //     1        4       12-bit color component padded to 16 bits
		PXL_FMT_YUV411_8   = 0x020C001E,    //     1        0       8-bit color component in one byte, UYYVYY component sequence
		PXL_FMT_YUV422_8   = 0x0210001F,    //     1        0       8-bit color component in one byte, UYVY component sequence
		PXL_FMT_YUV8       = 0x02180020,    //     1        0       8-bit color component in one byte, UYV component sequence

//		PXL_FMT_Mono1p     = 0x01010037,    //     8        0(*)    Combine 8 monochrome pixels in one byte
//		PXL_FMT_Mono2p     = 0x01020038,    //     4        0(*)    Combine 4 monochrome pixels in one byte
//		PXL_FMT_Mono4p     = 0x01040039,    //     2        0(*)    Combine 2 monochrome pixels in one byte
//		PXL_FMT_Mono10p    = 0x010a0046,    //     4        0(*)    It takes 4 pixels (packed over 5 bytes) to re-align on byte boundary
//		PXL_FMT_Mono12p    = 0x010c0047,    //     2        0(*)    It takes 2 pixels (packed over 3 bytes) to re-align on byte boundary
//		PXL_FMT_Mono14     = 0x01100025,    //     1        2       14-bit pixel padded to 16 bits
//		PXL_FMT_BayerGR10p = 0x010A0056,    //     4        0(*)    It takes 4 pixels (packed over 5 bytes) to re-align on byte boundary
//		PXL_FMT_BayerGR12p = 0x010C0057,    //     2        0(*)    It takes 2 pixels (packed over 3 bytes) to re-align on byte boundary
//		PXL_FMT_BayerGR16  = 0x0110002E,    //     1        0       16-bit pixel in two bytes
//		PXL_FMT_BayerRG10p = 0x010A0058,    //     4        0(*)    It takes 4 pixels (packed over 5 bytes) to re-align on byte boundary
//		PXL_FMT_BayerRG12p = 0x010C0059,    //     2        0(*)    It takes 2 pixels (packed over 3 bytes) to re-align on byte boundary
//		PXL_FMT_BayerRG16  = 0x0110002F,    //     1        0       16-bit pixel in two bytes
//		PXL_FMT_BayerGB10p = 0x010A0054,    //     4        0(*)    It takes 4 pixels (packed over 5 bytes) to re-align on byte boundary
//		PXL_FMT_BayerGB12p = 0x010C0055,    //     2        0(*)    It takes 2 pixels (packed over 3 bytes) to re-align on byte boundary
//		PXL_FMT_BayerGB16  = 0x01100030,    //     1        0       16-bit pixel in two bytes
//		PXL_FMT_BayerBG10p = 0x010A0052,    //     4        0(*)    It takes 4 pixels (packed over 5 bytes) to re-align on byte boundary
//		PXL_FMT_BayerBG12p = 0x010C0053,    //     2        0(*)    It takes 2 pixels (packed over 3 bytes) to re-align on byte boundary
//		PXL_FMT_BayerBG16  = 0x01100031,    //     1        0       16-bit pixel in two bytes
//		PXL_FMT_BGR10p     = 0x021E0048,    //     4        0(*)    It takes 4 pixels (packed over 15 bytes) to re-align on byte boundary
//		PXL_FMT_BGR12p     = 0x02240049,    //     2        0(*)    It takes 2 pixels (packed over 9 bytes) to re-align on byte boundary
//		PXL_FMT_BGR14      = 0x0230004A,    //     1        2       14-bit color component padded to 16 bits
//		PXL_FMT_BGR16      = 0x0230004B,    //     1        0       16-bit color component in two bytes
//		PXL_FMT_BGRa8      = 0x02200017,    //     1        0       8-bit color component in one byte
//		PXL_FMT_BGRa10     = 0x0240004C,    //     1        6       10-bit color component padded to 16 bits
//		PXL_FMT_BGRa10p    = 0x0228004D,    //     1        0       It takes 1 pixel (packed over 5 bytes) to re-align on byte boundary
//		PXL_FMT_BGRa12     = 0x0240004E,    //     1        4       12-bit color component padded to 16 bits
//		PXL_FMT_BGRa12p    = 0x0230004F,    //     1        0       It takes 1 pixel (packed over 6 bytes) to re-align on byte boundary
//		PXL_FMT_BGRa14     = 0x02400050,    //     1        2       14-bit color component padded to 14 bits
//		PXL_FMT_BGRa16     = 0x02400051,    //     1        0       16-bit color components in two bytes
//		PXL_FMT_YCbCr8     = 0x0218005B,    //     1        0       8-bit color component in one byte
//		PXL_FMT_YCbCr422_8 = 0x0210003B,    //     1        0       8-bit color component in one byte, YCbYCr component sequence
//		PXL_FMT_YCbCr411_8 = 0x020C005A,    //     1        0       8-bit color component in one byte, YYCbYYCr component sequence

		//[Note] (*):some additional padding bits might be necessary if the number of pixels is not a multiple of the number of Grouping Pixels.
	};
	typedef uint32_t CAM_PIXEL_FORMAT;

	// U3V Stream payload type
	enum _U3V_CAM_STRM_PYLD_TYPE
	{
		U3V_CAM_STRM_PYLD_IMAGE                = 0x0001,
		U3V_CAM_STRM_PYLD_CHUNK                = 0x4000,  // not supported
		U3V_CAM_STRM_PYLD_IMAGE_EXTENDED_CHUNK = 0x4001,
	};
	typedef uint16_t U3V_CAM_STRM_PYLD_TYPE;

	// GigE-Vision Stream payload type
	enum _GEV_CAM_STRM_PYLD_TYPE
	{
		GEV_CAM_STRM_PYLD_TEST     = 0x0000,
		GEV_CAM_STRM_PYLD_IMAGE    = 0x0001,
		GEV_CAM_STRM_PYLD_RAW      = 0x0002,
		GEV_CAM_STRM_PYLD_FILE     = 0x0003,
		GEV_CAM_STRM_PYLD_CHUNK    = 0x0004,
		GEV_CAM_STRM_PYLD_EX_CHUNK = 0x0005,
	};
	typedef uint16_t GEV_CAM_STRM_PYLD_TYPE;


	///////////////////////////////////////////////////////////
	// Structures

	typedef struct _U3V_SYSTEM_INFO
	{
		char		szDriverVersion[MAX_INFO_STR];
		char		szDllVersion[MAX_INFO_STR];
		char		szDllExVersion[MAX_INFO_STR];
	} U3V_SYSTEM_INFO, *PU3V_SYSTEM_INFO;

	typedef struct _GEV_SYSTEM_INFO
	{
		char		szDriverVersion[MAX_INFO_STR];
		char		szDllVersion[MAX_INFO_STR];
		char		szDllExVersion[MAX_INFO_STR];
	} GEV_SYSTEM_INFO, *PGEV_SYSTEM_INFO;

	typedef struct _CAM_SYSTEM_INFO
	{
		U3V_SYSTEM_INFO	sU3vInfo;
		GEV_SYSTEM_INFO	sGevInfo;
		char			szDllVersion[MAX_INFO_STR];
	} CAM_SYSTEM_INFO, *PCAM_SYSTEM_INFO;


	typedef struct _U3V_CAMERA_INFO
	{
		char		szFamilyName[MAX_INFO_STR];
		char		szDeviceVersion[MAX_INFO_STR];
		char		szManufacturerInfo[MAX_INFO_STR];
		uint32_t	uiAdapterVendorId;
		uint32_t	uiAdapterDeviceId;
		uint32_t	uiAdapterDfltMaxPacketSize;
	} U3V_CAM_INFO, *PU3V_CAMERA_INFO;

	typedef struct _GEV_CAMERA_INFO
	{
		char		szDisplayName[512];
		uint8_t		aucMACAddress[6];
		int8_t		cSupportIP_LLA;
		int8_t		cSupportIP_DHCP;
		int8_t		cSupportIP_Persistent;
		int8_t		cCurrentIP_LLA;
		int8_t		cCurrentIP_DHCP;
		int8_t		cCurrentIP_Persistent;
		uint8_t		aucIPAddress[4];
		uint8_t		aucSubnet[4];
		uint8_t		aucGateway[4];
		uint8_t		aucAdapterMACAddress[6];
		uint8_t		aucAdapterIPAddress[4];
		uint8_t		aucAdapterSubnet[4];
		uint8_t		aucAdapterGateway[4];
		char		szAdapterDisplayName[1024];
	} GEV_CAM_INFO, *PGEV_CAM_INFO;

	typedef struct _CAM_INFO
	{
		CAM_TYPE			eCamType;
		char				szManufacturer[MAX_INFO_STR];
		char				szModelName[MAX_INFO_STR];
		char				szSerialNumber[MAX_INFO_STR];
		char				szUserDefinedName[MAX_INFO_STR];
		U3V_CAM_INFO		sU3vCamInfo;
		GEV_CAM_INFO		sGevCamInfo;
	} CAM_INFO, *PCAM_INFO;

	typedef struct _CAM_NODE_NAME
	{
		char	szNodeName[NODE_NAME_LENGTH_MAX];
	} CAM_NODE_NAME, *PCAM_NODE_NAME;


	#pragma pack( push, 1 )

	// U3V Stream Image leader
	typedef struct _U3V_STRM_IMG_LDR
	{
		uint32_t				uiMagicKey;      // 0x4C563355 "U3VL"
		uint16_t				ushReserved1;
		uint16_t				ushLeaderSize;
		uint64_t				ullBlockId;
		uint16_t				ushReserved2;
		U3V_CAM_STRM_PYLD_TYPE	ushPayloadType;
		uint64_t				ullTimestamp;
		CAM_PIXEL_FORMAT		uiPixelFormat;
		uint32_t				uiSizeX;
		uint32_t				uiSizeY;
		uint32_t				uiOffset_x;
		uint32_t				uiOffset_y;
		uint16_t				ushPadding_x;
		uint16_t				ushRreserved3;
	} U3V_STRM_IMG_LDR, *PU3V_STRM_IMG_LDR;

	// U3V Stream Image Trailer
	typedef struct _U3V_STRM_IMG_TRLR
	{
		uint32_t				uiMagicKey;      // 0x54563355 "U3VT"
		uint16_t				ushReserved1;
		uint16_t				ushTrailerSize;
		uint64_t				ullBlockId;
		uint16_t				ushStatus;
		uint16_t				ushReserved2;
		uint64_t				ullValidPayloadSize;
		uint32_t				uiSizeY;
	} U3V_STRM_IMG_TRLR, *PU3V_STRM_IMG_TRLR;

	// U3V Stream Image Extended Chunk Trailer
	typedef struct _U3V_STRM_IMG_EX_CHUNK_TRLR
	{
		uint32_t				uiMagicKey;      // 0x54563355 "U3VT"
		uint16_t				ushReserved1;
		uint16_t				ushTrailerSize;
		uint64_t				ullBlockId;
		uint16_t				ushStatus;
		uint16_t				ushReserved2;
		uint64_t				ullValidPayloadSize;
		uint32_t				uiSizeY;
		uint32_t				uiChunkLayoutID;
	} U3V_STRM_IMG_EX_CHUNK_TRLR, *PU3V_STRM_IMG_EX_CHUNK_TRLR;

	// GigE-Vision Stream Image Leader
	typedef struct _GEV_STRM_IMG_LDR
	{
		uint16_t				ushBlockId;
		GEV_CAM_STRM_PYLD_TYPE  ushPayloadType;
		uint16_t				ushReserved;
		uint32_t				uiTimestampHi;
		uint32_t				uiTimestampLo;

		CAM_PIXEL_FORMAT		uiPixelFormat;
		uint32_t				uiSizeX;
		uint32_t				uiSizeY;
		uint32_t				uiOffsetX;
		uint32_t				uiOffsetY;
		uint16_t				ushPaddingY;
		uint16_t				ushPaddingX;
	} GEV_STRM_IMG_LDR, *PGEV_STRM_IMG_LDR;

	// GigE-Vision Stream Image Trailer
	typedef struct _GEV_STRM_IMG_TRLR
	{
		uint16_t				ushBlockId;
		GEV_CAM_STRM_PYLD_TYPE  ushPayloadType;
		uint16_t				ushReserved;
		uint32_t				uiSizeY;
	} GEV_STRM_IMG_TRLR, *PGEV_STRM_IMG_TRLR;

	// GigE-Vision Stream Extended Chunk Trailer
	typedef struct _GEV_STRM_EX_CHUNK_TRLR
	{
		uint16_t				ushBlockId;
		GEV_CAM_STRM_PYLD_TYPE	ushPayloadType;
		uint16_t				ushReserved;
		uint32_t				uiChunkDataPayloadLength;
		uint32_t				uiSizeY;
		uint32_t				uiChunkLayoutId;
	} GEV_STRM_EX_CHUNK_TRLR, *PGEV_STRM_EX_CHUNK_TRLR;

	#pragma pack( pop )


	// U3V Buffer information
	typedef struct _U3V_STRM_REQUEST_INFO
	{
		void		*pvLeader;			// Leader buffer
		void		*pvPayload;			// Pyload buffer
		void		*pvTrailer;			// Trailer buffer
		uint32_t    uiPayloadSize;		// Actual payload size
	} U3V_STRM_REQUEST_INFO, *PU3V_STRM_REQUEST_INFO;

	// GEV Buffer information
	typedef struct _GEV_STRM_REQUEST_INFO
	{
		void		*pvLeader;				// Leader buffer
		void		*pvPayload;             // Payload buffer
		void		*pvTrailer;             // Trailer buffer
		uint32_t	uiNumOfPayloadPacket;  // Actual number of payload packets
		uint32_t	uiPayloadSize;         // Actual payload size
		uint32_t	uiNumOfResendPacket;   // Number of resend packets
	} GEV_STRM_REQUEST_INFO, *PGEV_STRM_REQUEST_INFO;


	// Stream request buffer information
	typedef struct _STRM_REQUEST_INFO
	{
		U3V_STRM_REQUEST_INFO sU3vInfo;
		GEV_STRM_REQUEST_INFO sGevInfo;
	} CAM_STRM_REQUEST_INFO, *PSTRM_REQUEST_INFO;

	typedef struct _CAM_IMAGE_INFO
	{
		uint64_t				ullTimestamp;
		CAM_PIXEL_FORMAT		uiPixelFormat;
		uint32_t				uiSizeX;
		uint32_t				uiSizeY;
		uint32_t				uiOffsetX;
		uint32_t				uiOffsetY;
		uint32_t				uiPaddingX;
		uint64_t				ullBlockId;

		void					*pvBuf;
		uint32_t				uiSize;
		uint64_t				ullImageId;
		CAM_API_STATUS			uiStatus;
	} CAM_IMAGE_INFO, *PCAM_IMAGE_INFO;

	// statistics about data streaming
	typedef struct GEV_STRM_STATS
	{
	    uint64_t    ulRequest;          // requested counts in total
	    uint64_t    ulSuccess;          // successful counts
	    uint64_t    ulError;            // error counts
	    uint64_t    ulResendRequest;    // resend request counts
	    uint64_t    ulResendReceive;    // resend response receive counts
	    uint64_t    ulMissing20;        // dropped counts that exceed 20 or more packets
	} GEV_STRM_STATS;

	typedef struct _U3V_EVT_REQUEST_INFO
	{
		uint16_t		ushRequestId;	// request id
		uint16_t		ushEventId;		// event id
		uint64_t		ullTimestamp;	// timestamp
		void*			pvPayload;		// payload buffer pointer
	} U3V_EVT_REQUEST_INFO, *PU3V_EVT_REQUEST_INFO;

	typedef struct _GEV_EVT_REQUEST_INFO
	{
		uint16_t		ushRequestId;	// request id
		uint16_t		ushEventId;		// event id
		uint64_t		ullTimestamp;	// timestamp
		void*			pvPayload;		// payload buffer pointer
		uint32_t		uiReserved1;
		uint32_t		uiReserved2;
	} GEV_EVT_REQUEST_INFO, *PGEV_EVT_REQUEST_INFO;

	// Event request buffer information
	typedef struct _EVT_REQ_BUF_INFO
	{
		U3V_EVT_REQUEST_INFO sU3vInfo;
		GEV_EVT_REQUEST_INFO sGevInfo;
	} EVT_REQUEST_INFO, *PEVT_REQ_BUF_INFO;


	// GenICam error message
	typedef struct _CAM_GENICAM_ERR_MSG
	{
		const char	*pszDescription;		// Error description.
		const char	*pszSourceFileName;		// Filename in which the error occurred.
		uint32_t    uiSourceLine;			// Line number at which the error occurred.
	} CAM_GENICAM_ERR_MSG, *PCAM_GENICAM_ERR_MSG;

#if !defined (_WIN32)
	typedef void*	SIGNAL_HANDLE;

	#define CAM_SIGNAL_TIMEOUT_INFINITE	0xFFFFFFFF
#endif

	////////////////////////////////////////////////////////////////////////////////////////////////////////////////
	// System
	CAMAPI Sys_Initialize(CAM_TYPE eCamType = CAM_TYPE_ALL);
	CAMAPI Sys_Terminate(void);
	CAMAPI Sys_GetInformation(CAM_SYSTEM_INFO *psSysInfo);
	CAMAPI Sys_GetNumOfCameras(uint32_t *puiNum);

	CAMAPI Sys_GetGvcpParameters(uint32_t *puiUnicastTimeout, uint32_t *puiUnicastRetry, uint32_t *puiBroadcastTimeout);
	CAMAPI Sys_SetGvcpParameters(uint32_t uiUnicastTimeout, uint32_t uiUnicastRetry, uint32_t uiBroadcastTimeout);

#if !defined (_WIN32)
	CAMAPI Sys_CreateSignal(SIGNAL_HANDLE *phHandle);
	CAMAPI Sys_CloseSignal(SIGNAL_HANDLE hHandle);
	CAMAPI Sys_WaitForSignal(SIGNAL_HANDLE hHandle, uint32_t uiMillisecons);
	CAMAPI Sys_ResetSignal(SIGNAL_HANDLE hHandle);
#endif

	// Camera
	CAMAPI Cam_GetInformation(CAM_HANDLE hCam, uint32_t uiCamIdx, CAM_INFO *psCamInfo);
#if defined (_WIN32)
	CAMAPI Cam_Open(uint32_t uiCamIdx, CAM_HANDLE *phCam, HANDLE hRmv = NULL, bool8_t bUseGenICam = true, void *pvXml = NULL, CAM_ACCESS_MODE eAccessMode = CAM_ACCESS_MODE_CONTROL);
	CAMAPI Cam_OpenFromInfo(const char *pszSerialNo, const char *pszModelName, const char *pszUserDefinedName, CAM_HANDLE *phCam, HANDLE hRmv = NULL, bool8_t bUseGenICam = true, void *pvXml = NULL, CAM_ACCESS_MODE eAccessMode = CAM_ACCESS_MODE_CONTROL);
#else
	CAMAPI Cam_Open(uint32_t uiCamIdx, CAM_HANDLE *phCam, SIGNAL_HANDLE hRmv = NULL, bool8_t bUseGenICam = true, void *pvXml = NULL, CAM_ACCESS_MODE eAccessMode = CAM_ACCESS_MODE_CONTROL);
	CAMAPI Cam_OpenFromInfo(const char *pszSerialNo, const char *pszModelName, const char *pszUserDefinedName, CAM_HANDLE *phCam, SIGNAL_HANDLE hRmv = NULL, bool8_t bUseGenICam = true, void *pvXml = NULL, CAM_ACCESS_MODE eAccessMode = CAM_ACCESS_MODE_CONTROL);
#endif
	CAMAPI Cam_Close(CAM_HANDLE hCam);
	CAMAPI Cam_ReadReg(CAM_HANDLE hCam, uint64_t ullAdrs, uint32_t uiSizeQuadlet, void *pvData);
	CAMAPI Cam_WriteReg(CAM_HANDLE hCam, uint64_t ullAdrs, uint32_t uiSizeQuadlet, void *pvData);
	CAMAPI Cam_ResetPort(CAM_HANDLE hCam);
	CAMAPI Cam_GetHeartbeat(CAM_HANDLE hCam, bool8_t *pbEnable, uint32_t *puiHbTimeout);
	CAMAPI Cam_SetHeartbeat(CAM_HANDLE hCam, bool8_t bEnable, uint32_t uiHbTimeout);

	CAMAPI Cam_SaveParameter(CAM_HANDLE hCam, const char *pszFileName);
	CAMAPI Cam_LoadParameter(CAM_HANDLE hCam, const char *pszFileName, bool bEnableLoadDPC = false);

	CAMAPI Cam_AbortPipe(CAM_HANDLE hCam, CAM_IF_FLG eFlg);
	CAMAPI Cam_ResetPipe(CAM_HANDLE hCam, CAM_IF_FLG eFlg);

	// Stream
	CAMAPI Strm_Close(CAM_STRM_HANDLE hStrm);
	CAMAPI Strm_Start(CAM_STRM_HANDLE hStrm, CAM_ACQ_MODE_TYPE eAcqMode = CAM_ACQ_MODE_CONTINUOUS);
	CAMAPI Strm_Stop(CAM_STRM_HANDLE hStrm);
	CAMAPI Strm_Abort(CAM_STRM_HANDLE hStrm);

#if defined (_WIN32)
	CAMAPI Strm_OpenSimple(CAM_HANDLE hCam, CAM_STRM_HANDLE *phStrm, uint32_t *puiMaxPayloadSize, HANDLE hCmpEvt = NULL, uint32_t uiApiBufferCount = DEFAULT_API_BUFFER_CNT, uint32_t uiMaxPacketSize = 0);
#else
	CAMAPI Strm_OpenSimple(CAM_HANDLE hCam, CAM_STRM_HANDLE *phStrm, uint32_t *puiMaxPayloadSize, SIGNAL_HANDLE hCmpEvt = NULL, uint32_t uiApiBufferCount = DEFAULT_API_BUFFER_CNT, uint32_t uiMaxPacketSize = 0);
#endif
	CAMAPI Strm_ReadCurrentImage(CAM_STRM_HANDLE hStrm, void *pvBuf, uint32_t *puiSize, CAM_IMAGE_INFO *psImageInfo);
	CAMAPI Strm_GetCurrentBufferIndex(CAM_STRM_HANDLE hStrm, uint32_t *puiBufferIndex);
	CAMAPI Strm_LockBuffer(CAM_STRM_HANDLE hStrm, uint32_t uiBufferIndex, CAM_IMAGE_INFO *psImageInfo);
	CAMAPI Strm_UnlockBuffer(CAM_STRM_HANDLE hStrm, uint32_t uiBufferIndex);
	CAMAPI Strm_SetCallbackImageAcquired(CAM_STRM_HANDLE hStrm, void* pvContext, void (CALLBACK *pFunc)(CAM_HANDLE hRcvCam, CAM_STRM_HANDLE hRcvStrm, CAM_IMAGE_INFO *psImageInfo, uint32_t uiBufferIndex, void* pvRcvContext));
	CAMAPI Strm_SetCallbackImageError(CAM_STRM_HANDLE hStrm, void* pvContext, void (CALLBACK *pFunc)(CAM_HANDLE hRcvCam, CAM_STRM_HANDLE hRcvStrm, CAM_API_STATUS uiErrorStatus, uint32_t uiBufferIndex, void* pvRcvContext));
	CAMAPI Strm_SetCallbackBufferBusy(CAM_STRM_HANDLE hStrm, void* pvContext, void (CALLBACK *pFunc)(CAM_HANDLE hRcvCam, CAM_STRM_HANDLE hRcvStrm, uint32_t uiBufferIndex, void* pvRcvContext));

#if defined (_WIN32)
	CAMAPI Strm_Open(CAM_HANDLE hCam, HANDLE hCmpEvt, uint32_t *puiMaxPayloadSize, CAM_STRM_HANDLE *phStrm, uint32_t uiMaxPacketSize = 0);
#else
	CAMAPI Strm_Open(CAM_HANDLE hCam, SIGNAL_HANDLE hCmpEvt, uint32_t *puiMaxPayloadSize, CAM_STRM_HANDLE *phStrm, uint32_t uiMaxPacketSize = 0);
#endif
	CAMAPI Strm_CreateRequest(CAM_STRM_HANDLE hStrm, void *pvPayloadBuf, uint32_t uiPayloadSize, CAM_STRM_REQUEST_HANDLE *phStrmRequest);
	CAMAPI Strm_ReleaseRequest(CAM_STRM_HANDLE hStrm, CAM_STRM_REQUEST_HANDLE hStrmRequest);
	CAMAPI Strm_EnqueueRequest(CAM_STRM_HANDLE hStrm, CAM_STRM_REQUEST_HANDLE hStrmRequest);
	CAMAPI Strm_DequeueRequest(CAM_STRM_HANDLE hStrm, CAM_STRM_REQUEST_HANDLE *phStrmRequest, void **ppvPayloadBuf, uint32_t *puiPayloadSize);
	CAMAPI Strm_FlushWaitQueue(CAM_STRM_HANDLE hStrm);
	CAMAPI Strm_GetStrmReqInfo(CAM_STRM_HANDLE hStrm, CAM_STRM_REQUEST_HANDLE hStrmRequest, CAM_STRM_REQUEST_INFO *psStrmReqInfo);

#if defined (_WIN32)
	CAMAPI Strm_GetGevStatistics(CAM_STRM_HANDLE hStrm, GEV_STRM_STATS* psStats);
#endif

	// Event
	CAMAPI Evt_OpenSimple(CAM_HANDLE hCam, CAM_EVT_HANDLE *phEvt, uint32_t uiApiBufferCount = DEFAULT_API_BUFFER_CNT);
#if defined (_WIN32)
	CAMAPI Evt_Activate(CAM_EVT_HANDLE hEvt, const char *pszEvtName, HANDLE hCmpEvt);
#else
	CAMAPI Evt_Activate(CAM_EVT_HANDLE hEvt, const char *pszEvtName, SIGNAL_HANDLE hCmpEvt);
#endif
	CAMAPI Evt_Deactivate(CAM_EVT_HANDLE hEvt, const char *pszEvtName);

#if defined (_WIN32)
	CAMAPI Evt_Open(CAM_HANDLE hCam, CAM_EVT_HANDLE *phEvt, uint32_t *puiMaxPayloadSize, HANDLE hCmpEvt = NULL);
#else
	CAMAPI Evt_Open(CAM_HANDLE hCam, CAM_EVT_HANDLE *phEvt, uint32_t *puiMaxPayloadSize, SIGNAL_HANDLE hCmpEvt = NULL);
#endif
	CAMAPI Evt_CreateRequest(CAM_EVT_HANDLE hEvt, void *pvPayloadBuf, uint32_t uiPayloadSize, CAM_EVT_REQUEST_HANDLE *phEvtRequest);
	CAMAPI Evt_ReleaseRequest(CAM_EVT_HANDLE hEvt, CAM_EVT_REQUEST_HANDLE hEvtRequest);
	CAMAPI Evt_EnqueueRequest(CAM_EVT_HANDLE hEvt, CAM_EVT_REQUEST_HANDLE hEvtRequest);
	CAMAPI Evt_DequeueRequest(CAM_EVT_HANDLE hEvt, CAM_EVT_REQUEST_HANDLE *phEvtRequest, EVT_REQUEST_INFO *psEvtReqInfo);
	CAMAPI Evt_FlushWaitQueue(CAM_EVT_HANDLE hEvt);

	CAMAPI Evt_Close(CAM_EVT_HANDLE hEvt);
#if defined (_WIN32)
	CAMAPI Evt_ActivateCallback(CAM_EVT_HANDLE hEvt, const char *pszEvtName, void* pvContext, void (CALLBACK *pFunc)(CAM_HANDLE hRcvCam, CAM_EVT_HANDLE hRcvEvt, void* pvRcvContext));
#endif

	// Node
	CAMAPI Nd_GetNode(CAM_HANDLE hCam, const char *pszName, CAM_NODE_HANDLE *phNode);
	CAMAPI Nd_GetType(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, TC_NODE_TYPE *peNodeType);
	CAMAPI Nd_GetNumOfFeatures(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, uint32_t *puiNum);
	CAMAPI Nd_GetFeatureByIndex(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, uint32_t uiNodeIndex, CAM_NODE_HANDLE *phNode);
	CAMAPI Nd_GetName(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, CAM_NODE_NAME *pszNodeName);
	CAMAPI Nd_GetAccessMode(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, TC_NODE_ACCESS_MODE *peAccessMode);
	CAMAPI Nd_GetVisibility(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, TC_NODE_VISIBILITY *peVisibility);
	CAMAPI Nd_GetCachingMode(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, TC_NODE_CACHING_MODE *peCachingMode);
	CAMAPI Nd_GetDescription(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, char *pszBuf, uint32_t *puiSize);
	CAMAPI Nd_GetToolTip(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, char *pszBuf, uint32_t *puiSize);
	CAMAPI Nd_GetRepresentation(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, TC_NODE_REPRESENTATION *peRepresentation);
	CAMAPI Nd_GetUnit(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, char *pszBuf, uint32_t *puiSize);

	// Node Integer
	CAMAPI Nd_GetIntMin(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t *pllMin);
	CAMAPI Nd_GetIntMax(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t *pllMax);
	CAMAPI Nd_GetIntInc(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t *pllInc);
	CAMAPI Nd_GetIntValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t *pllValue, bool8_t bVerify = false, bool8_t bIgnoreCache = false);
	CAMAPI Nd_SetIntValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t llValue, bool8_t bVerify = true);

	// Node Float
	CAMAPI Nd_GetFloatMin(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, float64_t *pdMin);
	CAMAPI Nd_GetFloatMax(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, float64_t *pdMax);
	CAMAPI Nd_GetFloatHasInc(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, bool8_t *pbInc);
	CAMAPI Nd_GetFloatInc(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, float64_t *pdInc);
	CAMAPI Nd_GetFloatDisplayNotation(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, TC_NODE_DISPLAY_NOTATION *peDisplayNotation);
	CAMAPI Nd_GetFloatDisplayPrecision(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t *pllPrecision);
	CAMAPI Nd_GetFloatValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, float64_t *pdValue, bool8_t bVerify = false, bool8_t bIgnoreCache = false);
	CAMAPI Nd_SetFloatValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, float64_t dValue, bool8_t bVerify = true);

	// Node Boolean
	CAMAPI Nd_GetBoolValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, bool8_t *pbValue, bool8_t bVerify = false, bool8_t bIgnoreCache = false);
	CAMAPI Nd_SetBoolValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, bool8_t bValue, bool8_t bVerify = true);

	// Node Enumeration
	CAMAPI Nd_GetNumOfEnumEntries(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, uint32_t *piNum);
	CAMAPI Nd_GetEnumIntValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t *pllValue, bool8_t bVerify = false, bool8_t bIgnoreCache = false);
	CAMAPI Nd_SetEnumIntValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t llValue, bool8_t bVerify = true);
	CAMAPI Nd_GetEnumStrValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, char *pszBuf, uint32_t *puiSize, bool8_t bVerify = false, bool8_t bIgnoreCache = false);
	CAMAPI Nd_SetEnumStrValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, const char *pszBuf, bool8_t bVerify = true);
	CAMAPI Nd_GetEnumEntryByIndex(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, uint32_t uiEnumIdx, CAM_NODE_HANDLE *phEnumEntryNode);
	CAMAPI Nd_GetEnumEntryIntValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, int64_t *pllValue);
	CAMAPI Nd_GetEnumEntryStrValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, char *pszBuf, uint32_t *puiSize);

	// Node Command
	CAMAPI Nd_CmdExecute(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, bool8_t bVerify = true);
	CAMAPI Nd_GetCmdIsDone(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, bool8_t *pbDone, bool8_t bVerify = false);

	// Node String
	CAMAPI Nd_GetStrValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, char *pszBuf, uint32_t *puiSize, bool8_t bVerify = false, bool8_t bIgnoreCache = false);
	CAMAPI Nd_SetStrValue(CAM_HANDLE hCam, CAM_NODE_HANDLE hNode, const char *pszBuf, bool8_t bVerify = true);

	CAMAPI Chunk_AttachBuffer(CAM_STRM_HANDLE hStrm, void *pvPayloadBuf, uint32_t uiPayloadSize);

	CAMAPI Misc_GetLastGenICamError(CAM_GENICAM_ERR_MSG *psErrMsg);

	////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

	//
	// Camera Control

	// ImageFormatControl
	CAMAPI GetCamImageFormatSelector(CAM_HANDLE hCam, CAM_IMAGE_FORMAT_SELECTOR_TYPE *peFormat);
	CAMAPI SetCamImageFormatSelector(CAM_HANDLE hCam, CAM_IMAGE_FORMAT_SELECTOR_TYPE eFormat);

	// Scalable
	CAMAPI GetCamSensorWidth(CAM_HANDLE hCam, uint32_t *puiSensorWidth);
	CAMAPI GetCamSensorHeight(CAM_HANDLE hCam, uint32_t *puiSensorHeight);
	CAMAPI GetCamRoi(CAM_HANDLE hCam, uint32_t *puiWidth, uint32_t *puiHeight, uint32_t *puiOffsetX, uint32_t *puiOffsetY);
	CAMAPI SetCamRoi(CAM_HANDLE hCam, uint32_t uiWidth, uint32_t uiHeight, uint32_t uiOffsetX, uint32_t uiOffsetY);
	CAMAPI GetCamWidthMinMax(CAM_HANDLE hCam, uint32_t *puiWidthMin, uint32_t *puiWidthMax, uint32_t *puiWidthInc);
	CAMAPI GetCamWidth(CAM_HANDLE hCam, uint32_t *puiWidth);
	CAMAPI SetCamWidth(CAM_HANDLE hCam, uint32_t uiWidth);
	CAMAPI GetCamHeightMinMax(CAM_HANDLE hCam, uint32_t *puiHeightMin, uint32_t *puiHeightMax, uint32_t *puiHeightInc);
	CAMAPI GetCamHeight(CAM_HANDLE hCam, uint32_t *puiHeight);
	CAMAPI SetCamHeight(CAM_HANDLE hCam, uint32_t uiHeight);
	CAMAPI GetCamOffsetXMinMax(CAM_HANDLE hCam, uint32_t *puiOffsetXMin, uint32_t *puiOffsetXMax, uint32_t *puiOffsetXInc);
	CAMAPI GetCamOffsetX(CAM_HANDLE hCam, uint32_t *puiOffsetX);
	CAMAPI SetCamOffsetX(CAM_HANDLE hCam, uint32_t uiOffsetX);
	CAMAPI GetCamOffsetYMinMax(CAM_HANDLE hCam, uint32_t *puiOffsetYMin, uint32_t *puiOffsetYMax, uint32_t *puiOffsetYInc);
	CAMAPI GetCamOffsetY(CAM_HANDLE hCam, uint32_t *puiOffsetY);
	CAMAPI SetCamOffsetY(CAM_HANDLE hCam, uint32_t uiOffsetY);

	// Binning
	CAMAPI GetCamBinningHorizontalMinMax(CAM_HANDLE hCam, uint32_t *puiMin, uint32_t *puiMax);
	CAMAPI GetCamBinningHorizontal(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI SetCamBinningHorizontal(CAM_HANDLE hCam, uint32_t uiValue);
	CAMAPI GetCamBinningVerticalMinMax(CAM_HANDLE hCam, uint32_t *puiMin, uint32_t *puiMax);
	CAMAPI GetCamBinningVertical(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI SetCamBinningVertical(CAM_HANDLE hCam, uint32_t uiValue);

	// Decimation
	CAMAPI GetCamDecimationHorizontalMinMax(CAM_HANDLE hCam, uint32_t *puiMin, uint32_t *puiMax);
	CAMAPI GetCamDecimationHorizontal(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI SetCamDecimationHorizontal(CAM_HANDLE hCam, uint32_t uiValue);
	CAMAPI GetCamDecimationVerticalMinMax(CAM_HANDLE hCam, uint32_t *puiMin, uint32_t *puiMax);
	CAMAPI GetCamDecimationVertical(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI SetCamDecimationVertical(CAM_HANDLE hCam, uint32_t uiValue);

	// Reverse
	CAMAPI GetCamReverseX(CAM_HANDLE hCam, bool8_t *pbValue);
	CAMAPI SetCamReverseX(CAM_HANDLE hCam, bool8_t bValue);
	CAMAPI GetCamReverseY(CAM_HANDLE hCam, bool8_t *pbValue);
	CAMAPI SetCamReverseY(CAM_HANDLE hCam, bool8_t bValue);

	// PixelFormat
	CAMAPI GetCamPixelFormat(CAM_HANDLE hCam, CAM_PIXEL_FORMAT *puiPixelFormat);
	CAMAPI SetCamPixelFormat(CAM_HANDLE hCam, CAM_PIXEL_FORMAT uiPixelFormat);

	// TestPattern
	CAMAPI GetCamTestPattern(CAM_HANDLE hCam, CAM_TEST_PATTERN_TYPE *peTestPattern);
	CAMAPI SetCamTestPattern(CAM_HANDLE hCam, CAM_TEST_PATTERN_TYPE eTestPattern);

	// AcquisitionControl
	CAMAPI GetCamStreamPayloadSize(CAM_HANDLE hCam, uint32_t *puiPayloadSize);
	CAMAPI GetCamStreamEnable(CAM_HANDLE hCam, bool8_t* pbEnable);
	CAMAPI GetCamAcquisitionFrameCountMinMax(CAM_HANDLE hCam, uint32_t *puiAcqFrameCountMin, uint32_t *puiAcqFrameCountMax);
	CAMAPI GetCamAcquisitionFrameCount(CAM_HANDLE hCam, uint32_t *puiAcqFrameCount);
	CAMAPI SetCamAcquisitionFrameCount(CAM_HANDLE hCam, uint32_t uiAcqFrameCount);
	CAMAPI GetCamAcquisitionFrameRateControl(CAM_HANDLE hCam, CAM_ACQ_FRAME_RATE_CTRL_TYPE *peFrameRateControl);
	CAMAPI SetCamAcquisitionFrameRateControl(CAM_HANDLE hCam, CAM_ACQ_FRAME_RATE_CTRL_TYPE eFrameRateControl);
	CAMAPI GetCamAcquisitionFrameRateMinMax(CAM_HANDLE hCam, float64_t *pdAcqFrameRateMin, float64_t *pdAcqFrameRateMax);
	CAMAPI GetCamAcquisitionFrameRate(CAM_HANDLE hCam, float64_t *pdAcqFrameRate);
	CAMAPI SetCamAcquisitionFrameRate(CAM_HANDLE hCam, float64_t dAcqrameRate);

	// ImageBuffer
	CAMAPI GetCamImageBufferMode(CAM_HANDLE hCam, CAM_IMAGE_BUFFER_MODE_TYPE *peMode);
	CAMAPI SetCamImageBufferMode(CAM_HANDLE hCam, CAM_IMAGE_BUFFER_MODE_TYPE eMode);
	CAMAPI GetCamImageBufferFrameCount(CAM_HANDLE hCam, uint32_t *puiCount);
	CAMAPI ExecuteCamImageBufferRead(CAM_HANDLE hCam);

	// TriggerControl
	CAMAPI GetCamTriggerMode(CAM_HANDLE hCam, bool8_t *pbValue);
	CAMAPI SetCamTriggerMode(CAM_HANDLE hCam, bool8_t bValue);
	CAMAPI GetCamTriggerSequence(CAM_HANDLE hCam, CAM_TRIGGER_SEQUENCE_TYPE *peTriggerSequence);
	CAMAPI SetCamTriggerSequence(CAM_HANDLE hCam, CAM_TRIGGER_SEQUENCE_TYPE eTriggerSequence);
	CAMAPI GetCamTriggerSource(CAM_HANDLE hCam, CAM_TRIGGER_SOURCE_TYPE *peTriggerSource);
	CAMAPI SetCamTriggerSource(CAM_HANDLE hCam, CAM_TRIGGER_SOURCE_TYPE eTriggerSource);
	CAMAPI GetCamTriggerAdditionalParameterMinMax(CAM_HANDLE hCam, uint32_t *puiAdditionalParameterMin, uint32_t *puiAdditionalParameterMax);
	CAMAPI GetCamTriggerAdditionalParameter(CAM_HANDLE hCam, uint32_t *puiAdditionalParameter);
	CAMAPI SetCamTriggerAdditionalParameter(CAM_HANDLE hCam, uint32_t uiAdditionalParameter);
	CAMAPI GetCamTriggerDelayMinMax(CAM_HANDLE hCam, float64_t *pdDealyUsMin, float64_t *pdDealyUsMax);
	CAMAPI GetCamTriggerDelay(CAM_HANDLE hCam, float64_t *pdDealyUs);
	CAMAPI SetCamTriggerDelay(CAM_HANDLE hCam, float64_t dDelayUs);
	CAMAPI ExecuteCamSoftwareTrigger(CAM_HANDLE hCam);

	CAMAPI GetCamTriggerActivation(CAM_HANDLE hCam, CAM_TRIGGER_ACTIVATION_TYPE *peTriggerActivation);
	CAMAPI SetCamTriggerActivation(CAM_HANDLE hCam, CAM_TRIGGER_ACTIVATION_TYPE eTriggerActivation);

	// ExposureTime
	CAMAPI GetCamExposureTimeControl(CAM_HANDLE hCam, CAM_EXPOSURE_TIME_CONTROL_TYPE *peExpControl);
	CAMAPI SetCamExposureTimeControl(CAM_HANDLE hCam, CAM_EXPOSURE_TIME_CONTROL_TYPE eExpControl);
	CAMAPI GetCamExposureTimeMinMax(CAM_HANDLE hCam, float64_t *pdExpTimeUsMin, float64_t *pdExpTimeUsMax);
	CAMAPI GetCamExposureTime(CAM_HANDLE hCam, float64_t *pdExpTimeUs);
	CAMAPI SetCamExposureTime(CAM_HANDLE hCam, float64_t dExpTimeUs);

	// DigitalIoControl
	CAMAPI GetCamLineModeAll(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI SetCamLineModeAll(CAM_HANDLE hCam, uint32_t uiValue);
	CAMAPI GetCamLineInverterAll(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI SetCamLineInverterAll(CAM_HANDLE hCam, uint32_t uiValue);
	CAMAPI GetCamLineStatusAll(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI GetCamUserOutputValueAll(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI SetCamUserOutputValueAll(CAM_HANDLE hCam, uint32_t uiValue);
	CAMAPI GetCamLineSource(CAM_HANDLE hCam, CAM_LINE_SELECTOR_TYPE eLineSelector, CAM_LINE_SOURCE_TYPE *peLineSource);
	CAMAPI SetCamLineSource(CAM_HANDLE hCam, CAM_LINE_SELECTOR_TYPE eLineSelector, CAM_LINE_SOURCE_TYPE eLineSource);

	// TimerConrtol
	CAMAPI GetCamTimerDurationMinMax(CAM_HANDLE hCam, float64_t *pdTimerDurationMin, float64_t *pdTimerDurationMax);
	CAMAPI GetCamTimerDuration(CAM_HANDLE hCam, float64_t *pdTimerDuration);
	CAMAPI SetCamTimerDuration(CAM_HANDLE hCam, float64_t dTimerDuration);
	CAMAPI GetCamTimerDelayMinMax(CAM_HANDLE hCam, float64_t *pdTimerDelayMin, float64_t *pdTimerDelayMax);
	CAMAPI GetCamTimerDelay(CAM_HANDLE hCam, float64_t *pdTimerDelay);
	CAMAPI SetCamTimerDelay(CAM_HANDLE hCam, float64_t dTimerDelay);
	CAMAPI GetCamTimerTriggerSource(CAM_HANDLE hCam, CAM_TIMER_TRIGGER_SOURCE_TYPE *peTimerTriggerSource);
	CAMAPI SetCamTimerTriggerSource(CAM_HANDLE hCam, CAM_TIMER_TRIGGER_SOURCE_TYPE eTimerTriggerSource);

	// Gain
	CAMAPI GetCamGainMinMax(CAM_HANDLE hCam, float64_t *pdGainMin, float64_t *pdGainMax);
	CAMAPI GetCamGain(CAM_HANDLE hCam, float64_t *pdGain);
	CAMAPI SetCamGain(CAM_HANDLE hCam, float64_t dGain);
	CAMAPI GetCamGainAuto(CAM_HANDLE hCam, CAM_GAIN_AUTO_TYPE *peGainAuto);
	CAMAPI SetCamGainAuto(CAM_HANDLE hCam, CAM_GAIN_AUTO_TYPE eGainAuto);

	// BlackLevel
	CAMAPI GetCamBlackLevelMinMax(CAM_HANDLE hCam, float64_t *pdBlackLevelMin, float64_t *pdBlackLevelMax);
	CAMAPI GetCamBlackLevel(CAM_HANDLE hCam, float64_t *pdBlackLevel);
	CAMAPI SetCamBlackLevel(CAM_HANDLE hCam, float64_t dBlackLevel);

	// Gamma
	CAMAPI GetCamGammaMinMax(CAM_HANDLE hCam, float64_t *pdGammaMin, float64_t *pdGammaMax);
	CAMAPI GetCamGamma(CAM_HANDLE hCam, float64_t *pdGamma);
	CAMAPI SetCamGamma(CAM_HANDLE hCam, float64_t dGamma);

	// BalanceRatio
	CAMAPI GetCamBalanceRatioMinMax(CAM_HANDLE hCam, CAM_BALANCE_RATIO_SELECTOR_TYPE eSelector, float64_t *pdBalanceRatioMin, float64_t *pdBalanceRatioMax);
	CAMAPI GetCamBalanceRatio(CAM_HANDLE hCam, CAM_BALANCE_RATIO_SELECTOR_TYPE eSelector, float64_t *pdBalanceRatio);
	CAMAPI SetCamBalanceRatio(CAM_HANDLE hCam, CAM_BALANCE_RATIO_SELECTOR_TYPE eSelector, float64_t dBalanceRatio);

	// BalanceWhiteAuto
	CAMAPI GetCamBalanceWhiteAuto(CAM_HANDLE hCam, CAM_BALANCE_WHITE_AUTO_TYPE *peBalanceWhiteAuto);
	CAMAPI SetCamBalanceWhiteAuto(CAM_HANDLE hCam, CAM_BALANCE_WHITE_AUTO_TYPE eBalanceWhiteAuto);

	// Hue
	CAMAPI GetCamHueMinMax(CAM_HANDLE hCam, float64_t *pdHueMin, float64_t *pdHueMax);
	CAMAPI GetCamHue(CAM_HANDLE hCam, float64_t *pdHue);
	CAMAPI SetCamHue(CAM_HANDLE hCam, float64_t dHue);

	// Saturation
	CAMAPI GetCamSaturationMinMax(CAM_HANDLE hCam, float64_t *pdSaturationMin, float64_t *pdSaturationMax);
	CAMAPI GetCamSaturation(CAM_HANDLE hCam, float64_t *pdSaturation);
	CAMAPI SetCamSaturation(CAM_HANDLE hCam, float64_t dSaturation);

	// Sharpness
	CAMAPI GetCamSharpnessMinMax(CAM_HANDLE hCam, uint32_t *puiSharpnessMin, uint32_t *puiSharpnessMax);
	CAMAPI GetCamSharpness(CAM_HANDLE hCam, uint32_t *puiSharpness);
	CAMAPI SetCamSharpness(CAM_HANDLE hCam, uint32_t uiSharpness);

	// ColorCorrectionMatrix
	CAMAPI GetCamColorCorrectionMatrixMinMax(CAM_HANDLE hCam, CAM_COLOR_CORRECTION_MATRIX_TYPE eType, float64_t *pdMatrixMin, float64_t *pdMatrixMax);
	CAMAPI GetCamColorCorrectionMatrix(CAM_HANDLE hCam, CAM_COLOR_CORRECTION_MATRIX_TYPE eType, float64_t *pdMatrix);
	CAMAPI SetCamColorCorrectionMatrix(CAM_HANDLE hCam, CAM_COLOR_CORRECTION_MATRIX_TYPE eType, float64_t dMatrix);

	// LUTControl
	CAMAPI GetCamLutEnable(CAM_HANDLE hCam, bool8_t *pbEnable);
	CAMAPI SetCamLutEnable(CAM_HANDLE hCam, bool8_t bEnable);
	CAMAPI GetCamLutValue(CAM_HANDLE hCam, uint32_t uiLutIndex, uint32_t *puiLutValue);
	CAMAPI SetCamLutValue(CAM_HANDLE hCam, uint32_t uiLutIndex, uint32_t uiLutValue);

	// UserSetControl
	CAMAPI ExecuteCamUserSetLoad(CAM_HANDLE hCam, CAM_USER_SET_SELECTOR_TYPE eSelector);
	CAMAPI ExecuteCamUserSetSave(CAM_HANDLE hCam, CAM_USER_SET_SELECTOR_TYPE eSelector);
	CAMAPI ExecuteCamUserSetQuickSave(CAM_HANDLE hCam, CAM_USER_SET_SELECTOR_TYPE eSelector);
	CAMAPI GetCamUserSetDefault(CAM_HANDLE hCam, CAM_USER_SET_SELECTOR_TYPE *peSelector);
	CAMAPI SetCamUserSetDefault(CAM_HANDLE hCam, CAM_USER_SET_SELECTOR_TYPE eSelector);
	CAMAPI ExecuteCamUserSetSaveAndSetDefault(CAM_HANDLE hCam, CAM_USER_SET_SELECTOR_TYPE eSelector);

	// SequentialShutterControl
	CAMAPI GetCamSequentialShutterEnable(CAM_HANDLE hCam, bool8_t *pbEnable);
	CAMAPI SetCamSequentialShutterEnable(CAM_HANDLE hCam, bool8_t bEnable);
	CAMAPI GetCamSequentialShutterTerminateAtMinMax(CAM_HANDLE hCam, uint32_t *puiMin, uint32_t *puiMax);
	CAMAPI GetCamSequentialShutterTerminateAt(CAM_HANDLE hCam, uint32_t *puiValue);
	CAMAPI SetCamSequentialShutterTerminateAt(CAM_HANDLE hCam, uint32_t uiValue);
	CAMAPI GetCamSequentialShutterIndexMinMax(CAM_HANDLE hCam, uint32_t *puiMin, uint32_t *puiMax);
	CAMAPI GetCamSequentialShutterEntryMinMax(CAM_HANDLE hCam, uint32_t *puiMin, uint32_t *puiMax);
	CAMAPI GetCamSequentialShutterEntry(CAM_HANDLE hCam, uint32_t uiIndex, uint32_t *puiEntry);
	CAMAPI SetCamSequentialShutterEntry(CAM_HANDLE hCam, uint32_t uiIndex, uint32_t uiEntry);

	// UserDefinedName
	CAMAPI GetCamUserDefinedName(CAM_HANDLE hCam, char *pszName, uint32_t *puiSize);
	CAMAPI SetCamUserDefinedName(CAM_HANDLE hCam, char *pszName);

	// ChunkDataControl
	CAMAPI GetCamChunkModeActive(CAM_HANDLE hCam, bool8_t *pbValue);
	CAMAPI SetCamChunkModeActive(CAM_HANDLE hCam, bool8_t bValue);

	// AntiGlitch
	CAMAPI GetCamAntiGlitchMinMax(CAM_HANDLE hCam, float64_t *pdValueMin, float64_t *pdValueMax);
	CAMAPI GetCamAntiGlitch(CAM_HANDLE hCam, float64_t *pdValue);
	CAMAPI SetCamAntiGlitch(CAM_HANDLE hCam, float64_t dValue);

	// AntiChattering
	CAMAPI GetCamAntiChatteringMinMax(CAM_HANDLE hCam, float64_t *pdValueMin, float64_t *pdValueMax);
	CAMAPI GetCamAntiChattering(CAM_HANDLE hCam, float64_t *pdValue);
	CAMAPI SetCamAntiChattering(CAM_HANDLE hCam, float64_t dValue);

	// Others
	CAMAPI GetCamIndexFromCamHandle(CAM_HANDLE hCam, uint32_t *puiCamIndex);
	CAMAPI GetCamTypeFromCamHandle(CAM_HANDLE hCam, CAM_TYPE *peType);
	CAMAPI GetCamTLParamsLocked(CAM_HANDLE hCam, uint32_t *puiValue);



	// FrameSynchronization
	CAMAPI GetCamFrameSynchronization(CAM_HANDLE hCam, CAM_FRAME_SYNCHRONIZATION_TYPE *peSync);
	CAMAPI SetCamFrameSynchronization(CAM_HANDLE hCam, CAM_FRAME_SYNCHRONIZATION_TYPE eSync);

	// DPCControl
	CAMAPI GetCamDpcEnable(CAM_HANDLE hCam, bool8_t *pbEnable);
	CAMAPI SetCamDpcEnable(CAM_HANDLE hCam, bool8_t bEnable);
	CAMAPI GetCamDpcNumber(CAM_HANDLE hCam, uint32_t *puiNumber);
	CAMAPI SetCamDpcNumber(CAM_HANDLE hCam, uint32_t uiNumber);
	CAMAPI GetCamDpcPosition(CAM_HANDLE hCam, uint32_t uiDpcIndex, uint32_t *puiEntryX, uint32_t *puiEntryY);
	CAMAPI SetCamDpcPosition(CAM_HANDLE hCam, uint32_t uiDpcIndex, uint32_t uiEntryX, uint32_t uiEntryY);

}	// end of namespace Teli

#endif //_TELICAMAPI_H_

