/**
* This is the implementation of the D3 distributed outlier detection algorithm.
* This is the most simplistic approach, where each node only senses its own environment,
* without belonging to a hierarchy.
*
* Though there is a root node, this is only used to receive the incoming detected outliers.
* Each node simply senses its environment, finds its outliers and sends them to the parent node.
* The parent simply prints those outliers in the console output. Perhaps, a later version of this
* code, may add functionality on the root (or basestation), seeing which local outliers are also
* global outliers.
*
*
* We assume that a communication tree is already in place and that it is static (does not change).
* All sensors are equal, since there is no hierarchy. They sense their surroundings and find
* outliers, using Scott's rule, as described in [1]. Once an outlier has been detected, we inform
* the parent node of that outlier. We send only one outlier at a time. This is easier to implement.
*
* We assume that the network tree is rooted at TOS_NODE_ID = 0
*
* Note that the scheme is practically sequential!
*
* @date:	3 March 2011
* @revision: 	1.0
* @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
* 		National and Kapodistrian University of Athens,
* 		Dept. Informatics & Telecommunications
*		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
*
*
* References:
*	[1] Sharmila Subramaniam, Themis Palpanas, Dimitris Papadopoulos, Vana Kalogeraki, Dimitrios Gunopulos
*	Online Outlier Detection in Sensor Data Using Non-Parametric Models. VLDB, 2006

*/

#include "Timer.h"		// For use of timer
#include "AvroraPrint.h"	// For debugging purposes
#include "D3.h"

#include <stdlib.h>
#include <stdio.h>

/**
* This is an implementation of a mote that reads values and builds a Linear Regression
* classifier inside the Wireless Sensor Network.
* The safe() annotation does not do anything, as we are running TinyOS 2.0, which does
* not have this kind of support.
*/
module D3C @safe() {

	/* The interfaces that this application requires. We need the following for our application:
	* Boot to startup our app, Timer to fire alarms, Read to sense the environment. Everything
	* else is used to send / receive information over the network */
	uses {
		interface Boot;			/* This is needed to boot up the system */
		interface Timer<TMilli>;	/* Required interface for timer alarms and getting the time of a reading */

		/* Each node is equipped with two sensors: a temperature and a moisture sensor.
		* In our example, moisture is variable X and temperature is variable Y */
		interface Read<uint16_t> as ThermalSensor;

		/* Those interfaces are necessary for communication */
		interface AMSend;
		interface Receive;
		interface SplitControl as AMControl;
		interface Packet;

		/* To create a random sample from the input data */
		interface Random;
	}
}

