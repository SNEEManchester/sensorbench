/* * This is the header file with default configuration for a ROOT node, that runs the D3
* distributed outlier detection algorithm. Most likely this is a basestation node.
* For more information on the D3 algorithm, see
*
*	Sharmila Subramaniam, Themis Palpanas, Dimitris Papadopoulos, Vana Kalogeraki, Dimitrios Gunopulos:
*	Online Outlier Detection in Sensor Data Using Non-Parametric Models. VLDB, 2006
*
* @date:	3 March 2011
* @revision: 	1.0
* @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
* 		National and Kapodistrian University of Athens,
* 		Dept. Informatics & Telecommunications
*		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
*/

/* Include the generic configuration of motes */
#include "D3Gen.h"

#define IS_ROOT
#define PARENT_NODE_ID 0

