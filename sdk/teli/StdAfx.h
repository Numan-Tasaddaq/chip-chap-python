// stdafx.h : include file for standard system include files,
//  or project specific include files that are used frequently, but
//      are changed infrequently
//

#if !defined(AFX_STDAFX_H__26129EFA_B63D_11D5_95CD_0050DA74F9AA__INCLUDED_)
#define AFX_STDAFX_H__26129EFA_B63D_11D5_95CD_0050DA74F9AA__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000


// This prevents a lot of silly warnings regarding the use of the STL
#pragma warning (disable: 4786)
// This tells BCAM to use the MFC
#define USE_MFC

// BCAM can be used with Windows >= Win2k only
//#define WINVER 0x0500		//Workaround in Bcam.h to avoid this definition




#define VC_EXTRALEAN		// Exclude rarely-used stuff from Windows headers

#include <afxwin.h>         // MFC core and standard components
#include <afxext.h>         // MFC extensions

#ifndef _AFX_NO_OLE_SUPPORT
#include <afxole.h>         // MFC OLE classes
#include <afxodlgs.h>       // MFC OLE dialog classes
#include <afxdisp.h>        // MFC Automation classes
#endif // _AFX_NO_OLE_SUPPORT


#ifndef _AFX_NO_DB_SUPPORT
#include <afxdb.h>			// MFC ODBC database classes
#endif // _AFX_NO_DB_SUPPORT

#ifndef _AFX_NO_DAO_SUPPORT
#include <afxdao.h>			// MFC DAO database classes
#endif // _AFX_NO_DAO_SUPPORT

#include <afxdtctl.h>		// MFC support for Internet Explorer 4 Common Controls
#ifndef _AFX_NO_AFXCMN_SUPPORT
#include <afxcmn.h>			// MFC support for Windows Common Controls
#endif // _AFX_NO_AFXCMN_SUPPORT

#include <stdio.h>
#include <conio.h>
#include <iostream>
#include <Windows.h>
#include <string>
//#include "Camera.h"
#include "csr_structs_adv.h"
#include "structs.h"

#include "TeliCamApi.h"
#include "TeliCamUtl.h"

//{{AFX_INSERT_LOCATION}}
// Microsoft Visual C++ will insert additional declarations immediately before the previous line.

#endif // !defined(AFX_STDAFX_H__26129EFA_B63D_11D5_95CD_0050DA74F9AA__INCLUDED_)
