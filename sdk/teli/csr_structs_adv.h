/*****************************************************************************
 *
 *
 *
 ****************************************************************************/

#ifndef	__CSR_STRUCTS_ADV_H
#define	__CSR_STRUCTS_ADV_H

#include "types.h"
#include "structs.h"

#ifdef __cplusplus
    #ifndef __arm
        namespace csr_adv {
    #endif

	extern "C" {
#endif

#ifdef _MSC_VER
    #pragma pack(push, vnd1, 2)
#endif

/*****************************************************************************
    Advanced feature registers
*****************************************************************************/

// ---------------------------------------------------------------------------
//
typedef struct __tagCsrOffset
{
    __uint32                value           : 24;
    __uint32                key_type        :  8;
} CSR_OFFSET;

// ---------------------------------------------------------------------------
//
typedef struct __tagAdvFeatureGuid
{
    GUID                        m_Guid;
    __uint32                    m_AddrLow;
    __uint32                    m_AddrHigh;

    struct __tagAdvFeatureGuidElems
    {
        __uint32                m_nCsrSize          : 16;
        __uint32                                    : 16;
    }                           m_Extra;
} CSR_ADVFEATURE_GUID;

// ---------------------------------------------------------------------------
//
typedef struct __tagCsrAdvVersionInfo
{
    __uint16                    m_nArmVersion;      //  2 Bytes
    __uint16                    m_nArmSpecID;       //  2 Bytes
    __uint32                    gap1;               //  4 Bytes
    __uint16                    m_nFpgaVersion;     //  2 Bytes
    __uint16                    m_nFpgaSpecID;      //  2 Bytes
    __uint32                    gap2;               //  4 Bytes
} CSRADV_VERSION_INFO;

typedef struct __tagCsrAdvVersionInfoEx
{
    __uint16                    m_nArmVersion;      //  2 Bytes
    __uint16                    m_nArmSpecID;       //  2 Bytes
    __uint32                    gap1;               //  4 Bytes
    __uint16                    m_nFpgaVersion;     //  2 Bytes
    __uint16                    m_nFpgaSpecID;      //  2 Bytes
    __uint32                    gap2;               //  4 Bytes

    __uint64                    gap3[2];            // 16 Bytes

    __uint64                    m_KhkID;            //  8 Bytes
    __uint64                    m_CustomerKey;      //  8 Bytes
} CSRADV_VERSION_INFO_EX;

// ---------------------------------------------------------------------------
// Inquiry of available advanced features
typedef struct __tagCsrAdvInquiry
{
    struct __tagCsrAdvInq1
    {
        __uint32                m_bGPBuffer         :  1;
        __uint32                                    : 15;
        __uint32                m_bMiscFeatures     :  1;
        __uint32                m_bTriggerDelay     :  1;
        __uint32                m_bBlemishCorr      :  1;
        __uint32                m_bFpnCorrection    :  1;
        __uint32                m_bIbisHdrMode	    :  1;
        __uint32                m_bDeferredTrans    :  1;
        __uint32                m_bShading          :  1;
        __uint32                m_bLut              :  1;
        __uint32                                    :  1;
        __uint32                m_bVersionInfo      :  1;
        __uint32                m_bSequences        :  1;
        __uint32                m_bFrameInfo        :  1;
        __uint32                m_bTestImage        :  1;
        __uint32                m_bExtdShutter      :  1;
        __uint32                m_bTimeBase         :  1;
        __uint32                m_bMaxResolution    :  1;
    }                           Inq1;

    struct __tagCsrAdvInq2
    {
        __uint32                                    : 14;
        __uint32                m_bIncDecoder       :  1;
        __uint32                m_bIntEnaDelay      :  1;
        __uint32                                    :  5;
        __uint32                m_bOutp_3           :  1;
        __uint32                m_bOutp_2           :  1;
        __uint32                m_bOutp_1           :  1;
        __uint32                                    :  5;
        __uint32                m_bInp_3            :  1;
        __uint32                m_bInp_2            :  1;
        __uint32                m_bInp_1            :  1;
    }                           Inq2;

    struct __tagCsrAdvInq3
    {
        __uint32                m_Dummy;
    }                           Inq3;

    struct __tagCsrAdvInq4
    {
        __uint32                m_Dummy;
    }                           Inq4;

} CSRADV_FNC_INQ;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrAdvMaxResolution
{
    S_IMAGESIZE                 m;
    __uint32                    m_nAll;
} CSRADV_MAX_RESOLUTION;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrAdvTimebase
{
    struct __tagCsrAdvTimebaseElems
    {
        __uint32                m_nBase         :  4;
        __uint32                                : 27;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_TIMEBASE;

typedef union __tagCsrAdvExtdShutter
{
    struct __tagCsrAdvExtdShutterElems
    {
        __uint32                m_nShutter      : 26;
        __uint32                                :  5;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_EXTD_SHUTTER;

typedef union __tagCsrAdvTriggerDelay
{
    struct __tagCsrAdvTriggerDelayElems
    {
        __uint32                m_nDelay        : 21;
        __uint32                                :  4;
        __uint32                m_bOnOff        :  1;
        __uint32                                :  5;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_TRIGGER_DELAY;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrAdvTestPix
{
    struct __tagCsrAdvTestPixElems
    {
        __uint32                m_nTestPix      :  4;
        __uint32                                : 13;
        __uint32                m_bImg7Inq      :  1;   // Image 7 present
        __uint32                m_bImg6Inq      :  1;   // Image 6 present
        __uint32                m_bImg5Inq      :  1;   // Image 5 present
        __uint32                m_bImg4Inq      :  1;   // Image 4 present
        __uint32                m_bImg3Inq      :  1;   // Image 3 present
        __uint32                m_bImg2Inq      :  1;   // Image 2 present
        __uint32                m_bImg1Inq      :  1;   // Image 1 present
        __uint32                                :  7;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_TESTPIX;

// ---------------------------------------------------------------------------
// Sequence control and parameter
typedef union __tagCsrAdvSeqCtrl
{
    struct __tagCsrAdvSeqParamElems
    {
        __uint32                m_nSeqLength    :  8;
        __uint32                m_nMaxLength    :  8;
        __uint32                                :  9;
        __uint32                m_bOnOff        :  1;
        __uint32                m_bAutoRewind   :  1;
        __uint32                                :  4;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_SEQCTRL;

typedef union __tagCsrAdvSeqParam
{
    struct __tagCsrAdvSeqCtrlElems
    {
        __uint32                m_nImageNo      :  8;
        __uint32                                : 17;
        __uint32                m_bIncImgNo     :  1;   //! increment m_nImageNo on m_bSet
        __uint32                m_bApply        :  1;
        __uint32                                :  5;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_SEQPARAM;

// ---------------------------------------------------------------------------
// Lut control
//#define LUT_TABLE_SIZE          8192
//#define LUT_NUMOFTABLES         64

typedef struct __tagCsrAdvLutCtrl
{
    // Lut control
    struct __tagCsrAdvLutCtrlElems
    {
        __uint32                m_nLutNo        :  6;   //! number of table to use
        __uint32                                :  2;
        __uint32                m_nMemChn       :  8;   // memory channel to save/load data to/from
        __uint32                                :  6;
        __uint32                m_bMemLoad      :  1;   // load LUT data from channel n
        __uint32                m_bMemSave      :  1;   // save LUT data to channel n
        __uint32                                :  1;
        __uint32                m_bOnOff        :  1;
        __uint32                                :  5;
        __uint32                m_bPresence     :  1;
    }                           m_Ctrl;

    struct __tagCsrAdvLutMemElems
    {
        __uint32                m_nAddrOffset   : 16;   //! address offset to selected LUT
        __uint32                m_nLut2WR       :  8;   //! number of LUT to access
        __uint32                                :  1;
        __uint32                m_bEnaMemRD     :  1;
        __uint32                m_bEnaMemWR     :  1;
        __uint32                                :  4;
        __uint32                m_bPresence     :  1;
    }                           m_Mem;

    struct __tagCsrAdvLutInfoElems
    {
        __uint32                m_nMaxSize      : 16;   //! max size of one LUT
        __uint32                m_nNumOfLuts    :  8;   //! number of available LUTs
        __uint32                m_nBitsPerValue :  5;   //! number of bits/grey value
        __uint32                                :  2;
        __uint32                m_bPresence     :  1;   //
    }                           m_Info;

} CSRADV_LUT_CTRL;

// ---------------------------------------------------------------------------
// Deferred transport
typedef union __tagCsrAdvDeferredTrans
{
    struct __tagCsrAdvDeferredTransElems
    {
        __uint32                m_nSendPix      :  8;   //! number of images WR:to send, RD: left
        __uint32                m_nFifoDepth    :  8;   //! depth of image FIFO
        __uint32                                :  8;
        __uint32                m_bFastCapture  :  1;   //!
        __uint32                m_bHoldImg      :  1;   //!
        __uint32                m_bSendPix      :  1;   //!
        __uint32                                :  4;
        __uint32                m_bPresence     :  1;   //!
    }                           m;
    __uint32                    m_nAll;
} CSRADV_DEFERREDTRANS;

// ---------------------------------------------------------------------------
// IO input/output control
#define MAX_NUM_OF_INPUTS       8
#define NUM_OF_INPUTS           3
#define MAX_NUM_OF_OUTPUTS      8
#define NUM_OF_OUTPUTS          3

typedef enum __tagCsrAdvIoInpModes
{
    GPIO_INP_OFF                = 0,
    GPIO_INP_TRIGGER            = 0x02,
    GPIO_INP_DECODER            = 0x03
} CSRADV_IO_INP_MODES;

typedef union __tagCsrAdvIoInpCtrlx
{
    struct __tagCsrAdvIoInpCtrlxElems
    {
        __uint32                m_bPinState     :  1;
        __uint32                                : 15;
        __uint32                m_nMode         :  5;
        __uint32                                :  3;
        __uint32                m_bPolarity     :  1;
        __uint32                                :  6;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_IO_INP_CTRLX;

typedef enum __tagCsrAdvIoOutpModes
{
    GPIO_OUTP_OFF               = 0,
    GPIO_OUTP_DIRECT            = 0x01,
    GPIO_OUTP_INTENA            = 0x02,
    GPIO_OUTP_DECODER           = 0x03,
    GPIO_OUTP_FVAL              = 0x06,
    GPIO_OUTP_BUSY              = 0x07,
    GPIO_OUTP_FOLLOW_INP        = 0x08
} CSRADV_IO_OUTP_MODES;

typedef union __tagCsrAdvIoOutpCtrlx
{
    struct __tagCsrAdvIoOutpCtrlxElems
    {
        __uint32                m_bPinState     :  1;
        __uint32                                : 15;
        __uint32                m_nMode         :  5;
        __uint32                                :  3;
        __uint32                m_bPolarity     :  1;
        __uint32                                :  6;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_IO_OUTP_CTRLX;

// integration enable delay
typedef union __tagCsrAdvIntEnaDelay
{
    struct __tagCsrAdvIntEnaDelayElems
    {
        __uint32                m_nDelay1us     : 20;
        __uint32                                :  5;
        __uint32                m_bOnOff        :  1;
        __uint32                                :  5;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_INTENA_DELAY;

// incremental decoder
typedef struct __tagCsrAdvDecoder
{
    struct __tagCsrAdvDecoderCtrl
    {
        __uint32                                : 24;
        __uint32                m_bClearCounter :  1;
        __uint32                m_bOnOff        :  1;
        __uint32                                :  5;
        __uint32                m_bPresence     :  1;
    }                           m_Ctrl;

    struct __tagCsrAdvDecoderValues
    {
        __uint32                m_nCounter      : 12;
        __uint32                                :  4;
        __uint32                m_nCompare      : 12;
        __uint32                                :  4;
    }                           m_Val;

} CSRADV_DECODER;

typedef struct
{
    CSRADV_IO_INP_CTRLX         m_ioInp[MAX_NUM_OF_INPUTS];
    CSRADV_IO_OUTP_CTRLX        m_ioOutp[MAX_NUM_OF_OUTPUTS];
} CSRADV_IO_CTRL;

// ---------------------------------------------------------------------------
// Serial function control
typedef union __tagCsrAdvSerialFunction
{
    struct __tagCsrAdvSerialFunctionElems
    {
        __uint32                m_nFuncID       : 16;
        __uint32                m_nBitrateID    :  8;
        __uint32                                :  7;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_SERIALFUNCTION;

// ---------------------------------------------------------------------------
// Shading control
typedef struct __tagCsrAdvShading
{
    struct __tagCsrAdvShadingCtrl
    {
        __uint32                m_nGrabCount    :  8;   // number of images to build shading image
        __uint32                m_nMemChn       :  4;   // memory channel to save/load shading image to/from
        __uint32                                : 10;
        __uint32                m_bMemLoad      :  1;   // load shading image from channel n
        __uint32                m_bMemSave      :  1;   // save shading image to channel n
        __uint32                m_bBusy         :  1;   // build shading image in progress
        __uint32                m_bOnOff        :  1;   // shading on/off
        __uint32                m_bBuildTable   :  1;   // build shading image now
        __uint32                m_bShowImg      :  1;   // show shading data as image
        __uint32                                :  2;
        __uint32                m_bBuildError   :  1;   // build shading image reports an error
        __uint32                m_bPresence     :  1;   // Presence of this feature
    }                           m_Ctrl;

    struct __tagCsrAdvShadingMem
    {
        __uint32                m_nAddrOffset   : 24;   // wr: set address offset
                                                        // rd: get address offset
        __uint32                                :  1;
        __uint32                m_bEnaMemRD     :  1;   // enable RD access
        __uint32                m_bEnaMemWR     :  1;   // enable WR access
        __uint32                                :  4;
        __uint32                m_bPresence     :  1;   // Presence of this feature
    }                           m_Mem;

    struct __tagCsrAdvShadingInfo
    {
        __uint32                m_nMaxSize      : 24;   // max size of shading image
        __uint32                m_nMemChnCount  :  4;   // number of available memory channels
        __uint32                                :  3;
        __uint32                m_bPresence     :  1;   // Presence of this feature
    }                           m_Info;
} CSRADV_SHADING;

// ---------------------------------------------------------------------------
// FPN & Blemish correction control
typedef union __tagCsrAdvFpnCorrection
{
    struct __tagCsrAdvFpnCorrectionCtrl
    {
        __uint32                m_nGrabCount    :  8;   // number of images to build FPN image
        __uint32                m_nMemChn       :  4;   // memory channel to save/load FPN image to/from
        __uint32                                :  9;
        __uint32                m_bZeroTable    :  1;   // zero the FPN image buffer
        __uint32                m_bMemLoad      :  1;   // load FPN image from storage
        __uint32                m_bMemSave      :  1;   // save FPN image to storage
        __uint32                m_bBusy         :  1;   // build FPN image in progress
        __uint32                m_bOnOff        :  1;   // FPN correction on/off
        __uint32                m_bBuildTable   :  1;   // build shading image now
        __uint32                m_bShowImg      :  1;   // show shading data as image
        __uint32                                :  2;
        __uint32                m_bBuildError   :  1;   // build FPN image reports an error
        __uint32                m_bPresence     :  1;   // Presence of this feature
    }                           m;
    __uint32                    m_nAll;
} CSRADV_FPNCORRECTION, CSRADV_BLEMISHCORRECTION;

// ---------------------------------------------------------------------------
// general purpose data buffer

#define CSRADV_GPDATABUFFER_SIZE    2048

typedef union __tagCsrAdvGpDataInfo
{
    struct __tagCsrAdvGpDataInfoElems
    {
        __uint32                m_nSize         : 16;
        __uint32                                : 16;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_GPDATAINFO;

typedef union __tagCsrAdvGpDataBuffer
{
    __uint16                    m_int16[CSRADV_GPDATABUFFER_SIZE/sizeof(__uint16)];
    __uint32                    m_int32[CSRADV_GPDATABUFFER_SIZE/sizeof(__uint32)];
} CSRADV_GPDATABUFFER;

// ---------------------------------------------------------------------------
//
typedef struct __tagCsrAdvFrameInfo
{
    struct __tagCsrAdvFrameInfoElems
    {
        __uint32                                        : 30;
        __uint32                m_bClearFrameCounter    :  1;
        __uint32                m_bPresence             :  1;
    }                           m_Cmd;

    __uint32                    m_nFrameCounter;

} CSRADV_FRAMEINFO;

// ---------------------------------------------------------------------------
// HDR mode register
typedef	struct __tagCsrAdvIbisHdr
{
    struct __tagCsrAdvIbisHdrElems
    {
        __uint32                m_nKneePoints		:  4;
        __uint32                            		:  4;
        __uint32                m_nMaxKneePoints	:  4;
        __uint32                            		: 13;
        __uint32                m_bOnOff    		:  1;
        __uint32                            		:  5;
        __uint32                m_bPresence			:  1;
    }                           m_Cmd;

    __uint32                    m_kneePoint[3];
} CSRADV_IBISHDR;

// ---------------------------------------------------------------------------
// IBIS rolling shutter mode register
typedef	union __tagCsrAdvIbisShutter
{
    struct __tagCsrAdvIbisShutterElems
    {
        __uint32                            		: 25;
        __uint32                m_bOnOff    		:  1;
        __uint32                            		:  5;
        __uint32                m_bPresence			:  1;
    }                           m;
    __uint32                    m_nAll;
} CSRADV_IBISSHUTTER;

// ---------------------------------------------------------------------------
// color correction (8 quadlets)
typedef	struct __tagCsrAdvColorCorrection
{
    struct __tagCsrAdvColorCorrectionElems
    {
        __uint32                            		: 25;
        __uint32                m_bOnOff    		:  1;
        __uint32                            		:  5;
        __uint32                m_bPresence			:  1;
    }                           m;

    __uint16                    m_nValues[10];
    __uint32                    m_nGap[2];
} CSRADV_COLORCORRECTION;

// ---------------------------------------------------------------------------
// AutoShutterControl
typedef struct __tagCsrAdvAutoShutter
{
    struct __tagCsrAdvAutoShutterElems
    {
        __uint32                                    : 31;
        __uint32                m_bPresence			:  1;
    }                           m;

    struct __tagCsrAdvAutoShutterMinElems
    {
        __uint32                m_nValue            : 26;
        __uint32                                    :  6;
    }                           m_Low;

    struct __tagCsrAdvAutoShutterMaxElems
    {
        __uint32                m_nValue            : 26;
        __uint32                                    :  6;
    }                           m_High;
} CSRADV_AUTOSHUTTER;

// ---------------------------------------------------------------------------
// AutoGainControl
typedef union __tagCsrAdvAutoGain
{
    struct __tagCsrAdvAutoGainElems
    {
        __uint32                m_nLoVal            : 12;
        __uint32                                    :  4;
        __uint32                m_nHiVal            : 12;
        __uint32                                    :  3;
        __uint32                m_bPresence			:  1;
    }                           m;

    __uint32                    m_All;
} CSRADV_AUTOGAIN;

// ---------------------------------------------------------------------------
// AutoFeatureAOI
typedef struct __tagCsrAdvAutoFncAOI
{
    struct __tagCsrAdvAutoFncAOIElems
    {
        __uint32                                    :  25;
        __uint32                m_bOnOff    		:  1;
        __uint32                                    :  1;
        __uint32                m_bShowWorkArea     :  1;
        __uint32                            		:  3;
        __uint32                m_bPresence			:  1;
    }                           m_Ctrl;

    S_IMAGEPOS                  m_ImagePos;
    S_IMAGESIZE                 m_ImageSize;

} CSRADV_AUTOFNC_AOI;

// ---------------------------------------------------------------------------
//
typedef struct __tagCsrAdvMiscFeatures
{
    struct __tagCsrAdvMiscMirror
    {
        __uint32                                    :  25;
        __uint32                m_bOnOff    		:  1;
        __uint32                            		:  5;
        __uint32                m_bPresence			:  1;
    }                           m_Mirror;

    struct __tagCsrAdvMiscMNR
    {
        __uint32                                    :  25;
        __uint32                m_bOnOff    		:  1;
        __uint32                            		:  5;
        __uint32                m_bPresence			:  1;
    }                           m_MNR;
} CSRADV_MISC_FEATURES;

// ---------------------------------------------------------------------------
//


#ifdef _MSC_VER
    #pragma pack(pop, vnd1)
#endif

#ifdef __cplusplus
    } /// extern "C"

    #ifndef __arm
    } /// namespace csr_adv
    #endif
#endif

#endif /// #ifndef	__CSR_STRUCTS_ADV_H
	