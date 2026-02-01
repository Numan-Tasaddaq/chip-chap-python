/*****************************************************************************
 *
 *
 *
 ****************************************************************************/

#ifndef	__DCAM_BASE_H
#define	__DCAM_BASE_H

#ifdef __cplusplus
	extern "C" {
#endif

/*****************************************************************************
*****************************************************************************/

#ifdef __arm
#define	DCAM_BASE				0xFFFFF0000000llu
#define	DCAM_REG_OFF			0x000000F00000
#define	DCAM_ABS_OFF			0x000000F00000
#define	DCAM_OPT_OFF			0x000000F00000
#define	DCAM_FM7_OFF			0x000000F00000
#define	DCAM_ADV_OFF			0x000000000000
#define DCAM_VND_OFF            0x000000000000
#else
#define	DCAM_BASE				0xFFFFF0000000
#define	DCAM_REG_OFF			0x000000F00000
#define	DCAM_ABS_OFF			0x000000F00000
#define	DCAM_OPT_OFF			0x000000F00000
#define	DCAM_FM7_OFF			0x000000F00000
#define	DCAM_ADV_OFF			0x000000000000
#define DCAM_VND_OFF            0x000000000000
#endif

/*****************************************************************************
*****************************************************************************/

#ifndef	BIT31
#define	BIT31	0x80000000
#endif

//! BIT[0] in all DCAM register equals to BIT31 on this machine
#define DCAM_BIT0               BIT31
#define DCAM_BIT1				(DCAM_BIT0 >> 1)
#define DCAM_BIT2				(DCAM_BIT0 >> 2)
#define DCAM_BIT3				(DCAM_BIT0 >> 3)
#define DCAM_BIT4				(DCAM_BIT0 >> 4)
#define DCAM_BIT5				(DCAM_BIT0 >> 5)
#define DCAM_BIT8				(DCAM_BIT0 >> 8)
#define DCAM_BIT16              (DCAM_BIT0 >> 16)

#define NUM_FORMATS             8
#define NUM_FIXED_FORMATS       3

#define NUM_MODES               8
#define MAX_FIXED_MODE          7

#define NUM_FPS_IDS             8
#define MAX_FPS_ID              5

#define NUM_FORMAT7_MODES       8

typedef enum __tagVideoFormats
{
    E_VFORMAT_0             = 0,
    E_VFORMAT_1,
    E_VFORMAT_2,
    E_VFORMAT_3,
    E_VFORMAT_4,
    E_VFORMAT_5,
    E_VFORMAT_6,
    E_VFORMAT_7
} E_VFORMAT;

typedef enum __tagColorCoding
{
    ECCID_MONO8             = 0,
    ECCID_411YUV8,
    ECCID_422YUV8,
    ECCID_444YUV8,
    ECCID_RGB8,
    ECCID_MONO16,
    ECCID_RGB16,
	// IIDC v1.31
	ECCID_SMONO16,
	ECCID_SRGB16,
	ECCID_RAW8,
	ECCID_RAW16,

    ECCID_LAST
} E_COLORCODING_ID;

#ifdef __cplusplus
	}
#endif

#endif /// #ifndef	__DCAM_BASE_H
