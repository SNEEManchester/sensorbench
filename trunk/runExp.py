#!/usr/bin/python

import re, getopt, logging, sys, os, string, UtilLib, CSVLib, AvroraLib, networkLib, shutil
import SNEEMediator, MHOSCMediator, SBLib, equivRuns

#Directory to read the scenario files from
optScenarioDir = os.getcwd() + os.sep + "scenarios"

optLabel = ""
optOutputDir = os.getenv('HOME')+os.sep+"tmp"+os.sep+"sensebench"+os.sep

#Default list of platforms to run experiments over
#optPlatList = ["MHOSC", "INSNEE"]
optPlatList = ["INSNEE"]

#Default list of experiments to be run
#optExprList = ['0a', '0b', '0c', '0d', '0e']
#optExprList = ['alphaCalib2']
optExprList = ["1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b", "5a", "5b", "6a", "6b", "7"]
#optExprList = ["1a"]

#Parameter to determine number of instances of each scenario to run
#optNumInstances = 10
optNumInstances = 2

#Flag to determine whether Avrora jobs will be executed via Condor parallel execution system
optUseCondor = True

#Flag to determine whether runs that are equivalent should be skipped
optSkipEquivRuns = True

def parseArgs(args):	
	global optScenarioDir, optOutputDir, optPlatList, optExprList, optNumInstances, optUseCondor
	try:
		optNames = ["scenario-dir=", "outputdir=", "plat=", "exp=", "num-instances=", "use-condor=", "skip-equiv-runs="]
	
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
		elif (o == "--outputdir"):
			optOutputDir = a
		elif (o == "--plat"):
			optPlatList = a.split(',')
		elif (o == "--exp"):
			optExprList = a.split(',')
		elif (o == "--num-instances"):
			optNumInstances = int(a)	
		elif (o == "--use-condor"):
			optUseCondor = bool(a)
		elif (o == "--skip-equiv-runs"):
			optSkipEquivRuns = bool(a)
		else:
			usage()
			sys.exit(2)


def usage():
		print "runExp.py --scenario-dir=<dir>\n\t\tdefault="+optScenarioDir
		print "\t--outputdir=<dir>\n\t\tdefault="+optOutputDir
		print "\t--plat=<MHOSC,INSNEE>\n\t\tdefault="+str(optPlatList)
		print "\t--exp=[1a,1b,2a,2b,3a,3b,4a,4b,5a,5b,6a,6b,7]\n\t\tdefault="+str(optExprList)
		print "\t--num-instances=<int>\n\t\tdefault="+str(optNumInstances)
		print "\t--use-condor=<bool>\n\t\tdefault="+str(optUseCondor)


#Ouput info message to screen and logger if applicable
def report(message):
 	if (logger != None):
 		logger.info (message)
 	print message


#Ouput warning message to screen and logger if applicable
def reportWarning(message):
 	if (logger != None):
 		logger.warning(message)
 	print message


#Ouput error message to screen and logger if applicable
def reportError(message):
 	if (logger != None):
 		logger.error(message)
 	print message

def startLogger(timeStamp):
	global logger
  
	logger = logging.getLogger('test')

	#create the directory if required
	if not os.path.isdir(optOutputDir):
			os.makedirs(optOutputDir)
			
	hdlr = logging.FileHandler('%s/%s-%s.log' % (optOutputDir, optLabel, timeStamp))
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)	
	logger.addHandler(hdlr) 
	logger.setLevel(logging.INFO)
	logger.info('Starting Regression Test')


def obtainNetworkTopologyAttributes(runAttr):
	physicalSchemaName = runAttr['PhysicalSchema']

        #get the network attributes from topology file name
	m = re.search("n(\d+)_(linear|grid|random)_d(\d+)_s(\d+)", physicalSchemaName)
	if (m != None):
		runAttr['NetworkSize'] = int(m.group(1))
		runAttr['Layout'] = m.group(2)
		runAttr['NetworkDensity'] = int(m.group(3))
		runAttr['NetworkPercentSources'] = int(m.group(4))
		runAttr['PhysicalSchemaFilename'] = networkLib.getPhysicalSchemaFilename(runAttr['NetworkSize'],runAttr['Layout'],runAttr['NetworkDensity'],runAttr['NetworkPercentSources'],runAttr['Instance'])
		(runAttr['SNEETopologyFilename'],runAttr['AvroraTopologyFilename']) = networkLib.getTopologyFilenames(runAttr['NetworkSize'],runAttr['Layout'],runAttr['NetworkDensity'],runAttr['Instance'])
	else:
		print "ERROR: physical schema filename %s does not conform to standard format" % (physicalSchemaName)
		sys.exit(2)


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


def generateAvroraLogfileName(runAttr):
	 return "%s-exp%s-x%s-i%s-avrora-log.txt" % (runAttr["Platform"], runAttr["Experiment"], runAttr["xvalLabel"], runAttr["Instance"])




