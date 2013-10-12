import re, getopt, logging, sys, os, string, UtilLib, CSVLib, AvroraLib, networkLib, shutil
import SNEEMediator, SBLib, equivRuns, Node, LRMediator

optScenarioDir = os.getcwd() + os.sep + "scenarios"
optElfDir = os.getcwd() + os.sep + "sources" + os.sep + "LR" + os.sep + "elfs"
optExprList = ["1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b", "5a", "5b", "6a", "6b", "7"]
optNumInstances = 2
optSkipEquivRuns = True
optSourceRootDir = os.getcwd() + os.sep + "sources" + os.sep + "LR" + os.sep + "source"


def parseArgs(args):	
	global optScenarioDir, optElfDir, optExprList, optNumInstances, optUseCondor
	try:
		optNames = ["scenario-dir=", "elfdir=", "exp=", "num-instances=", "skip-equiv-runs=", "sourceRootDir="]
	
		#append the result of getOpNames to all the libraries 
		optNames = UtilLib.removeDuplicates(optNames)
		
		opts, args = getopt.getopt(args, "h",optNames)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
			
	for o, a in opts:
		if (o == "--scenario-dir"):
			optScenarioDir = a
		elif (o == "--elfdir"):
			optElfDir = a
		elif (o == "--exp"):
			optExprList = a.split(',')
		elif (o == "--num-instances"):
			optNumInstances = int(a)	
		elif (o == "--skip-equiv-runs"):
			optSkipEquivRuns = bool(a)
		elif (o == "--sourceRootDir"):
			optSourceRootDir = a
		else:
			usage()
			sys.exit(2)


def usage():
		print "runExp.py --scenario-dir=<dir>\n\t\tdefault="+optScenarioDir
		print "\t--elfdir=<dir>\n\t\tdefault="+optElfDir
		print "\t--exp=[1a,1b,2a,2b,3a,3b,4a,4b,5a,5b,6a,6b,7]\n\t\tdefault="+str(optExprList)
		print "\t--num-instances=<int>\n\t\tdefault="+str(optNumInstances)
		print "\t--skip-equiv-runs=<boolean>\n\t\tdefault="+str(optSkipEquivRuns)
		print "\t--sourceRootDir=<dir>\n\t\tdefault="+str(optSourceRootDir)

def initRunAttr(exprAttr, x, xValLabel, xValAttr, instance, plat, task):
	runAttr = exprAttr.copy()
	runAttr["Platform"] = plat
	#set fixed parameters for the experiments
	runAttr["PhysicalSchema"] = runAttr["PhysicalSchemas"] 
	runAttr["RadioLossRate"] = runAttr["RadioLossRates"]
	runAttr["AcquisitionRate"] = runAttr["AcquisitionRates"]
	#overwrite variable param
	runAttr[xValAttr] = x
	runAttr["xvalLabel"] = xValLabel
	runAttr["Instance"] = instance
	obtainNetworkTopologyAttributes(runAttr)
	runAttr["Task"] = task
	return runAttr

def obtainNetworkTopologyAttributes(runAttr):
	physicalSchemaName = runAttr['PhysicalSchema']

        #get the network attributes from topology file name
	m = re.search("n(\d+)_(linear|grid|random)_d(\d+)_s(\d+)", physicalSchemaName)
	if (m != None):
		runAttr['NetworkSize'] = int(m.group(1))
		runAttr['Layout'] = m.group(2)
		runAttr['NetworkDensity'] = int(m.group(3))
		#making all schemas work with 100% soruces as LR cannot distinquish betwen sources.
		runAttr['NetworkPercentSources'] = 100
		runAttr['PhysicalSchemaFilename'] = networkLib.getPhysicalSchemaFilename(runAttr['NetworkSize'],runAttr['Layout'],runAttr['NetworkDensity'],runAttr['NetworkPercentSources'],runAttr['Instance'])
		(runAttr['SNEETopologyFilename'],runAttr['AvroraTopologyFilename']) = networkLib.getTopologyFilenames(runAttr['NetworkSize'],runAttr['Layout'],runAttr['NetworkDensity'],runAttr['Instance'])
	else:
		print "ERROR: physical schema filename %s does not conform to standard format" % (physicalSchemaName)
		sys.exit(2)

