///////////////////////////////////////////////////////////////////////////////
// file    : TeliCamUtl.h
// brief   : Teli camera utility dll.
// version : 1.1.1.0
// Author  : (C)2014 - 2016 TOSHIBA TELI CORPORATION 
// Date    : 2016/03/09
//  * Appended JPEG format image saving methods.
//
// version : 1.0.0.0
// author  : (C)2014 TOSHIBA TELI CORPORATION 
// date    : 2014/09/02
// TeliCamUtl.h

#ifndef _TELICAMUTL_H_
#define _TELICAMUTL_H_


#include <windows.h>
#include "TeliCamApi.h"

namespace Teli
{

	#ifdef CAMUTL_EXPORTS
		#define TELICAMUTL_API
	#else
		#define TELICAMUTL_API __declspec(dllimport)
	#endif


	// 
	#ifdef __cplusplus
		#ifndef EXTERN_C
			#define EXTERN_C extern "C"
		#endif
	#else
		#ifndef EXTERN_C
			#define EXTERN_C
		#endif
	#endif


	#ifndef IMGAPI
	#define IMGAPI EXTERN_C TELICAMUTL_API CAM_API_STATUS _stdcall
	#endif  IMGAPI

	#ifndef IMGAPIINT
	#define IMGAPIINT  EXTERN_C TELICAMUTL_API int32_t _stdcall
	#endif  IMGAPIINT

	#ifndef IMGAPIUINT
	#define IMGAPIUINT EXTERN_C TELICAMUTL_API uint32_t _stdcall
	#endif  IMGAPIUINT

	#ifndef IMGAPIBYTE
	#define IMGAPIBYTE EXTERN_C TELICAMUTL_API uint8_t _stdcall
	#endif  IMGAPIBYTE

	#ifndef IMGAPIBOOL
	#define IMGAPIBOOL EXTERN_C TELICAMUTL_API bool8_t _stdcall
	#endif  IMGAPIBOOL

	#ifndef IMGAPIPFMT
	#define IMGAPIPFMT EXTERN_C TELICAMUTL_API CAM_PIXEL_FORMAT _stdcall
	#endif  IMGAPIPFMT



	enum _DST_FORMAT
	{
		DST_FMT_BGRA32		=   0,		// BGRA 32bit format (  0)	
		DST_FMT_BGR24		=   1,		// BGR  24bit format (  1)
		DST_FMT_BGR24PAD	=   2,		// BGR  24bit format (  2)						// Appended. v1.1.0.0
	};
	typedef uint32_t  DST_FORMAT;

	// Initialize.
	IMGAPI PrepareLUT();																		// Prepares Look up table for Yuv -> BGR conversion. Call this function once before using YUV type ARGB converter.			
	
	//Utility
	IMGAPIBYTE BitPerPixel		(CAM_PIXEL_FORMAT  uiPixelFormat);								// Gets bit per pixel data.
	IMGAPIBYTE DataDepth		(CAM_PIXEL_FORMAT  uiPixelFormat);								// Gets data depth of color component or pixel data.
	IMGAPIBOOL IsMonochromic	(CAM_PIXEL_FORMAT  uiPixelFormat);								// If monochrome format, returns true. False will be returned when bayer type PixelFormat is speccified.
	IMGAPIBOOL IsPixelBayer		(CAM_PIXEL_FORMAT  uiPixelFormat);								// If bayer type format, returns true.
//	IMGAPI GetAvailablePxlFmts	(CAM_HANDLE hCam, CAM_PIXEL_FORMAT *auiPxlFmt, int *piCount);	// Gets pixel formats available in the camera.
	IMGAPIPFMT GetPxlFmt		(uint32_t uiPxlCoding, uint32_t uiPxlSize);						// Gets pixel formats corresponding to the argument PixelCoding and PixelSize value.

