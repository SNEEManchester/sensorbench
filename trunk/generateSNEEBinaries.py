#!/usr/bin/python

import re, getopt, logging, sys, os, string, UtilLib, CSVLib, AvroraLib, networkLib, shutil
import parseAcquireDeliverTimes, equivRuns

optLabel = ""
optOutputDir = os.getenv('HOME')+os.sep+"tmp"+os.sep+"results"+os.sep

sneeRoot = os.getenv('SNEEROOT')

#optPlatList = ["MHOSC", "INSNEE"]
optPlatList = ["INSNEE"]

#optExprList = ['0a', '0b', '0c', '0d', '0e']
#optExprList = ['alphaCalib2']

optExprList = ["1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b", "5a", "5b", "6a", "6b", "7"]

tasks2queries = {"raw" : "RSTREAM SELECT * FROM seaDefence[NOW];", \
		 "aggr" : "RSTREAM SELECT AVG(seaLevel) FROM seaDefence[NOW];", \
		 "corr1" : "RSTREAM SELECT e.seaLevel, w.seaLevel FROM seaDefenceEast[NOW] e, seaDefenceWest[NOW] w WHERE e.seaLevel > w.seaLevel;", \
		 "corr2" : "RSTREAM SELECT e.seaLevel, w.seaLevel FROM seaDefenceEast[NOW] e, seaDefenceWest[FROM NOW TO NOW-1 SECOND] w WHERE e.seaLevel > w.seaLevel;", \
		 "LR" : "RSTREAM SELECT * FROM seaDefence[NOW];", #TODO: provide correct query
		 "OD" : "RSTREAM SELECT * FROM seaDefence[NOW];"} #TODO: provide correct query 

MHOSC_BETA = 5 #Multihop Oscilloscope Buffering factor

def parseArgs(args):	
	global optOutputDir, optPlatList, optExprList
	try:
		optNames = ["outputdir=", "plat=", "exp="]
	
		#append the result of getOpNames to all the libraries 
		optNames = UtilLib.removeDuplicates(optNames)
		
		opts, args = getopt.getopt(args, "h",optNames)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
			
	for o, a in opts:
		if (o == "--plat"):
			optPlatList = a.split(',')
		if (o == "--exp"):
			optExprList = a.split(',')


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
	#if not os.path.isdir(optOutputDir):
	#		os.makedirs(optOutputDir)
			
	hdlr = logging.FileHandler('%s/%s-%s.log' % (optOutputDir, optLabel, timeStamp))
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)	
	logger.addHandler(hdlr) 
	logger.setLevel(logging.INFO)
	logger.info('Starting Regression Test')


