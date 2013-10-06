/* This is the header file with default configuration material
* for all of the motes. All motes are synchronized at the moment.
*
* @date:	4 October 2013
* @revision: 	1.0
* @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
* 		National and Kapodistrian University of Athens,
* 		Dept. Informatics & Telecommunications
*		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
*/

#include <stdint.h>

#ifndef COMM_QUEUE_H
#define COMM_QUEUE_H

/* The dimensions that we currently have */
#define DIMS 1

#define DATA_SIZE ( sizeof( uint16_t ) * DIMS )
// #define DATA_SIZE 20

#define QUEUE_SUCCESS 0
#define QUEUE_FULL -1
#define QUEUE_EXISTING_ITEM -2


/* A struct the describes the basic information we care about */
typedef struct comm_queue_t {
	uint8_t id;				/* The id of the node that initiated this network packet */
	int32_t seqNo;			/* A unique sequence number */
	uint8_t data[DATA_SIZE];	/* The actual data that we care about */
} comm_queue_t;

/**
 * Enqueue the message that is INITIALLY sent by srcId, with the given seqNo.
 *
 * */
int enqueue( comm_queue_t msg );

comm_queue_t* dequeue( );

uint8_t queue_size();

#endif