	IMGAPI SaveBmpARGB	(void *pvTgt, uint32_t uiWidth, uint32_t uiHeight, const char *pszPath);// Saves image as ARGB 32bit bitmap. 
	IMGAPI SaveBmpRGB	(void *pvTgt, uint32_t uiWidth, uint32_t uiHeight, const char *pszPath);// Saves image as  RGB 24bit bitmap.
	IMGAPI SaveBmpMono	(void *pvTgt, uint32_t uiWidth, uint32_t uiHeight, const char *pszPath);// Saves image as monochrome 8nit bitmap. 

	// Appended JPeg saving functions. v1.1.0.0
	IMGAPI SaveJpeg		(void *pvTgt, DST_FORMAT eSrcFmt, uint32_t uiWidth, uint32_t uiHeight,
						 const char *pszPath);													// Saves image as Jpeg file. 
	IMGAPI SaveJpegQ	(void *pvTgt, DST_FORMAT eSrcFmt, uint32_t uiQuality,
						 uint32_t uiWidth, uint32_t uiHeight, const char *pszPath);				// Saves image as Jpeg file. 
	IMGAPI SaveJpegRaw	(void *pvRaw, CAM_PIXEL_FORMAT uiPxlFmtRaw,
						 uint32_t uiWidth, uint32_t uiHeight, const char *pszPath);				// Saves image as Jpeg file. 
	IMGAPI SaveJpegRQ	(void *pvRaw, CAM_PIXEL_FORMAT uiPxlFmtRaw, uint32_t uiQuality,
						 uint32_t uiWidth, uint32_t uiHeight, const char *pszPath);				// Saves image as Jpeg file. 
	
	IMGAPI SaveRWH		(void *pvTgt, CAM_PIXEL_FORMAT uiPixelFormat,
						 uint32_t uiWidth, uint32_t uiHeight, const char *pszPath);				// Saves image as original format "Raw data With Header" data. 
	IMGAPI LoadRWH		(const char *pszPath, void **ppTgt, CAM_PIXEL_FORMAT *puiPixelFormat = NULL,
						 uint32_t *puiWidth = NULL, uint32_t *puiHeight = NULL,
						 uint32_t *puiStride = NULL);											// Loads original format "Raw data With Header" data as image.
	
	// Reverses image using processing mode (multi-thread or single thread) specified with SetProcMode().		 // Appended multi thread processing mode. v1.1.0.0.
	IMGAPI ReverseImg	(void *pvDst, void *pvSrc, CAM_PIXEL_FORMAT uiPixelFormat,
						 uint32_t uiWidth, uint32_t uiHeight,  bool bRevX, bool bRevY);

	// Converts PixelFormat using processing mode (multi-thread or single thread) specified with SetProcMode(). // Appended multi thread processing mode. v1.1.0.0.
	IMGAPI ConvImage	(DST_FORMAT eDstFormat, CAM_PIXEL_FORMAT uiSrcPixelFormat,
						 bool bBayerConversion, void *pvDst, void *pvSrc,
						 uint32_t uiWidth, uint32_t uiHeight);
	// Expanded PixelFormat Converter. User application can specify bayer conversion mode, processing mode, and row padding mode. //Appended v1.1.0.0
	IMGAPI ConvImageEx	(DST_FORMAT eDstFormat, CAM_PIXEL_FORMAT uiSrcPixelFormat,
						 void *pvDst, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight,
						 uint32_t uiBayerCnv = 0, bool8_t bMultProc = TRUE, bool8_t bPadSrc = FALSE);

	// Rectangle area converter for bayer 8 bit source image. (pixel data depth : 8bit)  
	IMGAPI ConvBayerRect_ACPI(DST_FORMAT eDstFormat, CAM_PIXEL_FORMAT uiSrcPxlFmt,
						void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
						 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
						 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD);

	// Expanded rectangle area converter for bayer 8bit source iamge. (pixel data depth : 8bit)  
	IMGAPI ConvBayerRectEx_ACPI(DST_FORMAT eDstFormat, CAM_PIXEL_FORMAT uiSrcPxeFmt,
						void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
						 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
						 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
						 bool8_t bMultProc = TRUE);


