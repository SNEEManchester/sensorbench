/* This is the implementation file for the queue that we use, when motes want to communicate.
*
* @date:	4 October 2013
* @revision: 	1.0
* @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
* 		National and Kapodistrian University of Athens,
* 		Dept. Informatics & Telecommunications
*		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
*/

#include "CommQueue.h"


uint8_t initialized = 0;

/* Create a queue with the items we are going to propagate across the network.
* The head indicates where we remove items from, the tail indicates where we add. */
uint8_t count = 0;

uint8_t headIndex = 0;

uint8_t tailIndex = 0;

#define QUEUE_SIZE 255

comm_queue_t queue[QUEUE_SIZE];


/**
 * Attemps to add the given item to the existing queue.
 * If the queue is already full, we return a negative value.
 * */
int enqueue( comm_queue_t msg ){

	uint8_t i = 0;

	/* If the queue has not been initialized, do that */
	if ( !initialized ){

		/* Set all positions to empty values */
		for ( ; i < QUEUE_SIZE; i++ )
			queue[i].seqNo = -1;

		initialized = 1;
	}

	/* If the number of items in the queue is maxed out, return an error code */
	if ( count == QUEUE_SIZE )
		return -1;

	/* Check if the item already exists (matching id, seqNo and hops). */
	for ( i = 0; i < QUEUE_SIZE; i++ )
		if ( queue[i].seqNo == msg.seqNo && queue[i].id == msg.id )
			return QUEUE_EXISTING_ITEM;

	/* Add the item in the tail */
	queue[ tailIndex ] = msg;

	/* Find the position where the next item should be placed */
	tailIndex++;
	tailIndex = tailIndex % QUEUE_SIZE;

	/* Increase the size of the queue by 1 */
	count++;

	/* Return 0 (OK) */
	return 0;
}


/**
 * Dequeues the foremost item from the existing queue.
 * If the queue is empty, NULL is returned instead.
 * */
comm_queue_t* dequeue( ){

	comm_queue_t* curMsg = 0x0;

	/* If there are no items in the queue, return NULL */
	if ( count == 0 )
		return 0x0;

	/* Keep a pointer to the current item */
	curMsg = queue + headIndex;

	/* Proceed the head index to the next position */
	headIndex++;
	headIndex = headIndex % QUEUE_SIZE;

	/* Decrease the number of items we have */
	count--;

	/* Return the data of the current message. */
	return curMsg;
}


/**
 * Returns the size of the queue
 * */
uint8_t queue_size(){
	return count;
}
