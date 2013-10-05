import re, getopt, logging, sys, os, string, UtilLib, CSVLib, AvroraLib, networkLib, shutil
import SNEEMediator, SBLib, equivRuns, ODMediator

optScenarioDir = os.getcwd() + os.sep + "scenarios"
optVersion = 1
optElfDir = os.getcwd() + os.sep + "sources" + os.sep + "OD" + str(optVersion) + os.sep + "elfs"
optExprList = ["1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b", "5a", "5b", "6a", "6b", "7"]
optNumInstances = 2
optSkipEquivRuns = True
optSourceRootDir = os.getcwd() + os.sep + "sources" + os.sep + "OD" + str(optVersion) + os.sep + "source"


def parseArgs(args):	
	global optScenarioDir, optElfDir, optExprList, optNumInstances, optUseCondor, optVersion, optSourceRootDir
	try:
		optNames = ["scenario-dir=", "elfdir=", "exp=", "num-instances=", "skip-equiv-runs=", "sourceRootDir=", "ODversion="]
	
		#append the result of getOpNames to all the libraries 
		optNames = UtilLib.removeDuplicates(optNames)
		
		opts, args = getopt.getopt(args, "h",optNames)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
			
	for o, a in opts:
		print o
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
		elif (o == "--ODversion"):
			optVersion = int(a)
			optSourceRootDir = os.getcwd() + os.sep + "sources" + os.sep + "OD" + str(optVersion) + os.sep + "source"
			optElfDir = os.getcwd() + os.sep + "sources" + os.sep + "OD" + str(optVersion) + os.sep + "elfs"
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
		print "\t--ODversion=<1,2,3>\n\t\tdefault="+str(optVersion)

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
		#making all schemas work with 100% soruces as OD cannot distinquish betwen sources.
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
	global optVersion
	print "generating elfs"
	runAttrCols = exprAttrCols + ["AcquisitionRate", "BufferingFactor", "Platform", "Task", "xvalLabel", "Instance", "ExitCode", "PhysicalSchema", "NetworkSize", "Layout", "NetworkDensity","NetworkPercentSources", "SimulationDuration", "Tuple Acq Count", "Tuple Del Count", "Tuple Delta Sum", "Data Freshness", "Output Rate", "Delivery Rate", "Sum Energy", "Sum Energy 6M", "Max Energy", "Average Energy", "CPU Energy", "Sensor Energy", "Other Energy", "Network Lifetime secs", "Network Lifetime days", "Comments", "Equiv Run"]

	tasks = exprAttr["Tasks"].split(";")
	xValAttr = exprAttr["XvalAttr"]
	xVals = exprAttr[xValAttr+"s"].split(";")
	xValLabels = exprAttr["XvalLabels"].split(";")

	#
	#Addidion by lebi: ODx Platform supports only "OD" task (check the ODMediator as well).
	#

	for task in tasks:
		for (xVal,xValLabel) in zip(xVals,xValLabels):
			for instance in range(1,optNumInstances+1):

				plat = "OD" + str(optVersion);
				if (not ODMediator.taskSupported(task)):
					continue;

				exprAttr["Instance"] = instance
				print "\n**********Experiment="+exprAttr['Experiment']+ " task="+task+" x="+xVal + " xLabel="+xValLabel+" instance="+str(exprAttr["Instance"])	

				runAttr = initRunAttr(exprAttr, xVal, xValLabel, xValAttr, instance, plat, task)
				runOutputDir = SBLib.getRunOutputDir(runAttr)
				#Does not create an Avrora Job if there is another run that produces
				#equivalent results to this one
				if ((runAttr['Experiment'],"OD") in equivRuns.dict and optSkipEquivRuns):
					runAttr['Equiv Run'] = equivRuns.dict[(runAttr['Experiment'],"OD")]
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
	generateNodeHeaderFiles(SNEEMediator.defineTempSneeFilesRootDir(), elfOutputFolder, runOutputDir, runAttr)
	generateSettingFiles(elfOutputFolder, runAttr)
  #copy source files from OD source folder
	copyCorrectDataFilesFromStore(elfOutputFolder)

	#Copy top file for avrora
	avroraTopFile = optScenarioDir + os.sep + runAttr['AvroraTopologyFilename']
	shutil.copy(avroraTopFile, elfOutputFolder)

	#copy sensor reading files to soruce folder
	copySensorReadingsFolder(elfOutputFolder, runAttr)
	
	#compile bineries for OD
	compileBineries(elfOutputFolder, runAttr)


