/**
* This is the implementation of the D3 distributed outlier detection algorithm.
* This is the most simplistic approach, where each node only senses its own environment,
* without belonging to a hierarchy.
*
* Though there is a root node, this is only used to receive the incoming detected outliers.
* Each node simply senses its environment, finds its outliers and sends them to the parent node.
* The root simply prints those outliers in the console output. Perhaps, a later version of this
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
*
* @date:	5 October 2013
* @revision: 	1.3
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

#include <stdio.h>
#include <stdlib.h>

#include "Timer.h"	// For use of timer
#include "Debug.h"	// For debugging purposes
#include "D3.h"

#include "CommQueue.h"


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
		interface Timer<TMilli> as Timer;	/* Required interface for timer alarms and getting the time of a reading */

		/* Each node is equipped with two sensors: a temperature and a moisture sensor.
		* In our example, moisture is variable X and temperature is variable Y */
		interface Read<uint16_t> as ThermalSensor;

		/* Those interfaces are necessary for communication */
		interface AMSend as RadioSend;
		interface Receive as RadioReceive;
		interface SplitControl as RadioControl;

		interface PacketLink;	/* For more reliable sending */
		interface PacketAcknowledgements; /* For requesting the ACK of a package */

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

	/* Current number of tuples in window and max window size */
	uint32_t windowSize;

	uint32_t startTime;

	/* Variables necessary to compute the standard deviation */
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
	message_t packet;

	/* The id of the parent node of this mote */
	uint8_t parentId = PARENT_NODE_ID;

	/* This method is used to send the new point to the parent as an outlier */
	int32_t seqNo;
	comm_queue_t* lastCommMsg;
	void task sendData();

	/****************************************************************************************
	* 		CUSTOM COMMAND DECLARATION. Both Components and Tasks			*
	*****************************************************************************************/
	float percent();
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
	void sendOutlier( uint16_t* tuple );

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

	/* Task to update the model used internally */
	task void updateModel( );

	/* Updates the model with the given tuple. The tuple has been normalized */
	void updateModelT( uint16_t* point, float* normPnt );

	float getVariance( uint8_t idx );
	void updateVarianceEstimation( float* prevTpl, float* curTpl );

	/* In the global D3 case, the root will have to do the following: Maintain an array of the indexes where all of the motes are held */
	int32_t moteSeqNo[N_NODES];

	#ifdef IS_ROOT

	bool detecting = FALSE;
	task void detect();

	/* Id of the last mote from which we received the data */
	uint16_t lastMoteId;

	/* Information regarding the mote from which we received information */
	bool moteRcv[N_NODES];

	/* The last reading for each mote */
	uint16_t moteRead[N_NODES][DIMS];
	#endif


	/* Waste CPU cycles, to be able to print after that */
	uint16_t wasteCPU(){
		uint8_t i;
		uint32_t val = 0;

		for ( i = 0; i < 20; i++ )
			val += i;
		i = val / 2;
		val = (i * 5) >> 3;
		return (uint16_t)(val + i);
	}

	/****************************************************************************************
	* 		From this point on, we have the methods that will be called		*
	*****************************************************************************************/

 	/* Event fired once the application is started */
	event void Boot.booted() {

		uint8_t i = 0;

		/* The lclPayload is always sent by this ID, so we can simply use the TOS_NODE_ID */
		sampleSize = 0;
		oldestTupleIdx = 0;
		memset(used, 0, sizeof(bool) * SAMPLE_SIZE);

		/* Initialize informatino for the communication queue. 1st tuple ever for this node,
		* there is no previous communication message */
		seqNo = 0;
		lastCommMsg = 0x0;

		for ( ; i < N_NODES; i++ )
			moteSeqNo[i] = 0;

		/* If you are the ROOT, initialize the indexes */
		#ifdef IS_ROOT
		{
			detecting = FALSE;
		}
		#endif

		/* If the message size is too big for the payload, we just ignore it */
		if ( sizeof( comm_queue_t ) > call RadioSend.maxPayloadLength() )
			printInt16(RADIO_MSG_TOO_LARGE);

		/* Initialize the radio controller of this mote */
		if (call RadioControl.start() != SUCCESS)
			printInt16(AM_CONTROL_NOT_STARTED);
	}

	/* When the AMControl has started (the radio is ready for use) , I need to
	* start a timer, and anything else I was doing in the booted() method earlier. */
	event void RadioControl.startDone(error_t err) {

		/* If the AMControl was started successfully, we simply need to begin sensing */
		if (err == SUCCESS){

			/* Start a timer for sensing nodes, provided this is not the sink node (tree root) */
			if ( TOS_NODE_ID != 0 )
				call Timer.startOneShot(1);
		}else
			call RadioControl.start();
	}

	/* Event occuring when the AM controller is requested to stop */
	event void RadioControl.stopDone(error_t err) {}


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

			uint32_t curTm;	/* an indication of the current time */
			int32_t remaining; 

			/* In the Global D3 model, we just send the data to the sink */
			sendOutlier( lastTuple );

			/* And we reschedule the next sampling */
			curTm = call Timer.getNow();
			remaining = SAMPLING_FREQUENCY + epochStartTime - curTm;
			if ( remaining <= 0 )
				remaining = 1;
			call Timer.startOneShot(remaining);

			return;
		}else{

			/* Unless we have read all dimensions of a single tuple, keep calling the thermal sensor.*/
			call ThermalSensor.read();
			return;
		}
	}


	/* Method invoked after a Read operation has finished */
	event void ThermalSensor.readDone(error_t result, uint16_t data) {

		/* If the read operation completed successfully, do what we need */
		if (result == SUCCESS){

			//Ixent added this for SenseBench
			char dbg_msg[30];
			sprintf(dbg_msg, "ACQUIRE(id=%d,n=%d,m=%d,d=%d)",TOS_NODE_ID, 0, 0, data);
			printStr(dbg_msg);

			/* Each node calls the read operation only after it has received data from its
			* children. Therefore, the node performs a number of consecutive read operations,
			* until the buffer of readings has been filled. At that point, the read values
			* are returned to the parent.*/

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


	/***************************** ***************************** *****************************/
	/***************************** FUNCTIONS 4 NTW COMMUNICATION *****************************/
	/***************************** ***************************** *****************************/

	/* This method enqueues the given tuple for sending through the network. The tuple has
	* been characterized as an outlier, and we need to send it across the network. */
	void sendOutlier( uint16_t* tuple ){

		/* Create a new item that we are going to fill in and enqueue it for sending in the network */
		comm_queue_t msg;

		/* Fill in the details of the message that we want */
		msg.id = TOS_NODE_ID;
		msg.seqNo = seqNo;
		memcpy( msg.data, tuple, DATA_SIZE );

		/* Enqueue it for sending */
		if ( enqueue( msg ) == QUEUE_SUCCESS ){
			/* Item enqueued successfully. Post the sending task */
			post sendData();
		}

		seqNo++;
	}


	/* Task that performs the actual sending of a packet from the communication queue */
	void task sendData(){

		error_t errVal;

		/* Method called for sending. If no previous message exists, dequeue one */
		if ( lastCommMsg == 0x0 )
			lastCommMsg = dequeue();

		/* The dequeued value is the actual payload (the information we care about) */
		memcpy( call RadioSend.getPayload( &packet, sizeof( comm_queue_t ) ), lastCommMsg, sizeof( comm_queue_t ) );

		/* Request synchronous acknowledgement. If we can not set that now, repost the task */
		errVal = call PacketAcknowledgements.requestAck( &packet );
		if ( errVal == EBUSY  ){
			post sendData();
			return;
		}

		/* Send the packet across the network */
		errVal = call RadioSend.send( parentId, &packet, sizeof( comm_queue_t ) );
		if ( errVal == FAIL ){

			/* Failure to send. Can't proceed */
			char dbg_msg[30];
			sprintf( dbg_msg, "NETW SND FAIL (%d)", (int)TOS_NODE_ID );
			printStr(dbg_msg);

			call RadioSend.cancel( &packet );

		}else if ( errVal != SUCCESS ){

			/* Sending did not succeed but we can retry. repost the task */
			post sendData();
		}
	}

	/** CODE EXECUTED (APPARENTLY) WHEN A NEW MESSAGE IS SENT OVER THE NETWORK */
	event void RadioSend.sendDone(message_t* bufPtr, error_t error) {

		uint8_t queueSize;
		bool resend = FALSE;

		/* Get the size of the queue */
		queueSize = queue_size();

		/* Check if we had a problem during sending */
		if ( error == EBUSY || error == ERETRY || error == ENOACK ){

			resend = TRUE;

		}else if ( error == EOFF || error == ESIZE || error == ENOMEM ){

			char dbg_msg[30];
			sprintf(dbg_msg, "NETW (%d) SVRE: %d", (int)TOS_NODE_ID, (int)error );
			printStr(dbg_msg);

		}else{

			if ( call PacketAcknowledgements.wasAcked( bufPtr ) == FALSE ){

				/* If the packet has not been acknowledged, resend it */
				resend = TRUE;

			}else{

				/* Message sent and ack'ed. Reset to NULL, so that we send another msg if needed. */
				lastCommMsg = 0x0;
	
				if ( queueSize != 0 ){
	
					/* If the last packet has been delivered (and ack'ed), but there are pending items
					in the communication queue, send these as well. Reset the latestMessage */
					resend = TRUE;
				}
			}
		}
		
		/* If we must resend, post the sendData task again */
		if ( resend == TRUE )
			post sendData();
	}


	/*
	* Event task executed when a message is received from the network.
	* In our case, received messages are forwarded up the propagation chain, until they reach
	* the sink / gateway node. No local computations are performed in this setting.
	*
	* bufPtr is a pointer to the message that has just been received.
	* payload is a pointer to the actual information. It should be equal to getting the payload from the message itself
	* len is the length of the payload (data) */
	event message_t* RadioReceive.receive(message_t* bufPtr, void* data, uint8_t len) {

		/* If the sequence number has been superceded, ignore */
		comm_queue_t* rcm = (comm_queue_t*)data;

		if ( rcm->seqNo < moteSeqNo[ rcm->id ] )
			return bufPtr;

		/* Only a parent node can receive messages in the D3 context. All received messages signify outliers
		* (at the moment) */
		#ifndef IS_ROOT
		{
			/* This is not the ROOT node. Any data received here are not destined for this node.
			* Enqueue the received message for communication up the routing tree */
			comm_queue_t msg;

			memcpy( &msg, rcm, sizeof( comm_queue_t ) );

			/* If the message has been successfully enqueued, post the sending task */
			if ( enqueue( msg ) == QUEUE_SUCCESS )
				post sendData();
		} 
		#else
		{
			/* If we already have a value from that node, skip it (useful for high-speed sending).
			* Otherwise, copy its values */
			if ( moteRcv[rcm->id] == FALSE ){

				moteRcv[rcm->id] = TRUE;
				memcpy( moteRead[rcm->id], rcm->data, DATA_SIZE );

				/* post a task to update the model that the sink node uses */
				post updateModel();
			}
		}
		#endif

		/* The next tuple we will be expecting should have a higher sequence number than the
		* one we already saw. This way, we avoid reporting duplicate values */
		moteSeqNo[ rcm->id ] = 1 + rcm->seqNo;

		/* In any case, the buffer pointer is returned */
		return bufPtr;
	}




	/* Task to update the model. Note that this is only used by the SINK node in this case */
	task void updateModel( ){

		/* Code only executed by the root node */
		#ifdef IS_ROOT

		uint8_t i = 0;

		/* If the method is already detecting, we can not proceed */
		if ( detecting )
			return;

		/* Find the first item that has been updated */
		for ( ; i < N_NODES; i++ )
			if ( moteRcv[i] == TRUE )
				break;

		/* If no such mote exists, return */
		if ( i == N_NODES )
			return;

		/* The id of the mote under consideration is the i-th one */
		lastMoteId = i;

		/* Get the tuple from that node */
		memcpy( lastTuple, moteRead[i], DATA_SIZE );

		/* Requesting to detect a value. Post a task that we want to check that tuple as an outlier */
		detecting = TRUE;
		post detect();

		/* The value of that mote can be changed */
		moteRcv[i] = FALSE;

		#endif
	}


	#ifdef IS_ROOT
	task void detect(){

		/* The lastTuple contains the values that we want to check as an outlier */
		uint8_t i;
		float normT[DIMS];

		/* Normalize the values so that they are in the range [0,1] (kernels require that) */
		for ( i = 0; i < DIMS; i++ )
			normT[i] = (float)(lastTuple[i] - MIN_VAL) / (float)(MAX_VAL - MIN_VAL);

		/* Update the global model for outlier detection */
		updateModelT( lastTuple, normT );

		/* Detecting has ended */
		detecting = FALSE;

		/* Ask to update the model again, with the next tuple */
		post updateModel();
	}
	#endif


	/* Updates the model with the provided normalized tuple */
	void updateModelT( uint16_t* point, float* normPnt ){

		/* Unless we have reached the maximum window size, the window can expand */
		if ( windowSize < MAX_WINDOW_SIZE )
		    ++windowSize;

		/* First of all, remove from the sample any tuple that its time has elapsed */
		evictFromSample();

		if ( shouldInsert() ){

			/* Should the current tuple be eligible for insertion, we find the index
			* where it will be placed and add it there */
			uint16_t idx = selectTupleToEvict();
			addTuple( normPnt, idx );
		}		

		if ( isOutlier( normPnt ) ){

			/* The following code will only be executed by the ROOT node.
			* Makes the implementation simpler. Compile errors occur otherwise, although this method
			* will never be invoked by an intermediate node. */
			#ifdef IS_ROOT

				/* The tuple is an outlier. DELIVER it */
	    		char dbg_msg[30];
				sprintf(dbg_msg, "DELIVER(id=%d,n=%d)", lastMoteId, point[0]);
				printStr(dbg_msg);

			#endif
		}
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

		/* Get a random integer value */
		float val = percent();

		/* Turn that in the random value */
		return ( val <= SAMPLE_PRCNT );
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
		}/home/lebiathan/Programming/helios/workspaces/workspace-ssg4e/dats-bob/SenseBench/output/06Oct2013-20-59-51/avroraJobs/exp1a-OD1-x9-OD-1

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


	/* Computes the number of points that are in the vicinity of the provided point.
	* The vicinity count is an estimation, based on the Kernel function. */
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

		/* Instead of doing a double loop, we compute the integral at once,
		* since it can be independently computed for each dimension */
		for ( ; i < sampleSize; i++) {
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


	/****************************************************************************************
	* 			THE FOLLOWING ARE SIMPLE, HELPER FUNCTIONS	 		*
	*****************************************************************************************/

	/** Returns the variance at the idx-th position */
	float getVariance( uint8_t idx ){

		/** There is 0 variance when there are only a few points */
        if ( sampleSize < 2 )
            return 0;

        return (float)sqrt( ((float)sum_xx[idx] - (float)(sum_x[idx] * sum_x[idx] / (float)sampleSize) ) / 
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

	/* the integral for the Epanechnikov function */
	double IFEpanech(double x) {
		double res;

		if ((x < -1.0) || (x > 1.0)) {
			return (0.0f);
		}

		res = 0.25 * (3.0 * x - x * x * x);

		return (res);
	}


	/**************************** **************************** ****************************/
	/**************************** SIMPLE HELPER MATH FUNCTIONS ****************************/
	/**************************** **************************** ****************************/

	/* Returns a randomly generated uint16_t value. */
	float percent( ){

		uint16_t maxRand = 0xFFFF;
		uint16_t randVal = randomInt( maxRand );

		return (float)((float) randVal / (float) maxRand);
	}

	/* Selects randomly an integer in the range [0, n) */
	uint16_t randomInt( uint16_t n ){

		/* Get a random uint16_t value and do modulo n */
		uint16_t randVal;
		uint16_t maxRand = 0xFFFF;

		randVal = call Random.rand16() & maxRand;

		return ( randVal % n );
	}

	/**************************** **************************** ****************************/
	/**************************** **************************** ****************************/
	/**************************** **************************** ****************************/
}