def generateElfs(optElfDir):
	print "creating dir: "+optElfDir + " if not already created"
	if not os.path.exists(optElfDir):
		os.makedirs(optElfDir)
	else:
		shutil.rmtree(optElfDir)

	colNames = None
	first = True

	for line in open("experiments.csv", 'r'):
		print "runExperiments"
		if first:
			exprAttrCols = CSVLib.colNameList(line)
			exprAttrCols += ["TimeStamp"]
			first = False
			continue

		exprAttr = CSVLib.line2Dict(line, exprAttrCols)

		if not str(exprAttr['Experiment']) in optExprList:
			continue


		#Experiment,X,Y,Tasks,Xlabels,Network,RadioLossRate,AcquisitionRate
		generateElfsForExperimentalSetup(exprAttr, exprAttrCols)

def generateElfsForExperimentalSetup(exprAttr, exprAttrCols):
	print "generating elfs"
	runAttrCols = exprAttrCols + ["AcquisitionRate", "BufferingFactor", "Platform", "Task", "xvalLabel", "Instance", "ExitCode", "PhysicalSchema", "NetworkSize", "Layout", "NetworkDensity","NetworkPercentSources", "SimulationDuration", "Tuple Acq Count", "Tuple Del Count", "Tuple Delta Sum", "Data Freshness", "Output Rate", "Delivery Rate", "Sum Energy", "Sum Energy 6M", "Max Energy", "Average Energy", "CPU Energy", "Sensor Energy", "Other Energy", "Network Lifetime secs", "Network Lifetime days", "Comments", "Equiv Run"]

	tasks = exprAttr["Tasks"].split(";")
	xValAttr = exprAttr["XvalAttr"]
	xVals = exprAttr[xValAttr+"s"].split(";")
	xValLabels = exprAttr["XvalLabels"].split(";")

	for task in tasks:

		#If the task is not supported, skip it
		if (not LRMediator.taskSupported( task )):
				continue;

		for (xVal,xValLabel) in zip(xVals,xValLabels):
			for instance in range(1,optNumInstances+1):
				exprAttr["Instance"] = instance
				print "\n**********Experiment="+exprAttr['Experiment']+ " task="+task+" x="+xVal + " xLabel="+xValLabel+" instance="+str(exprAttr["Instance"])	



				runAttr = initRunAttr(exprAttr, xVal, xValLabel, xValAttr, instance, "LR", task)
				runOutputDir = SBLib.getRunOutputDir(runAttr)
				#Does not create an Avrora Job if there is another run that produces
				#equivalent results to this one
				if ((runAttr['Experiment'],"LR") in equivRuns.dict and optSkipEquivRuns):
					runAttr['Equiv Run'] = equivRuns.dict[(runAttr['Experiment'],"LR")]
					SBLib.logResultsToFiles(runAttr, runAttrCols, optOutputDir, "runs")
					continue
					
				generateElf(task,xVal,xValLabel,xValAttr,instance,runAttr,runAttrCols, runOutputDir)



def generateElf(task,xVal,xValLabel,xValAttr,instance,runAttr,runAttrCols, runOutputDir):
	SNEEMediator.init(optScenarioDir)
	elfOutputFolder = optElfDir + os.sep + runOutputDir
	#make elf output folder
	os.makedirs(elfOutputFolder)
	runAttr["CodeGenerationTarget"] = "null"
	SNEEMediator.generateAvroraJob(task,xVal,xValLabel,xValAttr,instance,runAttr,runAttrCols, optElfDir, runOutputDir, None)
	#generate header files from snee RT
	uniqueNodes = generateNodeHeaderFiles(SNEEMediator.defineTempSneeFilesRootDir(), elfOutputFolder, runOutputDir, runAttr)
	generateSettingFiles(elfOutputFolder, runAttr)
  #copy source files from LR source folder
	copyCorrectDataFilesFromStore(elfOutputFolder)

	#Copy top file for avrora
	avroraTopFile = optScenarioDir + os.sep + runAttr['AvroraTopologyFilename']
	shutil.copy(avroraTopFile, elfOutputFolder)
	
	#compile bineries for LR
	compileBineries(elfOutputFolder, runAttr, uniqueNodes)