def compileBineries(elfOutputFolder, runAttr):
	numberOfNodesInDeployment = runAttr['NetworkSize']
	for nodeid in range(0,numberOfNodesInDeployment):
		shutil.copy(elfOutputFolder+os.sep+"D3Node"+str(nodeid)+".h", elfOutputFolder+os.sep+"D3.h");
		commandStr = "cd %s \n SENSORBOARD=mts300 make micaz; \n " % (elfOutputFolder)
		exitVal = os.system(commandStr)
		if exitVal!=0:
			print "something failed during make micaz"
		shutil.copy(elfOutputFolder+os.sep+"build"+os.sep+"micaz"+os.sep+"main.exe", elfOutputFolder+os.sep+"mote"+str(nodeid)+".elf");
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
	outputFile = open(elfOutputFolder+os.sep+"D3Gen.h", "w")
	outputFile.write('''/* This is the header file with default configuration material for all of the motes.
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

#define WINDOW_SIZE 10000	//The size of the window for the query
#define SLIDE_SIZE 10000	//How much the window slides for the new set of tuples
#define SAMPLING_FREQUENCY %s	// sampling frequency in milliseconds

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

#endif''' % (int(runAttr["AcquisitionRate"])*1000))
# * 1000 to convert between seconds to microseconds, as the setup file needs to be in microseconds
	outputFile.close()




def generateNodeHeaderFiles(tempSneeFolder, elfOutputFolder, experiemntNameFolder, runAttr):
	shutil.copy(tempSneeFolder+"query-plan"+os.sep+"query1-RT-1.dot", elfOutputFolder+os.sep+"rt")
	rtFile = open(elfOutputFolder+os.sep+"rt", "r") 
	for line in rtFile:
		if(len(line.split(">")) ==2):
			bits = line.split("\"")
			child = bits[1]
			parent = bits[3]
			outputFile = open(elfOutputFolder+os.sep+"D3Node"+child+".h", "w")
			outputFile.write('''/* * This is the header file with default configuration for a ROOT node, that runs the D3
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

#define PARENT_NODE_ID %s''' % (parent))
			outputFile.close()
			numberofNodesInDeployment = runAttr['NetworkSize']
			outputFile = open(elfOutputFolder+os.sep+"D3Node0.h", "w")
			outputFile.write('''/* * This is the header file with default configuration for a ROOT node, that runs the D3
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

#define PARENT_NODE_ID 0
#define N_NODES %s''' % (numberofNodesInDeployment))
			outputFile.close()

def copyCorrectDataFilesFromStore(runOutputDir):
	global optVersion
	shutil.copy(optSourceRootDir+os.sep+"D3AppC.nc", runOutputDir)
	shutil.copy(optSourceRootDir+os.sep+"D3C.nc", runOutputDir)
	shutil.copy(optSourceRootDir+os.sep+"Makefile", runOutputDir)
	shutil.copy(optSourceRootDir+os.sep+"AvroraPrint.h", runOutputDir)

	#Copy the communication queue - lebi
	shutil.copy(optSourceRootDir+os.sep+"CommQueue.h", runOutputDir)
	shutil.copy(optSourceRootDir+os.sep+"CommQueue.c", runOutputDir)
	if(optVersion ==1):
		shutil.copy(optSourceRootDir+os.sep+"Debug.h", runOutputDir)

def main(): 	
	global optScenarioDir, optElfDir, optUseCondor, optVersion

	#parse the command-line arguments
	parseArgs(sys.argv[1:]) 
	generateElfs(optElfDir)

	print "\n OD elfs in directory:"+optElfDir

if __name__ == "__main__":
	main()

