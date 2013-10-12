/*
 * Copyright (c) 2011, Technische Universitaet Berlin
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * - Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 * - Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the distribution.
 * - Neither the name of the Technische Universitaet Berlin nor the names
 *   of its contributors may be used to endorse or promote products derived
 *   from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
 * TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
 * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 * OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
 * USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
* @date:	25 February 2011
* @revision: 	1.1
* @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
* 		National and Kapodistrian University of Athens,
* 		Dept. Informatics & Telecommunications
*		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
 */

/**
 * This application is used to create a linear regression classifier. This is the naive
 * approach in creating LR.
 * 
 * @author George Valkanas
 */

#include "LR_Naive.h"

configuration LR_LCAppC {
} 

implementation { 

	/* These components are required to sense the environment */
	components LR_LCC, MainC, new TimerMilliC(), RandomC;

	#ifndef IS_ROOT
	/* Sensors to sense the environment. Only intermediate nodes need these */
	components new PhotoC() as XSensor, new PhotoC() as YSensor;
	LR_LCC.XSensor -> XSensor;
	LR_LCC.YSensor -> YSensor;
	#endif


	/* All of these are necessary for radio communication */
	components new AMSenderC(AM_RADIO_COUNT_MSG);
	components new AMReceiverC(AM_RADIO_COUNT_MSG);
	components ActiveMessageC;


	/* To begin execution */
	LR_LCC.Boot -> MainC;

	/* To fire events. Everyone has a timer in this approach, in order to sense the environment */
	LR_LCC.Timer -> TimerMilliC;

	/* To receive data from radio transmission */
	LR_LCC.Receive -> AMReceiverC;

	/* To send data over the radio */
	LR_LCC.AMSend -> AMSenderC;

	/* Don't really know the practical use of these two */
	LR_LCC.AMControl -> ActiveMessageC;
	LR_LCC.Packet -> AMSenderC;

	LR_LCC.Random->RandomC;
}