def compileBineries(elfOutputFolder, runAttr, uniqueNodes):
	numberOfNodesInDeployment = runAttr['NetworkSize']
	for nodeindex in range(0,len(uniqueNodes)):
		shutil.copy(elfOutputFolder+os.sep+"LRNode"+str(uniqueNodes[nodeindex])+".h", elfOutputFolder+os.sep+"LR_Naive.h");
		commandStr = "cd %s \n SENSORBOARD=mts300 make micaz; \n " % (elfOutputFolder)
		exitVal = os.system(commandStr)
		if exitVal!=0:
			print "something failed during make micaz"
		shutil.copy(elfOutputFolder+os.sep+"build"+os.sep+"micaz"+os.sep+"main.exe", elfOutputFolder+os.sep+"mote"+str(uniqueNodes[nodeindex])+".elf");
		shutil.rmtree(elfOutputFolder+os.sep+"build")
	#do root node
	shutil.copy(elfOutputFolder+os.sep+"LRRoot.h", elfOutputFolder+os.sep+"LR_Naive.h");
	commandStr = "cd %s \n SENSORBOARD=mts300 make micaz; \n " % (elfOutputFolder)
	exitVal = os.system(commandStr)
	if exitVal!=0:
		print "something failed during make micaz"
	shutil.copy(elfOutputFolder+os.sep+"build"+os.sep+"micaz"+os.sep+"main.exe", elfOutputFolder+os.sep+"mote0.elf");
	shutil.rmtree(elfOutputFolder+os.sep+"build")
	#do leaf node
	shutil.copy(elfOutputFolder+os.sep+"LRLeaf.h", elfOutputFolder+os.sep+"LR_Naive.h");
	commandStr = "cd %s \n SENSORBOARD=mts300 make micaz; \n " % (elfOutputFolder)
	exitVal = os.system(commandStr)
	if exitVal!=0:
		print "something failed during make micaz"
	shutil.copy(elfOutputFolder+os.sep+"build"+os.sep+"micaz"+os.sep+"main.exe", elfOutputFolder+os.sep+"leaf.elf");
	shutil.rmtree(elfOutputFolder+os.sep+"build")


def copySensorReadingsFolder(elfOutputFolder, runAttr):
	numberOfNodesInDeployment = runAttr['NetworkSize']
	#uses the first 19 reading files then cycles around to rectify the issue on data files.
	for nodeid in range(1,numberOfNodesInDeployment):
		textFileid = nodeid
		while(textFileid > 19):
			textFileid= textFileid - 19
		shutil.copy(optSourceRootDir+os.sep+"data"+os.sep+"temper"+str(textFileid)+".txt", elfOutputFolder+os.sep+"temper"+str(nodeid)+".txt");

def generateSettingFiles(elfOutputFolder, runAttr):
	outputFile = open(elfOutputFolder+os.sep+"LR_NaiveGen.h", "w")
	outputFile.write('''/* This is the header file with default configuration material
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

#define NUM_TUPLES 10			// the number of tuples that we are going to use
#define SAMPLING_FREQUENCY %s		// sampling frequency in milliseconds
#define WINDOW_SIZE (SAMPLING_FREQUENCY * NUM_TUPLES)		//The size of the window for the query
#define SLIDE_SIZE (SAMPLING_FREQUENCY)		//How much the window slides for the new set of tuples

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
	AM_RADIO_COUNT_MSG = 0x93,
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
''' % (int(runAttr["AcquisitionRate"])*1000))
# * 1000 to convert between seconds to microseconds, as the setup file needs to be in microseconds
	outputFile.close()