def createSNEEPropertiesFile(runAttr):
	global sneeRoot
	
	str = '''# Determines whether graphs are to be generated.
compiler.generate_graphs = true

# Instructs query operator tree graphs to show operator output type 
compiler.debug.show_operator_tuple_type = true

compiler.convert_graphs = false
graphviz.exe = /usr/local/bin/dot

# Purge old output files at the start of every run
compiler.delete_old_files = true

# the root directory for the compiler outputs
compiler.output_root_dir = output

# Using equivalence-preserving transformation removes unrequired
# operators (e.g., a NOW window combined with a RSTREAM)
# TODO: currently in physical rewriter, move this to logical rewriter
# TODO: consider removing this option
# FIXME: Should not be a required property
compiler.logicalrewriter.remove_unrequired_operators = true

# Pushes project operators as close to the leaves of the operator
# tree as possible.
# TODO: currently in physical rewriter, move this to logical rewriter
# TODO: consider removing this option
# FIXME: Should not be a required property
compiler.logicalrewriter.push_project_down = true

# Combines leaf operators (receive, acquire, scan) and select operators
# into a single operator
# NB: In Old SNEE in the translation/rewriting step
# TODO: Only works for acquire operators at the moment
# TODO: consider removing this option
# FIXME: Should not be a required property
compiler.logicalrewriter.combine_leaf_and_select = true

# Sets the random seed used for generating routing trees
# FIXME: Should not be a required property
compiler.router.random_seed = 4

# Removes unnecessary exchange operators from the DAF
# FIXME: Should not be a required property
compiler.where_sched.remove_redundant_exchanges = false

# Instructs where-scheduler to decrease buffering factor
# to enable a shorter acquisition interval.
# FIXME: Should not be a required property
compiler.when_sched.decrease_beta_for_valid_alpha = true

#Specifies whether agendas generated should allow sensing to have interruptions
#Use this option to enable high acquisition intervals
compiler.allow_discontinuous_sensing = false

# Location of the logical schema
logical_schema = etc/inqp-logical-schema.xml

# Location of the physical schema
physical_schema = etc/%s

# Location of the cost parameters file
# TODO: This should be moved to physical schema, as there  is potentially
# one set of cost parameters per source.
# FIXME: Should not be a required property
cost_parameters_file = etc/inqp-cost-parameters.xml

# The name of the file with the types
types_file = etc/Types.xml

# The name of the file with the user unit definitions
units_file = etc/units.xml

# Specifies whether individual images or a single image is sent to WSN nodes.
sncb.generate_combined_image = false

# Specifies whether the metadata collection program should be invoked, 
# or default metadata should be used.
sncb.perform_metadata_collection = false

# Specifies whether the command server should be included with SNEE query plan
# Only compatible with Tmote Sky TinyOS2 code generation target
sncb.include_command_server = false

# Specifies code generation target
# tmotesky_t2 generates TinyOS v2 code for TelosB or TmoteSky hardware
# avrora_mica2_t2 generates TinyOS v2 code for Avrora simulator emulating mica2 hardware
# avrora_micaz_t2 generates TinyOS v2 code for Avrora simulator emulating micaz hardware
#   (power management currently does not work with avrora_mica2_t2, 
#    for power management use avrora_micaz_t2)
# tossim_t2 generates TinyOS v2 code for Tossim simulator
sncb.code_generation_target = avrora_micaz_t2

# Turns the radio on/off during agenda evalauation, 
# to enable power management to kick in.
# Ignored for tossim and telosb targets.
sncb.control_radio = true

TIMESTAMP_FORMAT = yyyy-MM-dd HH:mm:ss.SSS Z
WEBROWSET_FORMAT = http://java.sun.com/xml/ns/jdbc

# Size of history, in tuples, maintained per stream
results.history_size.tuples = 1000

# Determines whether Avrora DEBUG code is added,
# for use by c-print monitor
sncb.avrora_print_debug = true
	'''
	newStr = str % (runAttr['PhysicalSchemaFilename'])
	propsFilename =  "etc/exp" + runAttr["Experiment"] + "-snee.properties"
	propsFile = open(sneeRoot+os.sep+propsFilename, "w")
	propsFile.writelines(newStr)
	return propsFilename

def createSNEEParametersFile(runAttr):
	global sneeRoot
	
	tmpStr = '''<?xml version="1.0"?>

<query-parameters
xmlns="http://snee.cs.manchester.ac.uk"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://snee.cs.manchester.ac.uk query-parameters.xsd">

	<qos-expectations>

		<optimization-goal>
			<type>NONE</type>
			<variable>NONE</variable>
			<weighting>1</weighting>
		</optimization-goal>

		<acquisition-interval>
			<units>SECONDS</units>
			<constraint>
				<range>	
					<min-val>%s</min-val>
					<max-val>%s</max-val>					
				</range>	
			</constraint>
			<weighting>1</weighting>
		</acquisition-interval>	
		
		<buffering-factor>
			<constraint>
				<range>	
					<min-val>1</min-val>
					<max-val>%d</max-val>					
				</range>	
			</constraint>
			<weighting>1</weighting>
		</buffering-factor>			
		
		<delivery-time>
			<units>SECONDS</units>
			<constraint>
				<less-equals>9999</less-equals>
			</constraint>
			<weighting>2</weighting>
		</delivery-time>
	
	</qos-expectations>

<!-- Not currently implemented, but just to give an idea of what other
parameters may be associated with a query...

	<data-analysis>
	</data-analysis>
	
	<execution-schedule>
		<start-time>10:00 30 AUG 2010</start-time>
		<stop-time>22:00 30 AUG 2010</stop-time>
	</execution-schedule>
-->

</query-parameters>
	'''
	maxBF=9999
	if (runAttr["Y"]) == "Freshness":
		maxBF = 1
	newStr = tmpStr % (runAttr["AcquisitionRate"], runAttr["AcquisitionRate"], maxBF)
	paramsFilename = "etc/exp" + runAttr["Experiment"] + "-query-parameters.xml"
	paramsFile = open(sneeRoot+os.sep+paramsFilename, "w")
	paramsFile.writelines(newStr)
	return paramsFilename


