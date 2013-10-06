/**
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
 *
 * @date:	3 March 2011
 * @revision: 	1.1
 * @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
 * 		National and Kapodistrian University of Athens,
 * 		Dept. Informatics & Telecommunications
 *		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
 *
 * This is the wiring file for the D3 outlier detection algorithm. For more information
 * on the algorithm, see
 *	Sharmila Subramaniam, Themis Palpanas, Dimitris Papadopoulos, Vana Kalogeraki, Dimitrios Gunopulos:
 *	Online Outlier Detection in Sensor Data Using Non-Parametric Models. VLDB, 2006
 *
*/

#include "D3.h"

#include "CommQueue.h"

configuration D3AppC {
} 

implementation { 

	/* Required for initialization */
	components MainC;

	/* These components are required to sense the environment. The timer is required for timestamping the readings */
	components new PhotoC() as Sensor, new TimerMilliC();

	/* Required to implement the D3 algorithm: The D3 component itself, a random generator and a timer */
	components D3C, RandomC;

	/* All of these are necessary for radio communication */
	components new AMSenderC(AM_RADIO_COUNT_MSG);
	components new AMReceiverC(AM_RADIO_COUNT_MSG);
	components ActiveMessageC;
	components CC2420ActiveMessageC;


	/* To begin execution */
	D3C.Boot -> MainC;

	/* To fire events. Everyone has a timer in this approach, in order to sense the environment */
	D3C.Timer -> TimerMilliC;

	/* Sensors to sense the environment. */
	D3C.ThermalSensor -> Sensor;

	/* To receive data from radio transmission */
	D3C.RadioReceive -> AMReceiverC;

	/* To send data over the radio */
	D3C.RadioSend -> AMSenderC;

	/* Don't really know the practical use of these two */
	D3C.RadioControl -> ActiveMessageC;
	D3C.Packet -> AMSenderC;

	/* For more reliable communication */
	D3C.PacketLink -> CC2420ActiveMessageC;
	D3C.PacketAcknowledgements -> AMSenderC;

	D3C.Random->RandomC;
}