def generateNodeHeaderFiles(tempSneeFolder, elfOutputFolder, experiemntNameFolder, runAttr):
	shutil.copy(tempSneeFolder+"query-plan"+os.sep+"query1-RT-1.dot", elfOutputFolder+os.sep+"rt")
	rtFile = open(elfOutputFolder+os.sep+"rt", "r") 
	numberOfNodesInDeployment = runAttr['NetworkSize']
	nodes = []
	for i in range(0,numberOfNodesInDeployment):
		x = Node.Node(i)
		nodes.append(x)

	for line in rtFile:
		if(len(line.split(">")) ==2):
			bits = line.split("\"")
			child = bits[1]
			parent = bits[3]
			x = nodes[int(parent)]
			x.appendChild(int(child))

	noLeafs = 0
	uniqueNodes = []
	for node in range(1,len(nodes)):
		childrenOfNode = nodes[node].getChildren()
		if(len(childrenOfNode) == 0):
			noLeafs = noLeafs +1
		else:
			uniqueNodes.append(node)
			outputFile = open(elfOutputFolder+os.sep+"LRNode"+str(node)+".h", "w")
			childrenString = makeChildrenString(childrenOfNode)
			outputFile.write('''/* This is the header file with default configuration material 
* for all of the motes. All motes are synchronized at the moment.
 *
 *
 * @date:	24 July 2011
 * @revision: 	1.2
 * @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
 * 		National and Kapodistrian University of Athens,
 * 		Dept. Informatics & Telecommunications
 *		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
 */

 /* Include the generic configuration of motes */
#include "LR_NaiveGen.h"


#ifndef LR_NODE%s_H
#define LR_NODE%s_H

/* This defines the children nodes of this node */
#define MY_NEIGHBORS {%s}
#define NEIGHBOR_COUNT sizeof(childNodes)/sizeof(uint8_t)
#endif
''' % (node, node, childrenString))
			outputFile.close()


	#dealing with root node. Root node is node 0
	childrenOfNode = nodes[0].getChildren()
	childrenString = makeChildrenString(childrenOfNode)
	outputFile = open(elfOutputFolder+os.sep+"LRRoot.h", "w")
	outputFile.write('''/* This is the header file with default configuration material 
* for all of the motes. All motes are synchronized at the moment.
 *
 *
 * @date:	24 July 2011
 * @revision: 	1.2
 * @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
 * 		National and Kapodistrian University of Athens,
 * 		Dept. Informatics & Telecommunications
 *		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
 */

 /* Include the generic configuration of motes */
#include "LR_NaiveGen.h"


#ifndef LR_ROOT_H
#define LR_ROOT_H

#define IS_ROOT

/* This defines the children nodes of this node */
#define MY_NEIGHBORS {%s}
#define NEIGHBOR_COUNT sizeof(childNodes)/sizeof(uint8_t)
#endif
''' % (childrenString))
	outputFile.close()

	#deal with leaf node definition
	outputFile = open(elfOutputFolder+os.sep+"LRLeaf.h", "w")
	outputFile.write('''/* This is the header file with default configuration material
* for a LEAF node. Leaf nodes are such that they do not have any children
* to contact. This means that the MY_NEIGHBORS array will be empty. It
* also means that they act as sensing nodes only and do not take any
* other action. They also perceive the role of a SENDING mote (older
* configuration.
 *
 *
 * @date:	24 July 2011
 * @revision: 	1.2
 * @author: 	George Valkanas ( http://www.di.uoa.gr/~gvalk , gvalk@di.uoa.gr )
 * 		National and Kapodistrian University of Athens,
 * 		Dept. Informatics & Telecommunications
 *		Knowledge Data Discovery Group ( http://kddlab.di.uoa.gr )
 */

 /* Include the generic configuration of motes */
#include "LR_NaiveGen.h"


#ifndef LR_LEAF_H
#define LR_LEAF_H

/* This defines the children nodes of this node */
#define MY_NEIGHBORS {}
#define NEIGHBOR_COUNT sizeof(childNodes)/sizeof(uint8_t)
#endif''')
	outputFile.close()
	#record how many are leaves for the mediator
	outputFile = open(elfOutputFolder+os.sep+"NOLEAFS", "w")
	outputFile.write(str(noLeafs))
	outputFile.close()
	outputFile = open(elfOutputFolder+os.sep+"UniqueNodes", "w")
	outputFile.write(str(uniqueNodes))
	outputFile.close()
	return uniqueNodes

#takes the array of children and turns them into a string format
def makeChildrenString(childrenArray):
	if(len(childrenArray) == 1):
		return str(childrenArray[0])
	else:
		output = ""
		first = True
		for childIndex in range(0,len(childrenArray)):
			output = output + str(childrenArray[childIndex]) + ", "
		return output[:-2]


def copyCorrectDataFilesFromStore(runOutputDir):
	shutil.copy(optSourceRootDir+os.sep+"LR_LCAppC.nc", runOutputDir)
	shutil.copy(optSourceRootDir+os.sep+"LR_LCC.nc", runOutputDir)
	shutil.copy(optSourceRootDir+os.sep+"Makefile", runOutputDir)
	shutil.copy(optSourceRootDir+os.sep+"AvroraPrint.h", runOutputDir)
	shutil.copy(optSourceRootDir+os.sep+"LRDebug.h", runOutputDir)


def main(): 	
	global optScenarioDir, optElfDir, optUseCondor

	#parse the command-line arguments
	parseArgs(sys.argv[1:]) 

	generateElfs(optElfDir)

	print "\n LR elfs in directory:"+optElfDir

if __name__ == "__main__":
	main()

