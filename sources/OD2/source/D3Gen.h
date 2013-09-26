/* This is the header file with default configuration material for all of the motes.
* All motes are synchronized at the moment. For more information on the D3 algorithm, see
*
*	Sharmila Subramaniam, Themis Palpanas, Dimitris Papadopoulos, Vana Kalogeraki, Dimitrios Gunopulos:
*	Online Outlier Detection in Sensor Data Using Non-Parametric Models. VLDB, 2006
*
*
* @date:	3 March 2011
* @revision: 	1.0
* @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
* 		National and Kapodistrian University of Athens,
* 		Dept. Informatics & Telecommunications
*		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
*/


#ifndef D3_GEN_H
#define D3_GEN_H

/* Some macros that come in handy */
#ifndef max
    #define max(a,b) (((a) > (b)) ? (a) : (b))
#endif
#ifndef min
	#define min(a,b) (((a) < (b)) ? (a) : (b))
#endif


/* Whether we are in debug or in normal execution mode */
#define DEBUG 1

/* The dimensions that we currently have */
#define DIMS 1

#define WINDOW_SIZE 10000	//The size of the window for the query
#define SLIDE_SIZE 10000	//How much the window slides for the new set of tuples
#define SAMPLING_FREQUENCY 5000	// sampling frequency in milliseconds

/* The maximum number of allowed tuples, based on the window size and the sampling frequency */
#define MAX_WINDOW_SIZE (WINDOW_SIZE / SAMPLING_FREQUENCY)

/* The percentage of points from the buffer that are used as a sample of the actual readings. */
#define SAMPLE_PRCNT 1.0

/* The size of the sample that we are using to approximate the data distribution */
#define SAMPLE_SIZE max( (int)(MAX_WINDOW_SIZE * SAMPLE_PRCNT + 0.5), 1 )

/* This is the range used for the neighborhood */
#define RANGE 5

/* A probability under which tuples are marked as outliers */
#define OUTLIER_PROB 0.15

/* Computing the outlier threshold, in number of tuples */
#define OUTLIER_THRESHOLD max( (int)(OUTLIER_PROB * MAX_WINDOW_SIZE + 0.5), 1 )

#define MIN_VAL 0
#define MAX_VAL 1024

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
	AM_RADIO_COUNT_MSG = 0x93,
};

/* The current maximum number of readings that can be sent.
* The (default) maximum number of payload bytes is 28. This gives us up to 26 bytes
* of readings to be transmitted. This can be interpreted as 13 readings (each reading is
* a uint16_t value). We can have 5 readings without a problem */
/* 
* In this case, the size is fixed and contains 5 numbers: the four sum and their count.
* Other than that, we only care about who sent those readings. Values are currently uint32_t
* because they are summations, and may go way too high
*
*/
typedef nx_struct radio_count_msg {
	nx_uint8_t id;				//id of the sending mote
	//The actual readings themselves. Contains ALL readings that have been marked as outliers
	nx_uint8_t readings[DIMS * sizeof(float)];
} radio_count_msg_t;

#endif

