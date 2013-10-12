/* 
* This is the implementation of a Linear Regression classifier, where reading and sending are
* decoupled. Moreover, we perform local computations, instead of sending all of the queries to
* the root. This allows for the more sophisticated communication mechanism between nodes. The
* newer mechanism has not been implemented yet. However, each node computes (a,b) values locally
* and sends the result back to the parent, once all the values have been retrieved.
* This implementation works as follows:
* 	- We already assume that a tree has been built over the available sensors.
* 	- Each parent knows the id's of the children it has and that it needs to contact
*	- Using a round-robin scheme, the parent requests data from its children. Each
*	  child performs exactly the same thing, until we reach leaf nodes. The goal is
*	  for the data to reach the sink node.
*	- When a node is contacted, we inform a child to send data. After all children of a node
*	  have reported their data, we aggregate values sumX, sumY, sumXX and sumXY (and count)
*	  which are returned to the parent node.
*
* The entire communication begins from the sink node and propagates through its children.
* The sink requests data from the first child and awaits its response. Once the response
* has been received, the sink moves to the next child and requests data from it. The same
* is performed until the last child, at which point data are returned to the user and the
* loop begins again. 
*
* We do not do a broadcast, but we target specific sensors each time, through the AMSend.send()
* interface. We pass as the first argument the id that the request is intended for, and the
* protocol is responsible for the rest.
*
* We assume that the network tree is rooted at TOS_NODE_ID = 0
*
* Note that the scheme is practically sequential!
*
* @date:	23 July 2011
* @revision: 	1.4
* @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
* 		National and Kapodistrian University of Athens,
* 		Dept. Informatics & Telecommunications
*		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
*/

#include <stdio.h>
#include <stdlib.h>

#include "Timer.h"		// For use of timer
#include "LR_Naive.h"

/* For debugging purposes. Includes the AvroraPrint.h file internally */
#include "LRDebug.h"

/**
* This is an implementation of a mote that reads values and builds a Linear Regression
* classifier inside the Wireless Sensor Network.
* The safe() annotation does not do anything, as we are running TinyOS 2.0, which does
* not have this kind of support.
*/
module LR_LCC @safe() {