def getBufferingFactor():
	global sneeRoot
	deliverOpFilename = None
	beta = None
	mote0Dir = "%s/output/query1/avrora_micaz_t2/mote0" % (sneeRoot)
	for filename in os.listdir(mote0Dir):
		if filename.startswith("deliverOp"):
			deliverOpFilename = mote0Dir+os.sep+filename
			break
	if deliverOpFilename != None:
		for line in open(deliverOpFilename, 'r'):
			m = re.search("#define BUFFERING_FACTOR (\d+)", line)
			if (m != None):
				beta = int(m.group(1))
				break
	if beta != None:
		return beta
	else:
		print "BUFFERING FACTOR NOT FOUND in "+str(deliverOpFilename)
		sys.exit(4)	


def runSNEE(runAttr):
	global sneeRoot
	
	propertiesFilename = createSNEEPropertiesFile(runAttr)
	queryStr = runAttr["Query"]
	queryParametersFilename = createSNEEParametersFile(runAttr)

	#query optimizer parameters
	os.chdir(sneeRoot)

	#Example SNEE invocation:
	#java uk.ac.manchester.cs.snee.client.SampleClient "etc/dqp.snee.properties" "(SELECT * FROM envdata_haylingisland) UNION (SELECT * FROM envdata_sandownbay);" 30 null null
	commandStr = "java -Xmx1024m uk/ac/manchester/cs/snee/client/SampleClient \"%s\" \"%s\" ind \"%s\" null" % (propertiesFilename, queryStr, queryParametersFilename)
		
	#compile the query for using the SNEEql optimizer
	print commandStr
	exitVal = os.system(commandStr)
	
	runAttr['SNEEExitCode'] = exitVal

	if exitVal==0:
		runAttr['BufferingFactor'] = getBufferingFactor()

def getElfString(numNodes):
	elfs = []
	ones = []
	for i in range(0, numNodes):
		fileName = "mote"+str(i)+".elf"
		if os.path.exists(fileName):
			elfs += [fileName]
		else:
			elfs += ["Blink.elf"]
		ones += ['1']
			
	return (string.join(elfs,' '),string.join(ones,","))

def getRunOutputDir(runAttr, rootOutputDir, task):
	return rootOutputDir+os.sep+"exp"+runAttr["Experiment"]+"-"+runAttr["Platform"]+"-x"+runAttr["xvalLabel"]+"-"+task

def runINSNEEExperiment(task,xVals,xValLabels,xValAttr,exprAttr,runAttrCols,rootOutputDir):
	global sneeRoot
	
	for (x,xValLabel) in zip(xVals,xValLabels):
		runAttr = initRunAttr(exprAttr, x, xValLabel, xValAttr, 'INSNEE', task)
		runAttr["Query"] = tasks2queries[task]
	
		print "\n**********Experiment="+runAttr['Experiment']+" Platform=INSNEE task="+task+" x="+x + " xLabel="+xValLabel

		#check if equiv experiment run exists
		if (runAttr['Experiment'],'INSNEE') in equivRuns.dict:
			equivRuns.copyExperimentRunResults(runAttr, rootOutputDir)
		else:			
			#1 Compile SNEEql query
			runSNEE(runAttr)
	
	     
		