def runExperiment(exprAttr, exprAttrCols, outputDir):
	global optPlatList, optNumInstances, optSkipEquivRuns

	print "runExperiments"
	runAttrCols = exprAttrCols + ["AcquisitionRate", "BufferingFactor", "Platform", "Task", "xvalLabel", "Instance", "ExitCode", "PhysicalSchema", "NetworkSize", "Layout", "NetworkDensity","NetworkPercentSources", "SimulationDuration", "Tuple Acq Count", "Tuple Del Count", "Tuple Delta Sum", "Data Freshness", "Output Rate", "Delivery Rate", "Sum Energy", "Sum Energy 6M", "Max Energy", "Average Energy", "CPU Energy", "Sensor Energy", "Other Energy", "Network Lifetime secs", "Network Lifetime days", "Comments", "Equiv Run"]

	tasks = exprAttr["Tasks"].split(";")
	xValAttr = exprAttr["XvalAttr"]
	xVals = exprAttr[xValAttr+"s"].split(";")
	xValLabels = exprAttr["XvalLabels"].split(";")

	for plat in optPlatList:	
		for task in tasks:
			for (xVal,xValLabel) in zip(xVals,xValLabels):
				for instance in range(1,optNumInstances+1):
					exprAttr["Instance"] = instance
					print "\n**********Experiment="+exprAttr['Experiment']+" Platform="+plat+" task="+task+" x="+xVal + " xLabel="+xValLabel+" instance="+str(exprAttr["Instance"])	
					runAttr = initRunAttr(exprAttr, xVal, xValLabel, xValAttr, instance, plat, task)
					runOutputDir = SBLib.getRunOutputDir(runAttr)
					
					#Does not create an Avrora Job if there is another run that produces
					#equivalent results to this one
					if ((runAttr['Experiment'],plat) in equivRuns.dict and optSkipEquivRuns):
						runAttr['Equiv Run'] = equivRuns.dict[(runAttr['Experiment'],plat)]
						SBLib.logResultsToFiles(runAttr, runAttrCols, optOutputDir, "runs")
						continue

					if (plat == "INSNEE"):
						SNEEMediator.generateAvroraJob(task,xVal,xValLabel,xValAttr,instance,runAttr,runAttrCols,outputDir, runOutputDir, avroraJobsRootDir)
					elif (plat == "MHOSC"):
						MHOSCMediator.generateAvroraJob(task,xVal,xValLabel,xValAttr,instance,runAttr,runAttrCols,outputDir, runOutputDir, avroraJobsRootDir)
					#TODO: OD
					#elif (plat == "OD"):
					#	ODMediator.generateAvroraJob(task,xVals,xValLabels,xValAttr,instance,runAttr,runAttrCols,outputDir, runOutputDir)
					#TODO: TinyDB
					#elif (plat == "TinyDB"):
					#	TinyDBMediator.generateAvroraJob(task,xVals,xValLabels,xValAttr,instance,runAttr,runAttrCols,outputDir, runOutputDir)
					else:
						print "Error: Platform %s not supported" % (plat)
						sys.exit(2)

					#TODO: If not using Condor, run Avrora now
					#if (not optUseCondor):
					#	runAvroraJob(runAttr, runAttrCols)

					#3 Log the (partial) results
					SBLib.logResultsToFiles(runAttr, runAttrCols, optOutputDir, "runs")
					

				
def runExperiments(timeStamp, outputDir):
	colNames = None
	first = True

	print "creating dir: "+outputDir
	os.makedirs(outputDir)

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

		exprAttr['TimeStamp']=timeStamp
		#Experiment,X,Y,Tasks,Xlabels,Network,RadioLossRate,AcquisitionRate
		runExperiment(exprAttr, exprAttrCols, outputDir)

						
def init(timeStamp):
	global avroraJobsRootDir, optOutputDir

	if (not os.path.isdir(optScenarioDir)):
		print "Scenarios directory %s not found" % (optScenarioDir)
		sys.exit(2)
	#will need to call init method for all platforms
	SNEEMediator.init(optScenarioDir)
	MHOSCMediator.init(optScenarioDir, os.getcwd()+os.sep+"MHOSC"+os.sep+"elf")

	optOutputDir += os.sep+timeStamp

	avroraJobsRootDir = optOutputDir + os.sep + "avroraJobs"


def cleanup():
	SNEEMediator.cleanup(optScenarioDir)
	MHOSCMediator.cleanup()


def main(): 	
	global optScenarioDir, optOutputDir, optUseCondor

	#parse the command-line arguments
	parseArgs(sys.argv[1:]) 

	timeStamp = UtilLib.getTimeStamp()
	startLogger(timeStamp)
	init(timeStamp)
	
	runExperiments(timeStamp, optOutputDir)

	cleanup()

	print "\nResults in directory:"+optOutputDir

if __name__ == "__main__":
	main()

