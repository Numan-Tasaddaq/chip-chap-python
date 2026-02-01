///////////////////////////////////////////////////////////////////////////////
// file    : TeliCamNode.h
// brief   : API Header file
// version : 1.0.0.0
// author  : (C)2013 TOSHIBA TELI CORPORATION 
// date    : 2013/10/09

#ifndef _TELI_CAM_NODE_H_
#define _TELI_CAM_NODE_H_

namespace Teli {

	///////////////////////////////////////////////////////////////////////////////
	// Parameter and Structure declarations

	///////////////////////////////////////////////////////////
	// Commands and flags

	// Node type
	typedef enum
	{
		TC_NODE_TYPE_VALUE = 0,
		TC_NODE_TYPE_BASE,
		TC_NODE_TYPE_INTEGER,
		TC_NODE_TYPE_BOOLEAN,
		TC_NODE_TYPE_COMMAND,
		TC_NODE_TYPE_FLOAT,
		TC_NODE_TYPE_STRING,
		TC_NODE_TYPE_REGISTER,
		TC_NODE_TYPE_CATEGORY,
		TC_NODE_TYPE_ENUMERATION,
		TC_NODE_TYPE_ENUM_ENTRY,
		TC_NODE_TYPE_PORT,
		TC_NODE_TYPE_UNKNOWN
	} TC_NODE_TYPE;

	// Node access mode of a node
	typedef enum
	{
		TC_NODE_ACCESS_MODE_NI,              // Not implemented
		TC_NODE_ACCESS_MODE_NA,              // Not available
		TC_NODE_ACCESS_MODE_WO,              // Write Only
		TC_NODE_ACCESS_MODE_RO,              // Read Only
		TC_NODE_ACCESS_MODE_RW,              // Read and Write
		TC_NODE_ACCESS_MODE_Undefined,       // Object is not yet initialized
		TC_NODE_ACCESS_MODE_UNKNOWN
	} TC_NODE_ACCESS_MODE;

	// Recommended visibility of a node
	typedef enum
	{
		TC_NODE_VISIBILITY_BEGINNER,          // Always visible
		TC_NODE_VISIBILITY_EXPERT,            // Visible for experts or Gurus 
		TC_NODE_VISIBILITY_GURU,              // Visible for Gurus
		TC_NODE_VISIBILITY_INVISIBLE,         // Not Visible
		TC_NODE_VISIBILITY_Undefined,         // Object is not yet initialized
		TC_NODE_VISIBILITY_UNKNOWN
	} TC_NODE_VISIBILITY;

	// Caching mode of a register
	typedef enum
	{
		TC_NODE_CACHING_MODE_NO_CACHE,        // Do not use cache
		TC_NODE_CACHING_MODE_WRITE_THROUGH,   // Write to cache and register
		TC_NODE_CACHING_MODE_WRITE_AROUND,    // Write to register, write to cache on read
		TC_NODE_CACHING_MODE_UNDEFINED,       // Not yet initialized
		TC_NODE_CACHING_MODE_UNKNOWN
	} TC_NODE_CACHING_MODE;

	// Recommended representation of a node value 
	typedef enum
	{
		TC_NODE_REPRESENTATION_LINEAR,         // Slider with linear behavior
		TC_NODE_REPRESENTATION_LOGARITHMIC,    // Slider with logarithmic behaviour.
		TC_NODE_REPRESENTATION_BOOLEAN,        // Check box
		TC_NODE_REPRESENTATION_PURE_NUMBER,    // Decimal number in an edit control
		TC_NODE_REPRESENTATION_HEX_NUMBER,     // Hex number in an edit control
		TC_NODE_REPRESENTATION_IPV4_ADDRESS,   // IPV4-Address
		TC_NODE_REPRESENTATION_MAC_ADDRESS,    // MAC-Address
		TC_NODE_REPRESENTATION_UNDEFINED,      // Not yet initialized
		TC_NODE_REPRESENTATION_UNKNOWN
	} TC_NODE_REPRESENTATION;

	// Float notation 
	typedef enum
	{
		TC_NODE_DISPLAY_NOTATION_AUTOMATIC,    // the notation if either scientific or fixed depending on what is shorter 
		TC_NODE_DISPLAY_NOTATION_FIXED,        // the notation is fixed, e.g. 123.4 
		TC_NODE_DISPLAY_NOTATION_SCIENTIFIC,   // the notation is scientific, e.g. 1.234e2 
		TC_NODE_DISPLAY_NOTATION_UNDEFINED,    // Object is not yet initialized
		TC_NODE_DISPLAY_NOTATION_UNKNOWN
	} TC_NODE_DISPLAY_NOTATION;


	///////////////////////////////////////////////////////////
	// Structures

	// GenICam error message
	typedef struct _TC_GENICAM_ERR_MSG
	{
		const int8_t*      pDescription;       // Error description.
		const int8_t*      pSourceFileName;    // Filename in which the error occurred. 
		uint32_t           iSourceLine;        // Line number at which the error occurred. 
	} TC_GENICAM_ERR_MSG, *PTC_GENICAM_ERR_MSG;

}	// end of namespace Teli

#endif //_TELI_CAM_NODE_H_
