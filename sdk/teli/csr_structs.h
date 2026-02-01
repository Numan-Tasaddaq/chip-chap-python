/*****************************************************************************
 *
 *
 *
 ****************************************************************************/

#ifndef __CSR_STRUCTS_H
#define __CSR_STRUCTS_H

#include <types.h>
#include <structs.h>
#include <dcam_base.h>

#ifdef __cplusplus
    #ifndef __arm
        namespace csr_std {
    #endif

    extern "C" {
#endif

#ifdef _MSC_VER
    #pragma pack(push, vnd1, 1)
#endif

/*****************************************************************************
*****************************************************************************/

/*****************************************************************************
    Inquiries
*****************************************************************************/

// ---------------------------------------------------------------------------
//
typedef union __tagCsrInitialize
{
    struct __tagInitializeElems_0x000
    {
        __uint32                                : 31;
        __uint32                m_bInitialize   :  1;   // Bit[0]
    }                           m;
    __uint32                    m_nAll;
} CSR_INITIALIZE;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrVFormatInq_0x100
{
    struct __tagVFormatInqElems
    {
        __uint32                                : 24;
        __uint32                m_bFormat7      :  1;
        __uint32                m_bFormat6      :  1;
        __uint32                                :  3;
        __uint32                m_bFormat2      :  1;
        __uint32                m_bFormat1      :  1;
        __uint32                m_bFormat0      :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_VFORMAT_INQ;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrVModeInq_0x180
{
    struct __tagVModeInqElems
    {
        __uint32                                : 24;
        __uint32                m_bMode7        :  1;
        __uint32                m_bMode6        :  1;
        __uint32                m_bMode5        :  1;
        __uint32                m_bMode4        :  1;
        __uint32                m_bMode3        :  1;
        __uint32                m_bMode2        :  1;
        __uint32                m_bMode1        :  1;
        __uint32                m_bMode0        :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_VMODE_INQ;

typedef struct __tagCsrVModeInqAll_0x180
{
    CSR_VMODE_INQ               m_VFormat[8];
} CSR_VMODE_INQ_ALL;

// ---------------------------------------------------------------------------
//
#define FPS_1_875               BIT0
#define FPS_3_75                BIT1
#define FPS_7_5                 BIT2
#define FPS_15                  BIT3
#define FPS_30                  BIT4
#define FPS_60                  BIT5
#define FPS_120                 BIT6
#define FPS_240                 BIT7

#ifdef  BUG_TCPP_UNION_INIT
#define VFRMRATE_INIT(r5,r4,r3,r2,r1,r0)    ( (r0 ? BIT31 : 0)|(r1 ? BIT30 : 0)|(r2 ? BIT29 : 0)|(r3 ? BIT28 : 0)|(r4 ? BIT27 : 0)|(r5 ? BIT26 : 0))
#else
#define VFRMRATE_INIT(r5,r4,r3,r2,r1,r0)    { r5,r4,r3,r2,r1,r0 }
#endif

typedef union __tagCsrVFrmRateInq_0x200
{
    struct __tagVFrmRateInqElems
    {
        __uint32                                : 26;
        __uint32                m_bRate5        :  1;       // 60.0   fps
        __uint32                m_bRate4        :  1;       // 30.0   fps
        __uint32                m_bRate3        :  1;       // 15.0   fps
        __uint32                m_bRate2        :  1;       //  7.5   fps
        __uint32                m_bRate1        :  1;       //  3.75  fps
        __uint32                m_bRate0        :  1;       //  1.875 fps
    }                           m;
    __uint32                    m_nAll;
} CSR_VFRM_RATE_INQ;

typedef union __tagCsrVRev6Inq_0x2C0
{
    __uint32                    m_nAll;                     //
} CSR_VREV6_INQ;

typedef union __tagCsrVCsr7Inq_0x2E0
{
    __uint32                    m_nOffset;
} CSR_VCSR7_INQ;

typedef struct __tagCsrVFrmRateInqAll_0x200
{
    CSR_VFRM_RATE_INQ           m_VFormat[6][8];
    CSR_VREV6_INQ               m_VFormat6[8];
    CSR_VCSR7_INQ               m_VFormat7[8];
} CSR_VFRM_RATE_INQ_ALL;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrBasicFncInq_0x400
{
    struct __tagBasicFncInqElems
    {
        __uint32                m_nMemChannel           :  4;       //
        __uint32                                        :  7;       //
        __uint32                m_bMultiShot            :  1;       //
        __uint32                m_bOneShot              :  1;       //
        __uint32                                        :  2;       //
        __uint32                m_bCamPowerCtrl         :  1;       //
        __uint32                                        :  7;       //
        __uint32                m_b1394bCapability      :  1;       // IIDC-1.31
        __uint32                                        :  4;
        __uint32                m_bOptFuncCsr           :  1;       // IIDC-1.31
        __uint32                m_bFeatureCtrlErrStat   :  1;       //
        __uint32                m_bVModeErrStat         :  1;       //
        __uint32                m_bAdvFeature           :  1;       //
    }                           m;
    __uint32                    m_nAll;
} CSR_BASICFNC_INQ;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrFeatureHiInq
{
    struct __tagFeatureHiInqElems
    {
        __uint32                                        : 16;       //
        __uint32                m_bFrameRate            :  1;       // IIDC-1.31
        __uint32                m_bWhiteShading         :  1;       // IIDC-1.31
        __uint32                m_bTriggerDelay         :  1;       // IIDC-1.31
        __uint32                m_bTrigger              :  1;       //
        __uint32                m_bTemperature          :  1;       //
        __uint32                m_bFocus                :  1;       //
        __uint32                m_bIris                 :  1;       //
        __uint32                m_bGain                 :  1;       //
        __uint32                m_bShutter              :  1;       //
        __uint32                m_bGamma                :  1;       //
        __uint32                m_bSaturation           :  1;       //
        __uint32                m_bHue                  :  1;       //
        __uint32                m_bWhiteBal             :  1;       //
        __uint32                m_bSharpness            :  1;       //
        __uint32                m_bAutoExposure         :  1;       //
        __uint32                m_bBrightness           :  1;       //
    }                           m;
    __uint32                    m_nAll;
} CSR_FEATUREHI_INQ,
  CSR_FEATUREHI_ERRSTAT;

typedef union __tagCsrFeatureLoInq
{
    struct __tagFeatureLoInqElems
    {
        __uint32                                        : 14;       //
        __uint32                m_bCaptureQuality       :  1;       //
        __uint32                m_bCaptureSize          :  1;       //
        __uint32                                        : 12;       //
        __uint32                m_bOpticalFilter        :  1;       //
        __uint32                m_bTilt                 :  1;       //
        __uint32                m_bPan                  :  1;       //
        __uint32                m_bZoom                 :  1;       //
    }                           m;
    __uint32                    m_nAll;
} CSR_FEATURELO_INQ,
  CSR_FEATURELO_ERRSTAT;

// IIDC-1.31
typedef union __tagCsrOptFunctionInq
{
    struct __tagCsrOptFunctionInqElems
    {
        __uint32                                        : 28;
        __uint32                m_bStrobeOutp           :  1;
        __uint32                m_bSIO                  :  1;
        __uint32                m_bPIO                  :  1;
        __uint32                                        :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_OPTFUNC_INQ;

typedef struct __tagCsrFeatureInq_0x404
{
    CSR_FEATUREHI_INQ           m_Hi;
    CSR_FEATURELO_INQ           m_Lo;
    CSR_OPTFUNC_INQ             m_Opt;
} CSR_FEATURE_INQ;

typedef struct __tagCsrFeatureInq_0x640
{
    CSR_FEATUREHI_INQ           m_Hi;
    CSR_FEATURELO_INQ           m_Lo;
} CSR_FEATURE_ERRSTAT;

// ---------------------------------------------------------------------------
//
typedef struct __tagCsrAdvFeatureInq_0x480
{   // offsets in quadlets
    __uint32                    m_nAdvCsr;
    __uint32                    m_nPioCsr;          // IIDC-1.31
    __uint32                    m_nSioCsr;          // IIDC-1.31
    __uint32                    m_nStrobeOutpCsr;   // IIDC-1.31
} CSR_ADVFEATURE_INQ;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrBrightnessInq_0x500
{
    struct __tagBrightnessInqElems
    {
        __uint32                m_nMaxVal       : 12;
        __uint32                m_nMinVal       : 12;
        __uint32                m_bManual       :  1;
        __uint32                m_bAuto         :  1;
        __uint32                m_bOnOff        :  1;
        __uint32                m_bReadOut      :  1;
        __uint32                m_bOnePush      :  1;
        __uint32                                :  1;
        __uint32                m_bAbsControl   :  1;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_BRIGHTNESS_INQ,
  CSR_AUTOEXPOSURE_INQ,
  CSR_SHARPNESS_INQ,
  CSR_WHITEBAL_INQ,
  CSR_HUE_INQ,
  CSR_SATURATION_INQ,
  CSR_GAMMA_INQ,
  CSR_SHUTTER_INQ,
  CSR_GAIN_INQ,
  CSR_IRIS_INQ,
  CSR_FOCUS_INQ,
  CSR_TEMPERATURE_INQ,
  CSR_TRIGGER_DLY_INQ,
  CSR_WHITE_SHDG_INQ,
  CSR_FRAMERATE_INQ,
  CSR_ZOOM_INQ,
  CSR_PAN_INQ,
  CSR_TILT_INQ,
  CSR_OPTICAL_FILTER_INQ,
  CSR_CAPTURE_SIZE_INQ,
  CSR_CAPTURE_QUALITY_INQ;

typedef union __tagCsrTriggerInq_0x530
{
    struct __tagTriggerInqElems
    {
        __uint32                m_bTrigMode15   :  1;   // IIDC-1.31
        __uint32                m_bTrigMode14   :  1;   // IIDC-1.31
        __uint32                                :  8;
        __uint32                m_bTrigMode5    :  1;   // IIDC-1.31
        __uint32                m_bTrigMode4    :  1;   // IIDC-1.31
        __uint32                m_bTrigMode3    :  1;
        __uint32                m_bTrigMode2    :  1;
        __uint32                m_bTrigMode1    :  1;
        __uint32                m_bTrigMode0    :  1;
        __uint32                m_bSoftTrg      :  1;   // IIDC-1.31
        __uint32                                :  3;
        __uint32                m_nTrgSrc3      :  1;   // IIDC-1.31
        __uint32                m_nTrgSrc2      :  1;   // IIDC-1.31
        __uint32                m_nTrgSrc1      :  1;   // IIDC-1.31
        __uint32                m_nTrgSrc0      :  1;   // IIDC-1.31
        __uint32                m_bValueRead    :  1;   // IIDC-1.31
        __uint32                m_bPolarity     :  1;
        __uint32                m_bOnOff        :  1;
        __uint32                m_bReadOut      :  1;
        __uint32                                :  2;
        __uint32                m_bAbsControl   :  1;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_TRIGGER_INQ;

typedef struct __tagCsrFeatureCapabilitiesInq_0x500
{
    CSR_BRIGHTNESS_INQ          m_Brightness;
    CSR_AUTOEXPOSURE_INQ        m_AutoExposure;
    CSR_SHARPNESS_INQ           m_Sharpness;
    CSR_WHITEBAL_INQ            m_WhiteBal;
    CSR_HUE_INQ                 m_Hue;
    CSR_SATURATION_INQ          m_Saturation;
    CSR_GAMMA_INQ               m_Gamma;
    CSR_SHUTTER_INQ             m_Shutter;
    CSR_GAIN_INQ                m_Gain;
    CSR_IRIS_INQ                m_Iris;
    CSR_FOCUS_INQ               m_Focus;
    CSR_TEMPERATURE_INQ         m_Temperature;
    CSR_TRIGGER_INQ             m_Trigger;
    CSR_TRIGGER_DLY_INQ         m_TriggerDelay;
    CSR_WHITE_SHDG_INQ          m_WhiteShdg;
    CSR_FRAMERATE_INQ           m_FrameRate;
    __uint32                    m_gap1[16];
    CSR_ZOOM_INQ                m_Zoom;
    CSR_PAN_INQ                 m_Pan;
    CSR_TILT_INQ                m_Tilt;
    CSR_OPTICAL_FILTER_INQ      m_OpticalFilter;
    __uint32                    m_gap2[12];
    CSR_CAPTURE_SIZE_INQ        m_CaptureSize;
    CSR_CAPTURE_QUALITY_INQ     m_CaptureQuality;
    __uint32                    m_gap3[14];
} CSR_FEATURECAPABILITIES_INQ;

/*****************************************************************************
    Status and Control
*****************************************************************************/

// ---------------------------------------------------------------------------
//
typedef union __tagCsrCurVFrmRate_0x600
{
    struct __tagVFrmRateElems
    {
        __uint32                                : 29;
        __uint32                m_nFrmRate      :  3;
    }                           m;
    __uint32                    m_nAll;
} CSR_CUR_VFRM_RATE;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrCurVMode_0x604
{
    struct __tagVModeElems
    {
        __uint32                                : 29;
        __uint32                m_nMode         :  3;
    }                           m;
    __uint32                    m_nAll;
} CSR_CUR_VMODE;

typedef union __tagCsrCurVMode_0x608
{
    struct __tagVFormatElems
    {
        __uint32                                : 29;
        __uint32                m_nFormat       :  3;
    }                           m;
    __uint32                    m_nAll;
} CSR_CUR_VFORMAT;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrIsoSettings_0x60C
{
    struct __tagIsoSettingsElems
    {
        __uint32                m_IsoSpeedB     :  3;   // IIDC-1.31
        __uint32                                :  5;
        __uint32                m_IsoChnB       :  6;   // IIDC-1.31
        __uint32                                :  1;
        __uint32                m_bOpMode       :  1;   // IIDC-1.31
        __uint32                                :  8;
        __uint32                m_nIsoSpeed     :  2;   // see 1394base.h
        __uint32                                :  2;
        __uint32                m_nIsoChn       :  4;
    }                           m;
    __uint32                    m_nAll;
} CSR_ISO_SETTINGS;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrCameraPower_0x610
{
    struct __tagCameraPowerElems
    {
        __uint32                                : 31;
        __uint32                m_bOnOff        :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_CAMERA_POWER;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrIsoEnable_0x614
{
    struct __tagIsoEnableElems
    {
        __uint32                                : 31;
        __uint32                m_bOnOff        :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_ISO_ENBALE;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrMemSave_0x618
{
    struct __tagMemSaveElems
    {
        __uint32                                : 31;
        __uint32                m_bSave         :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_MEM_SAVE;

typedef union __tagCsrMemSaveChn_0x620x624
{
    struct __tagMemSaveChnElems
    {
        __uint32                                : 28;
        __uint32                m_nChn          :  4;
    }                           m;
    __uint32                    m_nAll;
} CSR_MEM_SAVE_CHN,
  CSR_CUR_MEM_CHN;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrShot_0x61C
{
    struct __tagShotElems
    {
        __uint32                m_nShotCnt      : 16;               // number of shots
        __uint32                                : 14;
        __uint32                m_bMultiShot    :  1;
        __uint32                m_bOneShot      :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_SHOT;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrVModeErrorStat_0x628
{
    struct __tagVModeErrorStatElems
    {
        __uint32                                : 31;
        __uint32                m_bError        :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_VMODE_ERR_STAT;

// ---------------------------------------------------------------------------
//
typedef union __tagCsrSoftTrigger_0x62C         // IIDC-1.31
{
    struct __tagCsrSoftTriggerElems
    {
        __uint32                                : 31;
        __uint32                m_bTrigger      :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_SOFT_TRIGGER;

typedef union __tagCsrDataDepth_0x630           // IIDC-1.31
{
    struct __tagCsrDataDepthElems
    {
        __uint32                                : 24;
        __uint32                m_nDepth        :  8;
    }                           m;
    __uint32                    m_nAll;
} CSR_DATA_DEPTH;

// ---------------------------------------------------------------------------
//
typedef struct __tagCsrVideoMode
{
	CSR_CUR_VFRM_RATE			m_CurVFrmRate;
	CSR_CUR_VMODE				m_CurVMode;
	CSR_CUR_VFORMAT				m_CurVFormat;
	CSR_ISO_SETTINGS			m_IsoSettings;
} CSR_VIDEOMODE;

typedef struct __tagCsrCameraStatusCtrl_IIDC_130
{
	CSR_VIDEOMODE				m_Modes;
	CSR_CAMERA_POWER			m_CameraPower;
	CSR_ISO_ENBALE				m_IsoEnable;
	CSR_MEM_SAVE				m_MemSave;
	CSR_SHOT					m_Shot;
	CSR_MEM_SAVE_CHN			m_MemSaveChn;
	CSR_CUR_MEM_CHN				m_CurMemChn;
	CSR_VMODE_ERR_STAT			m_VModeErrStat;
} CSR_CAMERA_STATUS_CTRL_130;

typedef struct __tagCsrCameraStatusCtrl_IIDC_131
{
	CSR_VIDEOMODE				m_Modes;
	CSR_CAMERA_POWER			m_CameraPower;
	CSR_ISO_ENBALE				m_IsoEnable;
	CSR_MEM_SAVE				m_MemSave;
	CSR_SHOT					m_Shot;
	CSR_MEM_SAVE_CHN			m_MemSaveChn;
	CSR_CUR_MEM_CHN				m_CurMemChn;
	CSR_VMODE_ERR_STAT			m_VModeErrStat;
	CSR_SOFT_TRIGGER			m_SoftTrigger;      // IIDC-1.31
	CSR_DATA_DEPTH				m_DataDepth;        // IIDC-1.31
} CSR_CAMERA_STATUS_CTRL_131;

typedef union __tagCsrCameraStatusCtrl_0x600
{
	CSR_CAMERA_STATUS_CTRL_131	m_131;
	CSR_CAMERA_STATUS_CTRL_130	m_130;
} CSR_CAMERA_STATUS_CTRL;

/*****************************************************************************
    Feature Status and Control
*****************************************************************************/

#ifdef  BUG_TCPP_UNION_INIT
#define BRIGHTNESS_INIT(v5,v4,v3,v2,v1,v0)      ((v0?BIT31:0)|(v1?BIT30:0)|(v2?BIT26:0)|(v3?BIT25:0)|(v4?BIT24:0)|(v5&0xFFF))
#else
#define BRIGHTNESS_INIT(v5,v4,v3,v2,v1,v0)      { v5,v4,v3,v2,v1,v0 }
#endif

typedef union __tagCsrBrightness_0x800
{
    struct __tagBrightnessElems
    {
        __uint32                m_nValue        : 12;   // B0..11
        __uint32                                : 12;
        __uint32                m_bAMMode       :  1;   // B24
        __uint32                m_bOnOff        :  1;   // B25
        __uint32                m_bOnePush      :  1;   // B26
        __uint32                                :  3;
        __uint32                m_bAbsControl   :  1;   // B30
        __uint32                m_bPresence     :  1;   // B31
    }                           m;
    __uint32                    m_nAll;
} CSR_BRIGHTNESS,
  CSR_AUTOEXPOSURE,
  CSR_SHARPNESS,
  CSR_HUE,
  CSR_SATURATION,
  CSR_GAMMA,
  CSR_SHUTTER,
  CSR_GAIN,
  CSR_IRIS,
  CSR_FOCUS,
  CSR_FRAMERATE,                // IIDC-1.31
  CSR_ZOOM,
  CSR_PAN,
  CSR_TILT,
  CSR_OPTICAL_FILTER,
  CSR_CAPTURE_SIZE,
  CSR_CAPTURE_QUALITY;

#ifdef  BUG_TCPP_UNION_INIT
#define WHITEBAL_INIT(v6,v5,v4,v3,v2,v1,v0)     ((v0?BIT31:0)|(v1?BIT30:0)|(v2?BIT26:0)|(v3?BIT25:0)|(v4?BIT24:0)|((v5&0xFFF)<<12)|(v6&0xFFF))
#else
#define WHITEBAL_INIT(v6,v5,v4,v3,v2,v1,v0)     { v6,v5,v4,v3,v2,v1,v0 }
#endif

typedef union __tagCsrWhiteBal_0x80C
{
    struct __tagWhiteBalElems
    {
        __uint32                m_nVRValue      : 12;
        __uint32                m_nUBValue      : 12;
        __uint32                m_bAMMode       :  1;
        __uint32                m_bOnOff        :  1;
        __uint32                m_bOnePush      :  1;
        __uint32                                :  3;
        __uint32                m_bAbsControl   :  1;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_WHITEBAL;

#ifdef  BUG_TCPP_UNION_INIT
#define TEMPERATURE_INIT(v6,v5,v4,v3,v2,v1,v0)  WHITEBAL_INIT(v6,v5,v4,v3,v2,v1,v0)
#else
#define TEMPERATURE_INIT(v6,v5,v4,v3,v2,v1,v0)  WHITEBAL_INIT(v6,v5,v4,v3,v2,v1,v0)
#endif

typedef union __tagCsrTemperature_0x82C
{
    struct __tagTemperatureElems
    {
        __uint32                m_nTemp         : 12;
        __uint32                m_nTargetTemp   : 12;
        __uint32                m_bAMMode       :  1;
        __uint32                m_bOnOff        :  1;
        __uint32                m_bOnePush      :  1;
        __uint32                                :  3;
        __uint32                m_bAbsControl   :  1;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_TEMPERATURE;

typedef union __tagCsrTrigger_0x830
{
    struct __tagTriggerElems
    {
        __uint32                m_nParam        : 12;
        __uint32                                :  4;
        __uint32                m_nMode         :  4;
        __uint32                m_bTrgValue     :  1;   // IIDC-1.31
        __uint32                m_nTrgSrc       :  3;   // IIDC-1.31
        __uint32                m_bPolarity     :  1;
        __uint32                m_bOnOff        :  1;
        __uint32                                :  4;
        __uint32                m_bAbsControl   :  1;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_TRIGGER;

typedef union __tagCsrTriggerDelay_0x834        // IIDC-1.31
{
    struct __tagCsrTriggerDelayElems
    {
        __uint32                m_nValue        : 12;
        __uint32                                : 13;
        __uint32                m_bOnOff        :  1;
        __uint32                                :  4;
        __uint32                m_bAbsControl   :  1;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_TRIGGER_DLY;

typedef union __tagCsrWhiteShdg_0x838           // IIDC-1.31
{
    struct __tagCsrWhiteShdgElems
    {
        __uint32                m_nBValue       :  8;
        __uint32                m_nGValue       :  8;
        __uint32                m_nRValue       :  8;
        __uint32                m_bAMMode       :  1;
        __uint32                m_bOnOff        :  1;
        __uint32                m_bOnePush      :  1;
        __uint32                                :  3;
        __uint32                m_bAbsControl   :  1;
        __uint32                m_bPresence     :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_WHITE_SHDG;

// ---------------------------------------------------------------------------
//
typedef struct __tagCsrFeatureStatusCtrl_0x800
{
    CSR_BRIGHTNESS              m_Brightness;
    CSR_AUTOEXPOSURE            m_AutoExposure;
    CSR_SHARPNESS               m_Sharpness;
    CSR_WHITEBAL                m_WhiteBal;
    CSR_HUE                     m_Hue;
    CSR_SATURATION              m_Saturation;
    CSR_GAMMA                   m_Gamma;
    CSR_SHUTTER                 m_Shutter;
    CSR_GAIN                    m_Gain;
    CSR_IRIS                    m_Iris;
    CSR_FOCUS                   m_Focus;
    CSR_TEMPERATURE             m_Temperature;
    CSR_TRIGGER                 m_Trigger;
    CSR_TRIGGER_DLY             m_TriggerDelay;
    CSR_WHITE_SHDG              m_WhiteShdg;
    CSR_FRAMERATE               m_FrameRate;
    __uint32                    m_gap840[16];
    CSR_ZOOM                    m_Zoom;
    CSR_PAN                     m_Pan;
    CSR_TILT                    m_Tilt;
    CSR_OPTICAL_FILTER          m_OpticalFilter;
    __uint32                    m_gap890[12];
    CSR_CAPTURE_SIZE            m_CaptureSize;
    CSR_CAPTURE_QUALITY         m_CaptureQuality;
    __uint32                    m_gap8C8[14];
} CSR_FEATURE_STATUS_CTRL;

typedef struct __tagCsrFeatureStatusMirror
{
    CSR_GAMMA           m_regGamma;

} CSR_FEATURE_STATUS_MIRROR;

/*****************************************************************************
    Absolute value CSR
*****************************************************************************/

#define NUM_CSR_ABS_VALUE       64

typedef struct __tagCsrAbsCsrInq_0x700
{
    __uint32                    m_nOffset[NUM_CSR_ABS_VALUE];   // offset in quadlets
} CSR_ABS_CSR_INQ;

typedef struct __tagCsrAbsValue
{
    float                       m_fMinValue;
    float                       m_fMaxValue;
    float                       m_fValue;
} CSR_ABS_VALUE;

typedef struct __tagCsrAbsValueMask
{
    __uint32                    m_fMinValue;
    __uint32                    m_fMaxValue;
    __uint32                    m_fValue;
} CSR_ABS_VALUE_MASK;

typedef struct __tagCsrAbsValueAll
{
    CSR_ABS_VALUE               m_AbsVal[NUM_CSR_ABS_VALUE];
} CSR_ABS_VALUE_ALL;

/*****************************************************************************
    Feature control error status
*****************************************************************************/

// see CSR_FEATUREHI_INQ, CSR_FEATURELO_INQ

/*****************************************************************************
    Format 7
*****************************************************************************/
typedef S_IMAGEPOS              CSR_IMAGEPOS;
typedef S_IMAGESIZE             CSR_IMAGESIZE, CSR_IMAGESIZE_INQ;

typedef struct __tagCsrUnitPos
{
    __uint16                    m_nVPosUnit;
    __uint16                    m_nHPosUnit;
} CSR_UNITPOS;

typedef struct __tagCsrUnitSize
{
    __uint16                    m_nVUnit;
    __uint16                    m_nHUnit;
} CSR_UNITSIZE;

typedef union __tagF7ColorID
{
    struct __tagF7ColorIDElems
    {
        __uint32                                : 24;
        __uint32                m_nID           :  8;
    }                           m;
    __uint32                    m_nAll;
} CSR_F7_COLOR_ID;

typedef union __tagF7ColorCodingInq
{
    struct __tagF7ColorCodingInqElems
    {
        __uint32                                : 21;
        __uint32                m_bSRaw16       :  1;
        __uint32                m_bSRaw8        :  1;
        __uint32                m_bSRgb16       :  1;
        __uint32                m_bSMono16      :  1;
        __uint32                m_bRgb16        :  1;
        __uint32                m_bMono16       :  1;
        __uint32                m_bRgb8         :  1;
        __uint32                m_b444YUV8      :  1;
        __uint32                m_b422YUV8      :  1;
        __uint32                m_b411YUV8      :  1;
        __uint32                m_bMono8        :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_F7_COLOR_INQ;

typedef union __tagF7AdvColorCodingInq
{
    struct __tagF7AdvColorCodingInqElems
    {
        __uint32                                : 29;
        __uint32                m_bY8blue       :  1;
        __uint32                m_bY8green      :  1;
        __uint32                m_bY8red         :  1;
    }                           m;
    __uint32                    m_nAll;
} CSR_F7_ADV_COLOR_INQ;

typedef struct __tagPacketParamInq
{
    __uint16                    m_nMaxBytePerPacket;
    __uint16                    m_nUnitBytePerPacket;
} CSR_F7_PACKETPARAM_INQ;

typedef struct __tagPacketmPara
{
    __uint16                    m_nRecBytePerPacket;
    __uint16                    m_nBytePerPacket;
} CSR_F7_PACKETPARAM;

typedef union __tagDataDepthInq
{
    struct __tagDataDepthInqElems
    {
        __uint32                                : 24;
        __uint32                m_nDataDepth    :  8;
    }                           m;
    __uint32                    m_nAll;
} CSR_DATADEPTH_INQ;

typedef struct __tagCsrFormat7
{
    CSR_IMAGESIZE_INQ           m_ImageSizeInq;
    CSR_UNITSIZE                m_UnitSizeInq;

    CSR_IMAGEPOS                m_ImagePos;
    CSR_IMAGESIZE               m_ImageSize;
    // 0x10
    CSR_F7_COLOR_ID             m_ColorCoding;
    CSR_F7_COLOR_INQ            m_ColorCodingInq;
    // 0x18
    __uint32                    m_gap018[7];
    // 0x34
    __uint32                    m_nPixelNumInq;
    __uint32                    m_nTotalBytesHiInq;
    __uint32                    m_nTotalBytesLoInq;
    // 0x40
    CSR_F7_PACKETPARAM_INQ      m_PacketParaInq;
    CSR_F7_PACKETPARAM          m_PacketSize;
    // 0x48
    __uint32                    m_PacketPerFrameInq;
    // 0x4C
    CSR_UNITPOS                 m_UnitPosInq;
    // 0x50
    __uint32                    m_FrameIntervalInq;     // IIDC v1.31
    // 0x54
    CSR_DATADEPTH_INQ           m_DataDepthInq;         // IIDC v1.31
    // 0x58
    __uint32                    m_ColorFilterID;        // IIDC v1.31
    // 0x5C
    __uint32                    m_gap05C[8];

    struct __tagValueSetting
    {
        __uint32                                : 22;
        __uint32                m_bError2       :  1;
        __uint32                m_bError1       :  1;
        __uint32                                :  6;
        __uint32                m_bSetting1     :  1;
        __uint32                m_bPresence     :  1;
    }                           m_ValueSetting;
} CSR_FORMAT7;

typedef struct __tagCsrFormat7Ex
{
    CSR_FORMAT7                 m_DCam;

    // following members are always overwritten, by SetRegisterDefaultValue()
    // ApplyRwMask() in contrast observes m_nMapSize, if defined

    struct __tagBinningFormat7
    {
        __uint8                 m_nV;
        __uint8                 m_nH;
    }                           m_Binning;

    struct __tagColorIdDependencies
    {
        __uint8                 m_nUsedBits4Data16;		//! number of bits used for MONO16/RAW16
    }                           m_ColorDependencies;

    struct __tagInfo
    {
        __uint32                m_nFrameReadoutTime1us; //! time required to read out and store an image into memory
        __uint32                m_nMinPacketsPerFrame;  //! used to calc the fastest capture time
    }                           m_Info;

} CSR_FORMAT7_EX;

/*****************************************************************************
    PIO Control Register (IIDC-1.31)
*****************************************************************************/
typedef struct __tagCsrPio
{
    __uint32                    m_nOutputs;
    __uint32                    m_nInputs;
} CSR_PIO;

/*****************************************************************************
    SIO Control Register (IIDC-1.31)
*****************************************************************************/
typedef enum
{
    ESIO_300        = 0,
    ESIO_600,
    ESIO_1200,
    ESIO_2400,
    ESIO_4800,
    ESIO_9600,
    ESIO_19200,
    ESIO_38400,
    ESIO_57600,
    ESIO_115200,
    ESIO_230400
} OPT_SIO_BPS;

typedef union __tagCsrOptSioModeReg
{
	struct __tagCsrOptSioModeRegElems
	{
		__uint32				m_nBufferSize   :  8;
		__uint32                                :  4;
		__uint32                m_nStopBits     :  2;
		__uint32                m_nParity       :  2;
		__uint32                m_nCharLength   :  8;
		__uint32                m_nBitrate      :  8;
	}							m;
	__uint32					m_nAll;
} CSR_OPT_SIO_MODE;

typedef union __tagCsrOptSioCtrlReg
{
	struct __tagCsrOptSioCtrlRegElems
	{
		__uint32                                : 17;
		__uint32                m_bRxParityErr  :  1;
		__uint32                m_bRxFrameErr   :  1;
		__uint32                m_bRxOverrun    :  1;
		__uint32                                :  1;
		__uint32                m_bRxReady      :  1;
		__uint32                                :  1;
		__uint32                m_bTxReady      :  1;
		__uint32                                :  6;
		__uint32                m_bTxEnable     :  1;
		__uint32                m_bRxEnable     :  1;
	}							m;
	__uint32					m_nAll;
} CSR_OPT_SIO_CTRL;

typedef union __tagCsrOptSioRxBufStatus
{
	struct __tagCsrOptSioRxBufStatusElems
	{
		__uint32                                : 16;
		__uint32                m_nBufCnt       :  8;
		__uint32                m_nBufSt        :  8;
	}							m;
	__uint32					m_nAll;
} CSR_OPT_SIO_RXBUF_STATUS,
  CSR_OPT_SIO_TXBUF_STATUS;

typedef struct __tagCsrOptSioLo
{
    CSR_OPT_SIO_MODE            m_Mode;
    CSR_OPT_SIO_CTRL            m_Ctrl;
    CSR_OPT_SIO_RXBUF_STATUS    m_RxStatus;
    CSR_OPT_SIO_TXBUF_STATUS    m_TxStatus;
} CSR_OPT_SIO_LO;

typedef union __tagCsrOptSioHi
{
    __uint8                     m_arrData8[256];
    __uint32                    m_arrData32[64];
} CSR_OPT_SIO_HI;

//typedef struct __tagCsrOptSio
//{
//    CSR_SIO_MODE_REG            m_Mode;
//    CSR_SIO_CTRL_REG            m_Ctrl;
//    CSR_SIO_RXBUFFER_STATUS     m_RxStatus;
//    CSR_SIO_TXBUFFER_STATUS     m_TxStatus;
//    __uint32                    m_gap010[60];
//    union __tagSioData
//    {
//        __uint8                 m_arr8[256];
//        __uint32                m_arr32[64];
//    }                           m_Data;
//} CSR_OPT_SIO;

/*****************************************************************************
    Strobe Control Register (IIDC-1.31)
*****************************************************************************/

/*****************************************************************************
    Access Control Register
*****************************************************************************/

typedef union __tagCsrAccessCtrl
{
    __uint64                    m_nAll;

    struct __tagAccessCtrlElemsWr
    {
        __uint32                m_nFeatureHiID  : 32;
        __uint32                m_nTout         : 12;
        __uint32                                :  4;
        __uint32                m_nFeatureLoID  : 16;
    }                           m_Wr;

    struct __tagAccessCtrlElemsRd
    {
        __uint32                                : 16;
        __uint32                m_nBusNodeID    : 16;
        __uint32                m_nTout         : 12;
        __uint32                                : 20;
    }                           m_Rd;

} CSR_ACCESS_CTRL;

/*****************************************************************************
*****************************************************************************/

typedef struct __tagCsrAll
{
    CSR_INITIALIZE              m_csrInitialize;                // rw
    CSR_VFORMAT_INQ             m_csrVFormatInq;                // r
    CSR_VMODE_INQ_ALL           m_csrVModeInq;                  // r
    CSR_VFRM_RATE_INQ_ALL       m_csrVFrameRateInq;             // r
    CSR_BASICFNC_INQ            m_csrBasicFncInq;               // r
    CSR_FEATURE_INQ             m_csrFeatureInq;                // r
    CSR_ADVFEATURE_INQ          m_csrAdvFeatureInq;             // r
    CSR_FEATURECAPABILITIES_INQ m_csrFeatureCapabilitiesInq;    // r

    CSR_CAMERA_STATUS_CTRL		m_csrCameraStatusCtrl;          // rw
    CSR_FEATURE_STATUS_CTRL     m_csrFeatureStatusCtrl;         // rw

    CSR_ABS_CSR_INQ             m_csrAbsCsrInq;                 // r
    CSR_ABS_VALUE_ALL           m_csrAbsValue;                  // rw

    CSR_FEATURE_ERRSTAT         m_csrFeatureErrStat;            // r

    CSR_FORMAT7                 m_csrFormat7[NUM_FORMAT7_MODES];// rw

    CSR_ACCESS_CTRL             m_csrAccessCtrl;                // rw
} CSR_ALL;

/*****************************************************************************
    Fixed video formats
*****************************************************************************/

typedef struct __tagFixedVideoMode
{
    __uint16                    m_nWidth;
    __uint16                    m_nHeight;
    __uint8                     m_nColorCoding;

    __uint16                    m_nPacketSize4[NUM_FPS_IDS];
    __uint8                     m_bSpeedReq[NUM_FPS_IDS];
} CSR_FIXED_VMODE;

typedef struct __tagFixedVideoFormats
{
    CSR_FIXED_VMODE             m_Formats[NUM_FIXED_FORMATS][NUM_MODES];

} CSR_FIXED_VFORMATS;

// ---------------------------------------------------------------------------
//
#ifdef _MSC_VER
    #pragma pack(pop, vnd1)
#endif

#ifdef __cplusplus
    } /// extern "C"

    #ifndef __arm
    } /// namespace csr_std
    #endif
#endif

#endif /// #ifndef  __CSR_STRUCTS_H