def obtainNetworkTopologyAttributes(runAttr):
	physicalSchemaName = runAttr['PhysicalSchema']

        #get the network attributes from topology file name
	m = re.search("n(\d+)_(linear|grid|random)_d(\d+)_s(\d+)", physicalSchemaName)
	if (m != None):
		runAttr['NetworkSize'] = int(m.group(1))
		runAttr['Layout'] = m.group(2)
		runAttr['NetworkDensity'] = int(m.group(3))
		runAttr['NetworkPercentSources'] = int(m.group(4))
		runAttr['PhysicalSchemaFilename'] = networkLib.getPhysicalSchemaFilename(runAttr['NetworkSize'],runAttr['Layout'],runAttr['NetworkDensity'],runAttr['NetworkPercentSources'])
		(runAttr['SNEETopologyFilename'],runAttr['AvroraTopologyFilename']) = networkLib.getTopologyFilenames(runAttr['NetworkSize'],runAttr['Layout'],runAttr['NetworkDensity'])
	else:
		print "ERROR: physical schema filename does not conform to standard format"
		sys.exit(2)


def getSensorDataString(numNodes):
	sensorData = []
	for i in range(numNodes):
		sensorData += ["light:"+str(i)+":."]
	return string.join(sensorData,',')

def generateAvroraLogfileName(runAttr):
	 return "%s-exp%s-x%s-avrora-log.txt" % (runAttr["Platform"], runAttr["Experiment"], runAttr["xvalLabel"])


def initRunAttr(exprAttr, x, xValLabel, xValAttr, plat, task):
	runAttr = exprAttr.copy()
	runAttr["Platform"] = plat
	#set fixed parameters for the experiments
	runAttr["PhysicalSchema"] = runAttr["PhysicalSchemas"]
	runAttr["RadioLossRate"] = runAttr["RadioLossRates"]
	runAttr["AcquisitionRate"] = runAttr["AcquisitionRates"]
	#overwrite variable param
	runAttr[xValAttr] = x
	runAttr["xvalLabel"] = xValLabel
	obtainNetworkTopologyAttributes(runAttr)
	runAttr["Task"] = task
	return runAttr

def runExperiment(exprAttr, exprAttrCols, outputDir):
	global optPlatList

	runAttrCols = exprAttrCols + ["BufferingFactor", "Platform", "Task", "xvalLabel", "SNEEExitCode", "NetworkSize", "Layout", "NetworkDensity","NetworkPercentSources", "SimulationDuration", "Tuple Acq Count", "Tuple Del Count", "Tuple Delta Sum", "Data Freshness", "Output Rate", "Delivery Rate", "Sum Energy", "Sum Energy 6M", "Max Energy", "Average Energy", "CPU Energy", "Sensor Energy", "Other Energy", "Network Lifetime secs", "Network Lifetime days", "Comments"]

	tasks = exprAttr["Tasks"].split(";")
	xValAttr = exprAttr["XvalAttr"]
	xVals = exprAttr[xValAttr+"s"].split(";")
	xValLabels = exprAttr["XvalLabels"].split(";")

	for plat in optPlatList:	
		for task in tasks:
			if (plat == "INSNEE"):
				runINSNEEExperiment(task,xVals,xValLabels,xValAttr,exprAttr,runAttrCols,outputDir)
				

				
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
						

def main(): 	
	global optScenarioDir, optOutputDir

	#parse the command-line arguments
	parseArgs(sys.argv[1:]) 

	timeStamp = UtilLib.getTimeStamp()
	#if (not optTimeStampOutput):
	#	timeStamp = ""
	startLogger(timeStamp)
	
	#RandomSeeder.setRandom()
	
	runExperiments(timeStamp, optOutputDir+os.sep+timeStamp)

if __name__ == "__main__":
	main()