	IMGAPI	   SetBayerConvMode	(uint32_t uiBCMode = 0);		// Bayer Conversion mode. 8: Monochrome, 1: ACPI, The others : Bi-Linear
	IMGAPIUINT GetBayerConvMode	();								// Bayer Conversion mode. 8: Monochrome, 1: ACPI, The others : Bi-Linear

	IMGAPI	   SetProcMode		(uint32_t uiPrcCMode = 0);		// Processing mode. 1: Multi-Thread, The others : Single thread
	IMGAPIUINT GetProcMode		();								// Processing mode. 1: Multi-Thread, The others : Single thread

	IMGAPI	   SetMPCount		(int32_t iCount = 0);			// Thread count used in multi thread processing mode.
	IMGAPIINT  GetMPCount		();								// Thread count used in multi thread processing mode.

	IMGAPI	   StartMPThreads	(uint32_t uiCountThread = 0);	// Starts threads for Multi-Processing of TeliCamUtl functions.
	IMGAPI	   TerminateMPThreads();							// Terminates threads for Multi-Processing of TeliCamUtl functions.
	IMGAPI	   SetMPThreadPriority(int32_t iPriority);			// Sets thread priority of threads for Multi-Processing of TeliCamUtl functions.
	IMGAPIINT  GetMPThreadPriority();							// Gets thread priority of threads for Multi-Processing of TeliCamUtl functions.
	IMGAPI	   SetMPTimeout_msec(uint32_t uiTimeout);			// Sets time out period for Multi-Processing functions.
	IMGAPIUINT GetMPTimeout_msec();								// Gets time out period for Multi-Processing functions.

	// Source image PixelFormat specific BGRA Converter. Uses processing mode (multi-thread or single thread) specified with SetProcMode(). 
	// for monochrome source data
	IMGAPI ConvMono8ToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Mono8 -> BGRA
	IMGAPI ConvMono10ToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Mono10 -> BGRA
	IMGAPI ConvMono12ToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Mono12 -> BGRA
	IMGAPI ConvMono16ToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Mono16 -> BGRA

	// for bayer filter sensor source data (pixel data depth : 8bit) 
	IMGAPI ConvByrGR8ToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GR8 -> BGRA
	IMGAPI ConvByrRG8ToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer RG8 -> BGRA
	IMGAPI ConvByrGB8ToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GB8 -> BGRA
	IMGAPI ConvByrBG8ToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer BG8 -> BGRA

	// for bayer filter sensor source data using ACPI method.(pixel data depth : 8bit) 
	IMGAPI ConvByrGR8ToBGRAACPI	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GR8 -> BGRA
	IMGAPI ConvByrRG8ToBGRAACPI	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer RG8 -> BGRA
	IMGAPI ConvByrGB8ToBGRAACPI	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GB8 -> BGRA
	IMGAPI ConvByrBG8ToBGRAACPI	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer BG8 -> BGRA

	// for bayer filter sensor source data (pixel data depth : 10bit) 
	IMGAPI ConvByrGR10ToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GR10 -> BGRA
	IMGAPI ConvByrRG10ToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer RG10 -> BGRA
	IMGAPI ConvByrGB10ToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GB10 -> BGRA
	IMGAPI ConvByrBG10ToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer BG10 -> BGRA

	// for bayer filter sensor source data (pixel data depth : 12bit) 
	IMGAPI ConvByrGR12ToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GR12 -> BGRA
	IMGAPI ConvByrRG12ToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer RG12 -> BGRA
	IMGAPI ConvByrGB12ToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GB12 -> BGRA
	IMGAPI ConvByrBG12ToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer BG12 -> BGRA

	//  Rectangle area converter for bayer source data. (pixel data depth : 8bit)  
	IMGAPI ConvGR8RectToBGRA_ACPI(void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
								 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
								 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
								 bool8_t bMultProc = TRUE);												// Bayer GR8 -> BGRA
	IMGAPI ConvRG8RectToBGRA_ACPI(void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
								 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
								 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
								 bool8_t bMultProc = TRUE);												// Bayer RG8 -> BGRA
	IMGAPI ConvGB8RectToBGRA_ACPI(void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
								 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
								 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
								 bool8_t bMultProc = TRUE);												// Bayer GB8 -> BGRA
	IMGAPI ConvBG8RectToBGRA_ACPI(void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
								 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
								 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
								 bool8_t bMultProc = TRUE);												// Bayer BG8 -> BGRA


