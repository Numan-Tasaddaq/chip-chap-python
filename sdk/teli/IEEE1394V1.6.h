/******************************************************************************
HEADER FILE FOR IEEE1394 HARDWARE INTERFACE
******************************************************************************/

#ifndef _IEEE_1394
#define _IEEE_1394

#include <queue>

using namespace std;
using namespace Teli;

#include "ImgBuf.h"

#include "afxmt.h"

#define NEARLYINFINITE 10000

typedef void (CALLBACK* CALLBACKFUNCT)(int);

extern "C" int _stdcall InitDLL();

extern "C" int _stdcall FreeDLL();

extern "C" int _stdcall AllocAppModule(void **pAppModule);

extern "C" int _stdcall FreeAppModule(void **pAppModule);

extern "C" int _stdcall AllocSysModule(long lSysNo, void **pSysModule);

extern "C" int _stdcall FreeSysModule(void **pSysModule);

extern "C" int _stdcall AllocCamModule(
						CString strCamFileName,
						CString strReserved,
						void *pAppModule,
						void *pSysModule,
						long lCamNo,
						long lCamChanNo,
						void **pCamModule,
						int nTimer);

extern "C" int _stdcall FreeCamModule(void *pCamModule);

extern "C" int _stdcall SetTriggerMode(void **pCamModule,int nMode);
extern "C" int _stdcall CancelRequest(void **pCamModule,int nCheck);
extern "C" int _stdcall GetTriggerMode(void **pCamModule,int *pnMode);
extern "C" int _stdcall SetGrabTimeOutMode(void *pCamModule,int nTimeout);
extern "C" int _stdcall SetInfiniteTimeOut(void **pCamModule, bool bSet);
extern "C" int _stdcall SetFirstTimeInfinite(void **pCamModule, bool bSet);
extern "C" int _stdcall SetGrabType(void **pCamModule,bool bType);
extern "C" int _stdcall GetCamResolution(void *pCamModule,CSize *pSize);

extern "C" int _stdcall ImageGrab(void *pCamModule, CImgBuf *pImgBuf);

extern "C" int _stdcall RegHookFunction(void **pCamModule, CALLBACKFUNCT UserFunct);

extern "C" int _stdcall ResetCamera(void *pCamModule,long lReserved);

extern "C" int _stdcall WaitForExposure(void *pCamModule);
extern "C" int _stdcall InitializeCamera(void **pCamModule);

int WaitForGrabEnd(void* pCamera);
int BufferCopy(unsigned char *pBuffer,
			CRect *prcSrc,
			CImgBuf *pImgDst,
			CRect *prcDst);
void ConvertRawY8BGGR(UINT32 XSize,UINT32 YSize,UINT8 *pBuf,UINT8 *pBGR);
//void ConvertRawY8RGGB(UINT32 XSize,UINT32 YSize,UINT8 *pBuf,UINT8 *pBGR);
extern "C" int  _stdcall WaitForCompletion(void *pCamModule, CImgBuf *pImgBuf, int nTimebound);
extern "C" int _stdcall EnqueueAsyncGrab(void *pCamModule, int nDummy);

extern "C" int _stdcall GetCameraMaxAoi(void *pCamModule, CRect *pRectMax);
extern "C" int _stdcall GetCameraAoi(void *pCamModule, CRect *pRect);
extern "C" int _stdcall SetCameraAoi(void *pCamModule, CRect rect);
extern "C" int _stdcall GetCameraGain(void *pCamModule, int *pnGain);
extern "C" int _stdcall SetCameraGain(void *pCamModule, int nGain);
extern "C" int _stdcall GetAperture(void *pCamModule, int *pnAperture);
extern "C" int _stdcall SetAperture(void *pCamModule, int nAperture);
extern "C" int _stdcall GetBytesPerPkt(void *pCamModule, int *pnBytesPerPkt, int* pnBytesPerPktMin, int* pnBytesPerPktMax, int* pnBytesPerPktInc);
extern "C" int _stdcall SetBytesPerPkt(void *pCamModule, int nBytesPerPkt);

