///////////////////////////////////////////////////////////////////////////////
// file    : TeliTypes.h
// brief   : API Type header
// version : 1.0.0.0
// author  : (C)2013 TOSHIBA TELI CORPORATION 
// date    : 2013/05/13

#ifndef _TELI_TYPES_H_
#define _TELI_TYPES_H_

#include <stdio.h>

#if defined (_WIN32)
	#if defined(_MSC_VER) && _MSC_VER >= 1600
		// VS2010 provides stdint.h
		#if defined(_MSC_VER)
		#pragma warning (push)
		#pragma warning (disable : 4005)
		#endif

		#include <stdint.h>

		#if defined(_MSC_VER)
		#pragma warning (pop)
		#endif
	#else
		#ifndef _STDINT // only define if not already done

	     typedef char                int8_t;
	     typedef unsigned char       uint8_t;

	     typedef short               int16_t;
	     typedef unsigned short      uint16_t;

	     typedef __int32             int32_t;
	     typedef unsigned __int32    uint32_t;

	     typedef __int64             int64_t;
	     typedef unsigned __int64    uint64_t;

		#endif // _STDINT
	#endif // _MSC_VER >= 1600
#else
	#include <stdint.h>
	//#include <stddef.h>
	#include <pthread.h>
	#include <limits.h>
	#include <linux/limits.h>

	typedef int HANDLE;

	#ifndef MAX_PATH
		#define	MAX_PATH	PATH_MAX
	#endif

	#ifndef CALLBACK
		#define	CALLBACK
	#endif
#endif


#ifndef _SIZE_T_DEFINED
    #ifdef  _WIN64
         typedef unsigned __int64    size_t;
    #else
         typedef unsigned int        size_t;
    #endif
    #define _SIZE_T_DEFINED
#endif

#ifndef bool8_t
	#ifdef __cplusplus
		 typedef bool       bool8_t;
	#else
		 typedef uint8_t    bool8_t;
	#endif
#endif

#ifndef float32_t
	typedef float     float32_t;
#endif

#ifndef float32_t
	typedef double    float64_t;
#endif

#ifndef byte
	typedef unsigned char byte;
#endif

#ifndef _STDINT
    #ifndef INT64_MAX
        #define INT64_MAX   0x7fffffffffffffffLL
    #endif

    #ifndef INT64_MIN
        #define INT64_MIN   0x8000000000000000LL
    #endif

    #ifndef UINT64_MAX
        #define UINT64_MAX  0xffffffffffffffffULL
    #endif

    #ifndef INT32_MAX
        #define INT32_MAX   0x000000007fffffffLL
    #endif

    #ifndef INT32_MIN
        #define INT32_MIN   0xffffffff80000000LL
    #endif

    #ifndef UINT32_MAX
        #define UINT32_MAX  0x00000000ffffffffULL
    #endif

    #ifndef INT8_MAX
        #define INT8_MAX    0x000000000000007fLL
    #endif

    #ifndef INT8_MIN
        #define INT8_MIN    0xffffffffffffff80LL
    #endif

    #ifndef UINT8_MAX
        #define UINT8_MAX   0x00000000000000ffULL
    #endif
#endif // _STDINT

#endif //_TELI_TYPES_H_