	// for RGB or BGR format source data (pixel data depth : 8bit) 
	IMGAPI ConvRGB8PToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// RGB8 -> BGRA
	IMGAPI ConvBGR8PToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// BGR8 -> BGRA

	// for RGB or BGR format source data (pixel data depth : 10bit) 
	IMGAPI ConvRGB10PToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// RGB10 -> BGRA
	IMGAPI ConvBGR10PToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// BGR10 -> BGRA

	// for RGB or BGR format source data (pixel data depth : 12bit) 
	IMGAPI ConvRGB12PToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// RGB12 -> BGRA
	IMGAPI ConvBGR12PToBGRA		(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// BGB12 -> BGRA

	// for YUV format 
	IMGAPI ConvYUV411PToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// YUV411 -> BGRA
	IMGAPI ConvYUV422PToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// YUV422 -> BGRA
	IMGAPI ConvYUV444PToBGRA	(void *pvDstBGRA, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// YUV444 -> BGRA


	// RGB24bit Converter
	// for monochrome source data
	IMGAPI ConvMono8ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Mono8 -> BGR
	IMGAPI ConvMono10ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Mono10 -> BGR
	IMGAPI ConvMono12ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Mono12 -> BGR
	IMGAPI ConvMono16ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Mono16 -> BGR

	// for bayer filter sensor source data. (pixel data depth : 8bit) 
	IMGAPI ConvByrGR8ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GR8 -> BGR
	IMGAPI ConvByrRG8ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer RG8 -> BGR
	IMGAPI ConvByrGB8ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GB8 -> BGR
	IMGAPI ConvByrBG8ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer BG8 -> BGR

	// for bayer filter sensor source data using ACPI method. (pixel data depth : 8bit) 
	IMGAPI ConvByrGR8ToBGRACPI	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GR8 -> BGR
	IMGAPI ConvByrRG8ToBGRACPI	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer RG8 -> BGR
	IMGAPI ConvByrGB8ToBGRACPI	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GB8 -> BGR
	IMGAPI ConvByrBG8ToBGRACPI	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer BG8 -> BGR

	// for bayer filter sensor source data. (pixel data depth : 10bit) 
	IMGAPI ConvByrGR10ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GR10 -> BGR
	IMGAPI ConvByrRG10ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer RG10 -> BGR
	IMGAPI ConvByrGB10ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GB10 -> BGR
	IMGAPI ConvByrBG10ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer BG10 -> BGR

	// for bayer filter sensor source data. (pixel data depth : 12bit) 
	IMGAPI ConvByrGR12ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GR12 -> BGR
	IMGAPI ConvByrRG12ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer RG12 -> BGR
	IMGAPI ConvByrGB12ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GB12 -> BGR
	IMGAPI ConvByrBG12ToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer BG12 -> BGR

	// Rectangle area converter for bayer source data. (pixel data depth : 8bit)  
	IMGAPI ConvGR8RectToBGR_ACPI(void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
								 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
								 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
								 bool8_t bPad = FALSE, bool8_t bMultProc = TRUE);						// Bayer GR8 -> BGR
	IMGAPI ConvRG8RectToBGR_ACPI(void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
								 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
								 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
								 bool8_t bPad = FALSE, bool8_t bMultProc = TRUE);						// Bayer RG8 -> BGR
	IMGAPI ConvGB8RectToBGR_ACPI(void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
								 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
								 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
								 bool8_t bPad = FALSE, bool8_t bMultProc = TRUE);						// Bayer GB8 -> BGR
	IMGAPI ConvBG8RectToBGR_ACPI(void *pvDst, void *pvSrc, uint32_t uiWSrc, uint32_t uiHSrc, 
								 uint32_t uiOfsXS, uint32_t uiOfsYS, uint32_t uiWS, uint32_t uiHS,
								 uint32_t uiWDst, uint32_t uiHDst, uint32_t uiOfsXD, uint32_t uiOfsYD,
								 bool8_t bPad = FALSE, bool8_t bMultProc = TRUE);						// Bayer BG8 -> BGR
	

	// for RGB or BGR format source data (pixel data depth : 8bit) 
	IMGAPI ConvRGB8PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// RGB8 -> BGR
	IMGAPI ConvBGR8PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// BGR8 -> BGR

	// for RGB or BGR format source data (pixel data depth : 10bit) 
	IMGAPI ConvRGB10PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// RGB10 -> BGR
	IMGAPI ConvBGR10PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// BGR10 -> BGR

	// for RGB or BGR format source data (pixel data depth : 12bit) 
	IMGAPI ConvRGB12PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// RGB12 -> BGR
	IMGAPI ConvBGR12PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// BGB12 -> BGR

	// for YUV format 
	IMGAPI ConvYUV411PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// YUV411 -> BGR
	IMGAPI ConvYUV422PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// YUV422 -> BGR
	IMGAPI ConvYUV444PToBGR		(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// YUV444 -> BGR


	// RGB24bit with row padding Converter. Uses processing mode (multi-thread or single thread) specified with SetProcMode(). 
	// for monochrome source data
	IMGAPI ConvMono8ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Mono8 -> BGR
	IMGAPI ConvMono10ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Mono10 -> BGR
	IMGAPI ConvMono12ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Mono12 -> BGR
	IMGAPI ConvMono16ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Mono16 -> BGR

	// for bayer filter sensor raw source data (pixel data depth : 8bit) 
	IMGAPI ConvByrGR8ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GR8 -> BGR
	IMGAPI ConvByrRG8ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer RG8 -> BGR
	IMGAPI ConvByrGB8ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GB8 -> BGR
	IMGAPI ConvByrBG8ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer BG8 -> BGR

	// for bayer filter sensor raw source data using ACPI method. (pixel data depth : 8bit) 
	IMGAPI ConvByrGR8ToBGRPad_ACPI(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GR8 -> BGR
	IMGAPI ConvByrRG8ToBGRPad_ACPI(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer RG8 -> BGR
	IMGAPI ConvByrGB8ToBGRPad_ACPI(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer GB8 -> BGR
	IMGAPI ConvByrBG8ToBGRPad_ACPI(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);	// Bayer BG8 -> BGR

	// for bayer filter sensor raw source data (pixel data depth : 10bit) 
	IMGAPI ConvByrGR10ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GR10 -> BGR
	IMGAPI ConvByrRG10ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer RG10 -> BGR
	IMGAPI ConvByrGB10ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GB10 -> BGR
	IMGAPI ConvByrBG10ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer BG10 -> BGR

	// for bayer filter sensor raw source data (pixel data depth : 12bit) 
	IMGAPI ConvByrGR12ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GR12 -> BGR
	IMGAPI ConvByrRG12ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer RG12 -> BGR
	IMGAPI ConvByrGB12ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer GB12 -> BGR
	IMGAPI ConvByrBG12ToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// Bayer BG12 -> BGR


	// for RGB or BGR format source data (pixel data depth : 8bit) 
	IMGAPI ConvRGB8PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// RGB8 -> BGR
	IMGAPI ConvBGR8PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// BGR8 -> BGR

	// for RGB or BGR format source data (pixel data depth : 10bit) 
	IMGAPI ConvRGB10PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// RGB10 -> BGR
	IMGAPI ConvBGR10PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// BGR10 -> BGR

	// for RGB or BGR format source data (pixel data depth : 12bit) 
	IMGAPI ConvRGB12PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// RGB12 -> BGR
	IMGAPI ConvBGR12PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// BGB12 -> BGR

	// for YUV format 
	IMGAPI ConvYUV411PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// YUV411 -> BGR
	IMGAPI ConvYUV422PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// YUV422 -> BGR
	IMGAPI ConvYUV444PToBGRPad	(void *pvDstBGR, void *pvSrc, uint32_t uiWidth, uint32_t uiHeight);		// YUV444 -> BGR


}

#endif // _TELICAMUTL_H_