extern "C" int _stdcall CancelGrabImg(void *pCamModule, int nDum);
extern "C" int _stdcall EnumerateAllCameras(void *pCamModule, int *pnCamera, unsigned long *pnMaxBytesPerPkt);
extern "C" int _stdcall SetOnePushWhiteBalance(void *pCamModule);
extern "C" int _stdcall SetWhiteBalance(void *pCamModule, UINT32 nWhiteBalance);
extern "C" int _stdcall DiscardFrame(void *pCamModule);

int ProcessColorImage(void* pCamera);	// VV color

const int STRM_REQUEST_NUM = 16; 

class CApplication
{
public :
	CApplication();
	~CApplication();
};


class CSystem
{
public :
	CSystem();
	~CSystem();
	long m_lSysNo;
};

class CCamera
{
public :

	long m_lCamNo;
	int nNoOfGet;
	int nNoOfEmpty;
	CEvent m_eventWaitMS;
	// handles
	CAM_HANDLE s_hCam;
	CAM_STRM_HANDLE  s_hStrm;
	CAM_EVT_HANDLE   s_hEvt;
	HANDLE		   s_hRmvEvt;    // unplugged event
	HANDLE         s_hStrmEvt;    // completion event for stream 
	HANDLE         s_hCompEvt;    // completion event for event
	
	// for stream
	CAM_STRM_REQUEST_HANDLE m_hStrmReq[STRM_REQUEST_NUM]; 
	CAM_STRM_REQUEST_HANDLE m_hRcvStrmReq[STRM_REQUEST_NUM];
	void  *m_pvRcvPayloadBuf;
    BYTE  *m_pbyPayloadBuf;              // All Payload Buffer
	void    *m_pstCurCompQueue;     // Current Complete Queue
	
  
	// for event
	CAM_EVT_REQUEST_HANDLE m_hEvtRequest; 
	CAM_EVT_REQUEST_HANDLE m_hRcvEvtRequest;
	void*     m_pvEvtPayloadBuf; 
	
	BOOL m_bUseDirectGrab;			// Flag to determine if we are using Direct Grab with the RegGrabBuffer
	BOOL m_bBufferValid;
	int m_nContexts;		

	DWORD m_dwGrabTimeout;
	bool m_bGrabType;
	bool bTest;
	int nSave;

	CSize m_szResolution;

	CPoint m_posAoi;
	CSize m_szAoi;
	int m_nAperture;
	int m_nGain;
	int m_nBrightness;
	int m_nBytePerPacket;
	int m_nBppMax;
	int m_nBppMin;
	int m_nBppInc;
	int nCam;		// Identifies No. of Cameras

	CString m_DeviceName;

	bool m_bColor;

	CRITICAL_SECTION m_csCamera;

	int m_nTriggerMode;

	CPerformanceTimer GrabTime;

////	CEvent m_evntExpEnd;
////	CEvent m_evntGrbEnd;

	//Functions
	CCamera();
	~CCamera();
	void (_stdcall* m_pUserFunct)(int);
	void CalcBytesPerPktInfo();
	void GrabCancel();
	void ContinuousGrab();
	void HardwareTriggerGrab();
	void GrabImage(void *pCamModule);
	CAM_API_STATUS RegWrite(uint64_t adrs, void* pdat, uint16_t num);
	CAM_API_STATUS RegRead(uint64_t adrs, void* pdat, uint32_t num);
	uint32_t OpenStream();
	uint32_t CloseStream();
	uint32_t OpenEvent();
	uint32_t DigitalIOControl();
	uint32_t SetPixelInfo();
	uint32_t SetEventCallback();
	uint32_t SetAoi();
	uint32_t SetExposure();
	uint32_t SetGain();
	uint32_t SetAcquisitionFrameRate();
	uint32_t StartAcquisition();
	uint32_t StopAcquisition();

private :

};

void RepoerError (int Result)
{
	CString Buffer;
	Buffer.Format("Camera Error Code : %d", Result);
	AfxMessageBox(Buffer);
}

void ReportError(UINT32 e)
{
	CString Buffer;
	Buffer.Format("Camera Error Code : %d\n", e);
	AfxMessageBox(Buffer);
}

// greatest common divisor
int gcd(int num1, int num2)
{
	ASSERT(num1 != 0);
	int remainder = num2 % num1;
	
	if (remainder != 0)
		return gcd(remainder,num1);
	
	return num1;
}

// least common multiple
int lcm(int num1, int num2)
{
	return (num1 * num2) / gcd(num1, num2);
}

#endif