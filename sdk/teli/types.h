/*****************************************************************************
 *
 *
 *
 ****************************************************************************/

#ifndef __TYPES_H
#define	__TYPES_H

#ifdef __cplusplus
    extern "C" {
#endif

/*****************************************************************************
*****************************************************************************/

#if !defined(__cplusplus) && !defined(bool)
	#define	true			    1
	#define	false			    0

	typedef	unsigned int 	    bool;
#endif

#ifndef TRUE
    #define TRUE                1
    #define FALSE               1
#endif

#if !defined(__int8_type) && !defined(_MSC_VER)
	#define	__int8_type

	typedef	char			    __int8;
	typedef	short			    __int16;
	typedef	int			    	__int32;
//	typedef	long long    		__int64;
#endif

#if !defined(__uint8_type)
	#define	__uint8_type

	typedef unsigned char	    __uint8;
	typedef unsigned short	    __uint16;
	typedef unsigned int	    __uint32;
	typedef unsigned __int64	__uint64;
#endif

#if !defined(__INT8_type) && !defined(_MSC_VER)
	#define	__INT8_type

    typedef __int8              INT8;
    typedef __int16             INT16;
    typedef __int32             INT32;
    typedef __int64             INT64;
#endif

#if !defined(__UINT8_type) && !defined(_MSC_VER)
	#define	__UINT8_type

    typedef __uint8             UINT8;
    typedef __uint16            UINT16;
    typedef __uint32            UINT32;
    typedef __uint64            UINT64;
#endif

#ifndef __crc16
	typedef __uint16		    __crc16;
	typedef __uint32		    __crc32;
#endif

#ifndef __quadlet
    typedef __uint32            __quadlet;
#endif

#ifndef __1394GUID
    typedef __uint64            __1394GUID;
#endif

/*****************************************************************************
*****************************************************************************/

/*****************************************************************************
*****************************************************************************/

#ifndef __arm
    #define __irq
#endif

/*****************************************************************************
*****************************************************************************/

#ifdef __cplusplus
    }
#endif

#endif /// #if !defined(__TYPES_H)
