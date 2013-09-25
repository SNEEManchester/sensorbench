/* This is the header file with default configuration material
* for all of the motes. All motes are synchronized at the moment.
*
*
* @date:	25 February 2011
* @revision: 	1.0
* @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
* 		National and Kapodistrian University of Athens,
* 		Dept. Informatics & Telecommunications
*		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
*/

#ifndef LR_NAIVE_GEN_H
#define LR_NAIVE_GEN_H

/* Thif file contains generic information for all of the motes, 
also used for their configuration. In this file, we place all
of our #DEFINES, to know where to look for them */

#ifndef max
    #define max(a,b) (((a) > (b)) ? (a) : (b))
#endif
#ifndef min
	#define min(a,b) (((a) < (b)) ? (a) : (b))
#endif

#define WINDOW_SIZE 10000		//The size of the window for the query
#define SLIDE_SIZE 10000		//How much the window slides for the new set of tuples
#define SAMPLING_FREQUENCY 5000		// sampling frequency in milliseconds

#define DIMS 2	// number of dimensions

typedef uint16_t read_type_t;

/* The number of readings that we need before starting transmitting data.
* The (default) maximum number of payload bytes is 28. This gives us up to 26 bytes
* of readings to be transmitted. This can be interpreted as 13 readings (each reading is
* a uint16_t value). We can have 5 readings without a problem */
#define BFR_SZ (WINDOW_SIZE / SAMPLING_FREQUENCY)	// The buffer where read tuples are stored, before being sent

/* The number of maximum readings that we can have in a radio message.
 * The (default) maximum payload is 28 bytes. This gives us up to 26 bytes of payload,
 * which can be interpreted as 13 readings of (x,y) values, provided that each reading
 * is a single byte ([0,255] range) or 6 readings of (x,y) values in the [0,65535] range */
#define RADIO_READINGS ((28 - 2 * sizeof(nx_uint8_t))/( DIMS * sizeof(read_type_t)))

/* The number of bytes that are required to host RADIO_READINGS readings */
#define RADIO_BYTES (RADIO_READINGS * DIMS * sizeof(read_type_t))


/* HERE WE DEFINE POSSIBLE ERROR CODES */
#define AM_LOCKED_OK 0
#define AM_CONTROL_NOT_STARTED -1
#define AM_CONTROL_STOP_DONE_OK -2
#define AM_SEND_LOCK_FAILED -3
#define AM_SEND_IS_LOCKED -4
#define TEMPR_SENSOR_READ_ERROR -5
#define RADIO_MSG_TOO_LARGE -6
#define MOIST_SENSOR_READ_ERROR -7


enum {
	//AM_OSCILLOSCOPE = 0x93
	AM_RADIO_COUNT_MSG = 0x93
//	AM_RADIO_COUNT_MSG = 6
};

/* This is most likely a struct that we populate ourselves
* The sampling frequency may not be required.
* Note that if we increaase the BFR_SZ too much, we may have
* to re-wire the message_t library.
*
* The maximum size that I have encountered this far is 2 readings (2 * 2 bytes) + 
* 4 uint16_t variables, i.e. 4 * 2 bytes. This gives: 12 bytes in total. */
typedef struct {
	uint8_t id;			//id of the sending mote
	uint8_t readings[ 5 * sizeof(uint32_t) ];	//The actual readings themselves. Contains ALL readings
} radio_count_msg_t;


#endif