	/* The interfaces that this application requires. We need the following for our application:
	* Boot to startup our app, Timer to fire alarms, Read to sense the environment. Everything
	* else is used to send / receive information over the network */
	uses {
		interface Boot;			/* This is needed to boot up the system */
		interface Timer<TMilli>;	/* Required interface for timer alarms and getting the time of a reading */

		/* Each node is equipped with two sensors: a temperature and a moisture sensor.
		* In our example, moisture is variable X and temperature is variable Y */
		#ifndef IS_ROOT
		interface Read<uint16_t> as XSensor;
		interface Read<uint16_t> as YSensor;
		#endif

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

	/* The naive approach, sends everything that it reads. This can be simulated
	* by keeping a buffer of only 1 item each time, as with Naive Batch sending */
	#ifndef IS_ROOT
	bool bfrFull = FALSE;
	uint8_t bfrCntr = 0;		/* Which is the currently read value */
	uint16_t xvals[BFR_SZ];	/* Buffer where moisture values are stored */
	uint16_t yvals[BFR_SZ];	/* Buffer where temperature values are stored */
	uint32_t timesBuffer[BFR_SZ];	/* timestamps of sensing values */
	uint32_t lastReadTime = 0;		/* when was the last tuple read */

	uint16_t tmpX;	/* Temporary variable to temporarily store value X, in case data are requested prior to that */
	#endif

	/* It may be better to have one packet for receiving messages and one for outgoing */
	message_t packet;
	message_t rqPacket;

	radio_count_msg_t lclPayload;	/* local copy of what will be sent */

	uint8_t parentId = 0;		/* The id of the parent node of this mote */
	uint8_t curContact = 0;		/* The neighbor we are currently contacting */

	uint32_t lastCycleStart = 0;

	/* The number of readings that we have sent so far */
	uint8_t sentDataCntr = 0;

	/* The number of readings that this node has received from its child, so that it
	* will start requesting data from the next one */
	uint8_t readRcvd = 0;

	/* The children nodes of this node. MY_NEIGHBORS is defined in each file separately,
	* depending on the tree that we assume that is constructed. Technically, it is the
	* same tree as the minimum hop tree to the root that each node builds internally.
	* We also use a define for the neighbor count. This is easy to implement with header
	* files and scripted compilation.
	*
	* SIDE NOTE: It is not necessary to be a minimum hop tree, as some trees may be
	* longer, but the linkage between nodes is recognized as much better.
	*
	* ATTENTION: Make sure that if you change the variable name of childNodes here, to
	* change it in the header file as well!!! The reason is that the childCount is
	* computed directly by the sizeof the childNodes. */
	uint8_t childNodes[] = MY_NEIGHBORS;
	uint8_t childCount = NEIGHBOR_COUNT;

	/********************************************************************************
	* 		VARIABLES SPECIFICALLY TIED TO LINEAR REGRESSION		*
	*********************************************************************************/

	/* Note that unlike other implementations, *ALL* nodes store the four sums */
	uint32_t sumX;		/* Sum of X variable */
	uint32_t sumY;		/* Sum of Y variable */
	uint32_t sumX2;		/* Sum of X^2 (X square) */
	uint32_t sumXY;		/* Sum of X * Y */
	uint32_t count;		/* The number of received variables. this is not particularly interesting */

	/* This method is used to update the local 4 sums, necessary to compute (a,b),
	* when values are received from the network. As all nodes compute the 4 sums,
	* all of them require the following method */
	void nxFourSumsUpdate( const uint32_t* );

	/* This methos is used to update the four sums using the local buffers, where
	* information is stored */
	void updateFourSums( const uint16_t*, const uint16_t*, const uint8_t );

	#ifdef IS_ROOT
	float a, b;	/* float values where a and b are stored */

	/* This is the method to invoke when we are ready to compute a and b values */
	void computeAB( );
	#endif

	/****************************************************************************************
	* 		CUSTOM COMMAND DECLARATION. Both Components and Tasks			*
	*****************************************************************************************/
	/* Inform the next neighbor that we want it to return data */
	void task requestNextData();
//	void task sendDataToParent();
//	void task processIncomingReadings();

	/* Task declaration to sense the environment */
	#ifndef IS_ROOT

	int16_t acqEpoch = -1;
	task void readTuple();

	/* Only intermediate nodes and leaves need to send data back to their parents. Not the root */
	task void sendReadings();
	#endif

	#ifdef IS_ROOT

	int16_t delEpoch = 0;

	/* Task declaration to begin a new epoch */
	task void startNewEpoch();

	/* Only  the root computes the LR parameters (a, b) */
	task void computeLRParameters();
	/*only the root when its recieved a packet from a child can it deliver it out of network)*/
	void computeLRParametersRootRecieved(uint8_t childID);

	#endif

	void initializeData();

	uint16_t randomMaxInt();
	uint16_t randomInt( uint16_t n );


	uint16_t wasteCPU(){
		uint8_t i;
		uint32_t val = 0;

		for ( i = 0; i < 254; i++ )
			val += i;
		i = val / 2;
		val = (i * 5) >> 8;
		return (uint16_t)(val + i);
	}


	/****************************************************************************************
	* 		From this point on, we have the methods that will be called		*
	*****************************************************************************************/

 	/* Event fired once the application is started */
	event void Boot.booted() {

		/* Setting up the mote id */
		lclPayload.id = TOS_NODE_ID;

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

		/* If the AMControl was started successfully, initialize anything else */
		if (err == SUCCESS){

			call Timer.startOneShot( 1 );
		}else
			call AMControl.start();
	}

	/* Event occuring when the AM controller is requested to stop */
	event void AMControl.stopDone(error_t err) {}


	/* Method invoked when the timer event fires. The action we take depends on whether we 
	* want to print staff or do something else. */
	event void Timer.fired(){

		#ifdef IS_ROOT

			/* Everything needed during this epoch has been performed.
			* Proceed to the new epoch */
			post startNewEpoch();

		#else
			/* Methods executed by a simple sensor, not the sink when the timer fires */
			post readTuple();
		#endif


	}

	/* This method is used to start a new epoch. Internally, it initializes all variables required
	* prior to beginning a new round of requests to the sensors. */
	task void startNewEpoch(){

		initializeData();

		/* In case this is the root, we need to initialize values (a,b) as well. Moreover,
		* since a new round has started, we either need to contact the remaining children
		* nodes, or try and compute the LR parameters, if there are no other children in
		* the vicinity. Only the root will initiate a new request */
		#ifdef IS_ROOT
		if ( curContact < childCount )
			post requestNextData();
		else
			post computeLRParameters();
		#else
			/* Start a new task to sense readings from the environment.
			Only child nodes start doing so. The sink does not have sensors */
			post readTuple();

		#endif
	}


	/* This method is used by the sink to initialize its data */
	void initializeData(){

		#ifdef IS_ROOT
		/* The parent has just initiated another cycle. Log the time when this occurred */
		lastCycleStart = call Timer.getNow();

		a = b = 0.0;
		#endif

		/* Start all over again */
		sumX = sumY = sumX2 = sumXY = count = 0;

		/* Since this is a new epoch, no children have been contacted.
		* This is the same for both root and other nodes. */
		curContact = 0;
	}


	#ifndef IS_ROOT

	/* Because we have decoupled sensing from sending, sensing needs to be started in a separate task.
	* Even though we have decoupled the two actions, we want to keep the code simple, so we only allow
	* a temperature reading after a moisture reading. So, sensing the environment simply means a call
	* to reading data from the moisture sensor (X parameter) */
	/* Reads the next tuple */
	void task readTuple(){

		acqEpoch++;

		/* Does not have to do anything else other than call the method to read data */
		lastReadTime = call Timer.getNow();
		call XSensor.read();
	} 



	/* Method called when the moisture reading has been completed */
	event void XSensor.readDone(error_t result, uint16_t data) {

		data = randomInt( 1024 );

		if (result == SUCCESS){

			/* Because we want to read data in couples (moisture, temperature), once the
			* moisture reading has been retrieved and stored, we request a temperature reading */
			tmpX = data;
			call YSensor.read();

		}else{
			/* Print an error message and try to read again */
			printInt8(MOIST_SENSOR_READ_ERROR);
			call XSensor.read();
		}
	}


	/* Method invoked after a Read operation has finished */
	event void YSensor.readDone(error_t result, uint16_t data) {

		data = randomInt( 1024 );

		/* If the read operation completed successfully, do what we need */
		if (result == SUCCESS){

			long tmp;
			int32_t tmpNow;

			/* Each node calls the read operation only after it has received data from its
			* children. Therefore, the node performs a number of consecutive read operations,
			* until the buffer of readings has been filled. At that point, the read values
			* are returned to the parent.*/

			/* Record the sensed value and time of occurence */
			xvals[bfrCntr] = tmpX;
			yvals[bfrCntr] = data;
			bfrCntr++;
			if ( bfrCntr == BFR_SZ ){
				bfrFull = TRUE;
				bfrCntr = 0;
			}

			//Ixent added this for SenseBench
			{
				char dbg_msg[64];
				sprintf( dbg_msg, "ACQUIRE(id=%d,ep=%d,x=%u,y=%u)", TOS_NODE_ID, acqEpoch, tmpX, data );
				printStr( dbg_msg );
			}

			/* Set again to read the new tuple, taking into account the SAMPLING_FREQUENCY.
			Log the current time, when the tuple has been successfully read. Find how much
			time we have left until reading the next tuple. If no time is left, start reading
			the new tuple immediately (set tmpNow = 1) */
			tmp = call Timer.getNow();
			tmpNow = SAMPLING_FREQUENCY - (tmp - lastReadTime);

			/* The amount of time to read the next tuple has been computed. If it was a
			negative number, then we need to start right away */
			if ( tmpNow <= 0 )
				tmpNow = 1;
			call Timer.startOneShot( (uint32_t)tmpNow );

		}else{
			printInt8(TEMPR_SENSOR_READ_ERROR);
			call YSensor.read();
		}
	}

	#endif

	/** CODE EXECUTED (APPARENTLY) WHEN A NEW MESSAGE IS SENT OVER THE NETWORK */
	event void AMSend.sendDone(message_t* bufPtr, error_t error) {

		/* Readings are sent only by child (or intermediate nodes).
		* Once readings are sent, the node goes into a new epoch */
		//post startNewEpoch();

	}


	/* This method is used to request data from the next child node in line.
	* Appropriate / Necessary checks are assumed to have been performed prior to calling this method. */
	void task requestNextData(){

		call Packet.clear( &rqPacket );
		memcpy( call AMSend.getPayload( &rqPacket, sizeof(uint8_t) ), (uint8_t*)&lclPayload.id, sizeof(uint8_t) );
		call AMSend.send(childNodes[curContact], &rqPacket, sizeof(uint8_t) );
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

		/* Received messages may be either of two types: a request or an incoming reading */

		#ifndef IS_ROOT
		if ( len == sizeof(uint8_t) ){

			/* The message is definitely intended for this node, because request messages are sent directly,
			* based on "IP". Such a message implies that the parent node has requested readings from this
			* node. This is only intended for nodes other than the root */

			/*  The content of the message is the parent node id. Such a message means that this node should
			* begin requesting data from its children or sense the environment */
			parentId = *((uint8_t*) data);

			/* A new epoch is beginning, since the sensor was notified by its parent. Therefore, we need to
			initialize the data once again */
			initializeData();

			/* Send a request to the children of this node, provided it has any */
			if ( curContact < childCount ){
				post requestNextData();
			}else{
				/* This node does not have anyone else to contact. Send the readings to the parent node */
				post sendReadings();
			}

			return bufPtr;
		}
		#endif

		/* Case where a message with readings was received from the network. */
		if ( len == sizeof(radio_count_msg_t) ){

			/* Such messages are always (and only) sent from child nodes. Get the child node id */
			radio_count_msg_t* rcm = (radio_count_msg_t*)data;

			/* If the received message is from the child that was contacted last,
			* we need to proceed with contacting the next child */
			if ( rcm->id == childNodes[curContact] )
				curContact++;

			/* The received message is from a child node and contains readings from its
			* environment. In particular, it contains the 4 sums of that child node. We use
			* those values to update the local 4 sums, regardless of being the root or not.
			* We choose to do the updating synchronously, to use less memory.  */
			nxFourSumsUpdate( (uint32_t*)rcm->readings );

			/* After we have updated the local 4 sums, we contact the next child, if any */
			if ( curContact < childCount ){

				/* More children exist. Contact them before doing anything else */
				post requestNextData();
			}else{

				/* In case there are no other children, then the action depends on the 
				* type of the node. If it is the root, it should compute the LR parameters.
				* If it is an intermediate node, it should send all readings to the parent */
				#ifdef IS_ROOT
				computeLRParametersRootRecieved(rcm->id);
				#else
				post sendReadings();
				#endif
			}
		}

		/* In any case, the buffer pointer is returned */
		return bufPtr;
	}


	/** Given a reading from the network, we parse it (deserialize it) and get the individual values it contains.
	* We remind that the values inside a reading from the network are:
	*
	* - COUNT
	* - SumX
	* - SumY
	* - SumXY
	* - SumX2 (x^2 or x square)
	* 
	* We can use directly those values to update the local copies. */
	void nxFourSumsUpdate( const uint32_t* networkReading ){

		count += networkReading[0];	/* Read the count */
		sumX += networkReading[1];	/* Read sumX */
		sumY += networkReading[2];	/* Read sumY */
		sumXY += networkReading[3];	/* Read sumXY */
		sumX2 += networkReading[4];	/* Read sumX2 (sum of square X) */
	}

	/** Given the input variables, update the four sums that are required for linear regression.
	* bufferX contains the X (independent) values, while bufferY the Y (derived) values. cnt is the
	* number of variables that each buffer has. */
	void updateFourSums( const uint16_t* bufferX, const uint16_t* bufferY, uint8_t cnt ){
		uint8_t i = 0;

		count += cnt;
		for ( ; i < cnt; i++ ){

			uint32_t x = bufferX[i];
			uint32_t y = bufferY[i];

			sumX += x;
			sumX2 += x * x;
			sumY += y;
			sumXY += x * y;
		}
	}


	/****************************************************************************************
	* 				LOCALLY CREATED TASKS	 				*
	*****************************************************************************************/


	/** This is a task used to send readings with sensed values from the environment.
	* Perhaps, it is best to wait until all of the readings have been retrieved. Should look into that
	* The sendReadings task assembles sensed values into a message and sends them to the parent node
	* that has already requested them. */
	#ifndef IS_ROOT
	task void sendReadings(){

		uint8_t tmpCnt;

		/* If the buffer is full, then we only need the buffer counter */
		tmpCnt = ( bfrFull ) ? BFR_SZ : bfrCntr;
		updateFourSums( xvals, yvals, tmpCnt );

		/* All I'm sending is the 4 sums and the count. Copy these in the readings and send the packet.
		* The count (size) is apriori known. The order in which values are stored is:
		* - COUNT
		* - SumX
		* - SumY
		* - SumXY
		* - SumX2 (x^2 or x square)
		*/
		memcpy( lclPayload.readings, &count, sizeof(uint32_t) );
		memcpy( lclPayload.readings + sizeof(uint32_t), &sumX, sizeof(uint32_t) );
		memcpy( lclPayload.readings + (2 * sizeof(uint32_t)), &sumY, sizeof(uint32_t) );
		memcpy( lclPayload.readings + (3 * sizeof(uint32_t)), &sumXY, sizeof(uint32_t) );
		memcpy( lclPayload.readings + (4 * sizeof(uint32_t)), &sumX2, sizeof(uint32_t) );

		/* Copy the above message to the actual payload and send directly to the parent */
		call Packet.clear ( &packet );
		memcpy( call AMSend.getPayload( &packet, sizeof(radio_count_msg_t) ), &lclPayload, sizeof(radio_count_msg_t) );
		call AMSend.send( parentId, &packet, sizeof(radio_count_msg_t) );
	}
	#endif


	#ifdef IS_ROOT

	/* This task is only issued by the root node to compute (a, b) values that are required for the linear
	* regression classifier. The root needs to use its local values of temperature and moisture as well, in
	* order to compute (a, b) */
	task void computeLRParameters(){
		long tmp;
		int32_t tmpNow;

		computeAB();

		//Ixent added this for SenseBench
		{
			char dbg_msg[64];
		    sprintf(dbg_msg, "DELIVER(id=%d,ep=%d,x=%d,y=%d)", TOS_NODE_ID, delEpoch, a, b );
		   	printStr(dbg_msg);
	   	}

		delEpoch++;

		/* Log when all of this happened */
		tmp = call Timer.getNow();
		tmpNow = SLIDE_SIZE - (tmp - lastCycleStart);
		if ( tmpNow < 0 )
			tmpNow = 1;

		/* Move to the next cycle, starting after the appropriate time has elapsed */
		call Timer.startOneShot( (uint32_t)tmpNow );
	}

	/* This task is only issued by the root node to compute (a, b) values that are required for the linear
	* regression classifier. The root needs to use its local values of temperature and moisture as well, in
	* order to compute (a, b) */
	void computeLRParametersRootRecieved(uint8_t childID){
		post computeLRParameters();
	}



	/* Computes a and b from the already stored sumX, sumY, sumX2, sumXY and count */
	void computeAB( ){

		a = ( ((float)sumXY / (float)sumX) - ((float)sumY / (float)count) ) / 
			( ( (float)sumX2 / (float)sumX ) - ( (float)sumX / (float)count));
//		a = ((float)( count * sumXY - sumX * sumY )) / ((float)(count * sumX2 - sumX * sumX));
		b = ((double)sumY - a * sumX) / (float)(count);
	}

	#endif


	/* Selects randomly an integer in the range [0, n) */
	uint16_t randomMaxInt(){

		return randomInt( (uint16_t)0xFFFF );
	}

	/* Selects randomly an integer in the range [0, n) */
	uint16_t randomInt( uint16_t n ){

		/* Get a random uint16_t value and do modulo n */
		uint16_t randVal;
		uint16_t maxRand = 0xFFFF;

		randVal = call Random.rand16() & maxRand;

		return ( randVal % n );
	}

}