implementation{

	/********************************************************************************
	* 			VARIABLES SPECIFICALLY TIED TO D3			*
	*********************************************************************************/

	const float sqrt5 = 2.236;	/* The square root of 5. Used in Scott's rule, for computing the bandwidth */

	/* These two variables are not required given that we m */
	uint16_t lastTuple[DIMS];	/* This is the latest tuple that was read */

	uint32_t windowSize;

	/* Variables necessary to compute the sample size */
	float sum_x[DIMS];
	float sum_xx[DIMS];

	/* Values related to clock */
	uint32_t clock;
	uint16_t oldestTupleIdx;
	uint32_t epochStartTime = 0;

	/* The current sample size and the corresponding sample */
	uint16_t sampleSize;
	bool used[SAMPLE_SIZE];
	float sample[SAMPLE_SIZE][DIMS];
	uint32_t sampleTimes[SAMPLE_SIZE];

	/* Dimensionality index. Shows which array to use next */
	uint8_t dimIdx;

	/************************************************************************
	*			VARIABLES USED TO COMMUNICATE WITH ONE ANOTHER				* 
	 ************************************************************************/
	/* The id of the parent node of this mote */
	uint8_t parentId = PARENT_NODE_ID;

	/* It may be better to have one packet for receiving messages and one for outgoing */
	message_t packet;
	radio_count_msg_t lclPayload;	/* local copy of what will be sent */

	/****************************************************************************************
	* 		CUSTOM COMMAND DECLARATION. Both Components and Tasks			*
	*****************************************************************************************/
	uint16_t randomInt(uint16_t n);		/* Returns a new random int number */
	double IFEpanech(double x);	/* Returns the Integral of the Epanechnikov value of number x */
	double IEpanech(float* newPnt, float* smpPnt);

	/* Task declaration to sense the environment */
	task void senseEnvironment();

	/* This method is used to update the standard deviation with the latest point that will be added */
	void updateStandardDeviation(float* normTuple);

	/* This method checks whether the given tuple is an outlier or not */
	bool isOutlier( float* tuple );

	/* This method is used to send the new point to the parent as an outlier */
	void sendOutlier( float* tuple );

	/* Clears the sample from all of the tuples that should be evicted
	 (actually there is only one such tuple each time the function is called) */
	void evictFromSample();

	void replaceInSample( int16_t position );

	/* Finds the next oldest tuple after the current oldest tuple. The new tuple
	* will be used for eviction in subsequent items */
	void findNextOldestTuple();

	/** Returns the index of the next tuple that should be evicted */
	uint16_t selectTupleToEvict();

	/* Returns whether the tuple should be inserted or not */
	bool shouldInsert();

	/* Add the given set of readings (i.e. tuple) in the idx-th position of the sample */
	void addTuple( float* tuple, uint16_t idx);

	uint16_t vicinityCount( float* newPnt );

	double computePointMass(float* point);

	/* Updates the model with the given tuple. The tuple is not normalized */
	task void updateModel( );

	float getVariance( uint8_t idx );
	void updateVarianceEstimation( float* prevTpl, float* curTpl );

	/* Waste CPU cycles, to be able to print after that */
	#if DEBUG
	void printTuple( float* values );

	uint16_t wasteCPU(){
		uint32_t val = 0;

		for ( i = 0; i < 20; i++ )
			val += i;
		i = val / 2;
		val = (i * 5) >> 3;
		return (uint16_t)(val + i);
	}

	/* Prints the readings from a tuple */
	void printTuple( float* values ){

		uint8_t dimItr;

		printStr("VALUES");
		wasteCPU();

		for ( dimItr = 0; dimItr < DIMS; dimItr++ ){

			printFloat( values[dimItr] );
			wasteCPU();
		}
	}

	#endif


	/****************************************************************************************
	* 		From this point on, we have the methods that will be called		*
	*****************************************************************************************/

 	/* Event fired once the application is started */
	event void Boot.booted() {

		/* The lclPayload is always sent by this ID, so we can simply use the TOS_NODE_ID */
		lclPayload.id = TOS_NODE_ID;
		sampleSize = 0;
		oldestTupleIdx = 0;
		memset(used, 0, sizeof(bool) * SAMPLE_SIZE);

		/* If the message size is too big for the payload, we just ignore it */
		if ( sizeof(radio_count_msg_t) > call AMSend.maxPayloadLength() )
			printInt16(RADIO_MSG_TOO_LARGE);

		/* Initialize the radio controller of this mote */
		if (call AMControl.start() != SUCCESS)
			printInt16(AM_CONTROL_NOT_STARTED);
	}

	/* 
	* WHY DO I NEED TO START THE AM Controler? WHAT IS THE AMControl???
	* ANS: The AMController is required to start / stop the radio transmitter.
	*
	* When the AMControl has started (the radio is ready for use) , I need to
	* start a timer, and anything else I was doing in the booted() method earlier. */
	event void AMControl.startDone(error_t err) {

		/* If the AMControl was started successfully, we simply need to begin sensing */
		if (err == SUCCESS){

			#ifndef IS_ROOT
			//In case the mote is the ROOT of the tree, we do nothing
			call Timer.startOneShot(1);
			#endif
		}else
			call AMControl.start();
	}

	/* Event occuring when the AM controller is requested to stop */
	event void AMControl.stopDone(error_t err) {}


	/* Method invoked when the timer event fires. The action we take depends on whether we 
	* want to print staff or do something else. */
	event void Timer.fired(){

		/* Log the time when the sensing cycle began */
		epochStartTime = call Timer.getNow();

		/* Start sensing */
		dimIdx = 0;
		post senseEnvironment();
	}

	/* D3 is an outlier detection algorithm, therefore, sensing and sending are by definition decoupled
	* tasks. Every time the senseEnvironment() task runs, we want to proceed with the next bfrCntr item
	* as this is where the new value will be stored.
	*
	* FIXME: Perhaps we should eliminate any items from the sample that are invalid here.
	* TODO: Find an efficient way to eliminate items here, without checking every time! */
	task void senseEnvironment(){

		/* If all of the dimensions have been read */
		if ( dimIdx == DIMS ){

			post updateModel();
			return;
		}

		if ( dimIdx == 0 ){

			/* This is the first time that the environment is sensed.
			* Start by reading the first dimension, and call ThermalSensor */
			call ThermalSensor.read();
			return;
		} 
	}


	/* Method invoked after a Read operation has finished */
	event void ThermalSensor.readDone(error_t result, uint16_t data) {
				//Ixent added this for SenseBench
	      char dbg_msg[30];
    	  sprintf(dbg_msg, "ACQUIRE(id=%d,n=%d,m=%d,d=%d)",TOS_NODE_ID, 0, 0, data);
    	  printStr(dbg_msg);


		/* If the read operation completed successfully, do what we need */
		if (result == SUCCESS){

			/* Each node calls the read operation only after it has received data from its
			* children. Therefore, the node performs a number of consecutive read operations,
			* until the buffer of readings has been filled. At that point, the read values
			* are returned to the parent.*/

			#if DEBUG
			printInt16( data );
			#endif

			/* Record the sensed value and log the time of occurence. The data read is for
			* the same reading as before, but for another dimension. We have retrieved data
			* from all dimensions, so we only need to go to the new tuple */
			lastTuple[dimIdx] = data;
			dimIdx++;

			/* Try sensing the environment again */
			post senseEnvironment();
		}else{
			printInt8(TEMPR_SENSOR_READ_ERROR);
		}
	}

	/* This method is used to update the D3 model. The D3 model runs the basic
	* task of identifying the outliers */
	task void updateModel( ){

		uint8_t i = 0;	/* a simple iterator */
		uint32_t curTm;	/* an indication of the current time */
		int32_t remaining;	/* remaining time until we sense the next batch */
		float normT[DIMS];	/* here we store the normalized values */

		/* Normalize the values so that they are in the range [0,1] as they should */
		for ( i = 0; i < DIMS; i++ )
			normT[i] = (float)(lastTuple[i] - MIN_VAL) / (float)(MAX_VAL - MIN_VAL);

		/* Unless we have reached the maximum window size, the window can expand */
	        if ( windowSize < MAX_WINDOW_SIZE )
	            ++windowSize;

		/* First of all, remove from the sample any tuple that its time has elapsed */
		evictFromSample();

		if ( shouldInsert() ){

			/* Should the current tuple be eligible for insertion, we find the index
			* where it will be placed and add it there */
			uint16_t idx = selectTupleToEvict();
			addTuple( normT, idx );
		}		

		if ( isOutlier( normT ) ){

			//Need to send this tuple to the parent as an outlier
			sendOutlier( normT );
		}

		clock++;

		curTm = call Timer.getNow();
		remaining = SAMPLING_FREQUENCY + epochStartTime - curTm;
		if ( remaining <= 0 )
			remaining = 1;
		call Timer.startOneShot(remaining);
	}

	/* Removes from the sample any tuples whose timing has elapsed */
	void evictFromSample(){

		bool wasUsed;
		float replTpl[DIMS];

		/* If we can not evict the oldest tuple, 
		* then no other tuple can either be evicted. Exit the loop */
		if ( clock - sampleTimes[oldestTupleIdx] < MAX_WINDOW_SIZE )
			return;

		/* Else, copy the tuple that will be replaced */
		memcpy( replTpl, sample + oldestTupleIdx, sizeof(float) * DIMS);
		wasUsed = used[oldestTupleIdx];

		/* Replace in the sample the item at position oldestTupleIdx. If the position
		* is occupied, the previous point is evicted. Otherwise, the point is just replaced */
		replaceInSample( oldestTupleIdx );

		/* If the position was used before being replaced, we need to update the variance */
		if ( wasUsed )
			updateVarianceEstimation( replTpl, NULL );

		findNextOldestTuple();
	}

	/** Replaces the item in the given position with the last item
	* that is in the sample and is not null */
	void replaceInSample( int16_t position ){

		if ( sampleSize <= 0 )
			return;

		/* Since we remove the item at position, we replace it with the last
		* item in the sample, so that we can handle it more efficiently */
		sampleSize--;
		if ( used[sampleSize] && (sampleSize != position) ){
			memcpy( sample + position, sample + sampleSize, sizeof(float) * DIMS);
			sampleTimes[position] = sampleTimes[sampleSize];
			used[position] = TRUE;
		}

		sampleTimes[sampleSize] = 0;
		used[sampleSize] = FALSE;
	}


	void findNextOldestTuple(){

		uint16_t i = 1;

		/* Now find the newest tuple with the lowest arrival time. This will
		* be the next best one to evict from the sample */
		oldestTupleIdx = 0;
		for ( i = 1; i < sampleSize; i++ )
			if ( sampleTimes[i] < sampleTimes[oldestTupleIdx] )
				oldestTupleIdx = i;
	}

	/* Whether the tuple should be inserted in the sample */
	bool shouldInsert(){

		/* Check if we will include the point in the random sample. Use 8 bits, to better control what is happening.
		* FIXME: Maybe, we should revert to 16 bits later */
		uint16_t randVal;
		uint16_t maxRand = 0xFFFF;

		randVal = call Random.rand16() & maxRand;

		return ( ((float) randVal / (float) maxRand) <= SAMPLE_PRCNT );
	}


	/** Returns the next tuple that should be evicted */
	uint16_t selectTupleToEvict() {

		/* If not all of the positions in the sample have been filled,
		* we will "replace" the last position in the sample */
		if ( sampleSize < SAMPLE_SIZE )
			return sampleSize;
		return randomInt( sampleSize );
	}


	void addTuple(float* t, uint16_t idx) {

		/* Update the variance estimation of the model, with the values from
		the previous and the new values */
		if ( used[idx] )
			updateVarianceEstimation( sample[idx], t );
		else{
			/* The position was not used, which means that not only do we update
			with a NULL value for the first argument, but also increase the sample! */
			updateVarianceEstimation( NULL, t );
			sampleSize++;
		}

		/* Store the given value and the timestamp that we encountered the tuple */
		memcpy(sample + idx, t, sizeof(float) * DIMS);
		sampleTimes[idx] = clock;
		used[idx] = TRUE;

		/* Find the oldest tuple after insertion, because we could have evicted it */
		findNextOldestTuple();
	}

	/* Checks if the point found at position bfrCntr is an outlier or not. According to the algorithm,
	* we need to compute the number of points that are expected in the vicinity of that point. In
	* particular we must compute the quantity:
	*
	*				N(p, r) = P[p-r, p+r] x |W|
	*
	* @param newPnt: The coordinates of the tuple which we want to check whether it is an outlier or not
	* */
	bool isOutlier( float* newPnt ) {

		uint16_t vicCnt;
     
        vicCnt = vicinityCount( newPnt );
        return vicCnt < OUTLIER_THRESHOLD;
    }

    uint16_t vicinityCount( float* newPnt ) {

		double pntMass;

        if ( sampleSize == 0 )
            return 0;

        pntMass = computePointMass( newPnt );
        return (uint16_t)ceil(windowSize * pntMass / (double)sampleSize);
    }

    /** Returns the value of bandwidth according to Scott's rule
     * (as was the case in the paper) */
    double scottsRule( int16_t idx ) {
		return sqrt5 * getVariance( idx ) * pow( sampleSize, -1.0 / (float) (DIMS + 4) );
    }

	/** Computes the point mass around the given point */
	double computePointMass(float* point) {

		int16_t i = 0;
	        double sum = 0.0;

		for ( ; i < sampleSize; i++) {

			/* Instead of doing a double loop, we compute the integral at once,
			* since it can be independently computed for each dimension */
			sum += IEpanech(point, sample[i]);
		}

		return sum;
	}


    double IEpanech(float* newPnt, float* smpPnt){

		int8_t i = 0;
        double product = 1.0;

        for ( ; i < DIMS; i++ ){

            double band = scottsRule( i );
            double stretch = band + RANGE;

            double pCoord = newPnt[i];
            double sampleCoord = smpPnt[i];

            if ( sampleCoord < pCoord - stretch)
                return 0.0;

            if ( sampleCoord > pCoord + stretch)
                return 0.0;

            if ( (sampleCoord >= band) && sampleCoord <= (1 - band) ){

                continue;

            }else if ( (sampleCoord >= - band) &&
                    (sampleCoord < band) && (sampleCoord < (1 - band)) ){

                product = product * ( 0.5 - IFEpanech( (-sampleCoord) / band) );

            }else if ( sampleCoord > (1 - band) && (sampleCoord < 1 + band) &&
                    (sampleCoord > band) ){

                product = product * ( 0.5 + IFEpanech( (1-sampleCoord) / band) );

            }else if ( (sampleCoord > -band) && (sampleCoord < band) &&
                    (sampleCoord > (1-band)) && (sampleCoord < (1 + band)) ) {

                product = product * (
                        IFEpanech( (1 - sampleCoord) / band ) -
                        IFEpanech( (sampleCoord) / band ));
            }else
                return 0;

        }

        return product;
    }

	/** CODE EXECUTED (APPARENTLY) WHEN A NEW MESSAGE IS SENT OVER THE NETWORK */
	event void AMSend.sendDone(message_t* bufPtr, error_t error) {

	}


	/************************************************************************************************
	* 		The following is code required for communication between motes			*
	*************************************************************************************************/

	/* CODE EXECUTED (APPARENTLY) WHEN A MESSAGE IS RECEIVED FROM THE NETWORK
	*
	* bufPtr is a pointer to the message that has just been received.
	* payload is a pointer to the actual information. It should be equal to getting the payload from the message itself
	* len is the length of the payload (data) */
	event message_t* Receive.receive(message_t* bufPtr, void* data, uint8_t len) {
		char dbg_msg[30];
		uint8_t i = 0;
				uint16_t actVal[DIMS];	/* here we store the normalized values */
		
		/* Only a parent node can receive messages in the D3 context. All received messages signify outliers
		* (at the moment) */
		#ifndef IS_ROOT
			/* Any intermediate node will simply send the reading upwards (to its parent node) */
			call AMSend.send(parentId, bufPtr, len);
		#else
		{
			/* In case this is the parent node, we output the tuple
			* (assuming the appropriate monitor is used ) */
			float outlier[DIMS];

			/* Such messages are always (and only) sent from child nodes. Get the child node id */
			radio_count_msg_t* rcm = (radio_count_msg_t*)data;

			memcpy(outlier, rcm->readings, sizeof(float) * DIMS);

			
			//Ixent added this for SenseBench
			
			/* Convert it back to an int16 */
				/* Normalize the values so that they are in the range [0,1] as they should */
				for ( ; i < DIMS; i++ )
					actVal[i] = MIN_VAL + outlier[i] * (float)(MAX_VAL - MIN_VAL);
				//printInt16( actVal[0] );

    	sprintf(dbg_msg, "DELIVER(id=%d,n=%d)",rcm->id, actVal[0]);
    	printStr(dbg_msg);
			#if DEBUG==	1
			printTuple(outlier);
			#endif
		}
		#endif

				
		/* In any case, the buffer pointer is returned */
		return bufPtr;
	}


	/****************************************************************************************
	* 				LOCALLY CREATED TASKS	 				*
	*****************************************************************************************/


	/* This method is used to send the latest received point to the parent of this node, as an outlier.
	* The parent node only expects outliers, so the application logic does not require to do much! */
	void sendOutlier( float* tuple ){

		/* Copy the new point values to the buffer that will be sent */
		memcpy( lclPayload.readings, tuple, DIMS * sizeof(float) );

		/* Copy the item to the payload of the packet that we'll send */
		memcpy( call AMSend.getPayload(&packet, sizeof(radio_count_msg_t)), &lclPayload, sizeof(radio_count_msg_t) );

		/* Send the packet to the parent */
		call AMSend.send(parentId, &packet, sizeof(radio_count_msg_t) );
	}

	/****************************************************************************************
	* 			THE FOLLOWING ARE SIMPLE, HELPER FUNCTIONS	 		*
	*****************************************************************************************/

	/** Returns the variance at the idx-th position */
	float getVariance( uint8_t idx ){

		/** There is 0 variance when there are only a few points */
        if ( sampleSize < 2 )
            return 0;

        return 
        	(float)sqrt( ((float)sum_xx[idx] - (float)(sum_x[idx] * sum_x[idx] / (float)sampleSize) ) / 
        	(float)(sampleSize - 1) );
		
	}

	/* Updates the estimation of the variance for each of the dimensions.
	* The method assumes that the prevTpl is one that has just been removed
	* from the sample, therefore its values should be removed from the variance.
	* On the other hand, the curTpl is one that has just been inserted, therefore
	* its values need to be added to the current variance for each dimension. */
	void updateVarianceEstimation( float* prevTpl, float* curTpl ){

		if ( prevTpl != NULL ){
			uint8_t i = 0;

			for ( ; i < DIMS; i++ ){
	            sum_x[i] -= prevTpl[i];
	            sum_xx[i] -= prevTpl[i] * prevTpl[i];
			}
		}
		
		if ( curTpl != NULL ){
			uint8_t i = 0;

			for ( ; i < DIMS; i++ ){
	            sum_x[i] += curTpl[i];
	            sum_xx[i] += curTpl[i] * curTpl[i];
			}
		}
	}

	/* Selects randomly an integer in the range [0, n) */
	uint16_t randomInt(uint16_t n){

		return 0;
	}

    /* the integral for the Epanechnikov function */
    double IFEpanech(double x) {
        double res;

        if ((x < -1.0) || (x > 1.0)) {
            return (0.0f);
        }

        res = 0.25 * (3.0 * x - x * x * x);

        return (res);
    }
}

