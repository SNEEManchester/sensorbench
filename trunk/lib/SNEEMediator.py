import os, shutil, sys, re, string

sneeRoot = os.getenv('SNEEROOT')

tasks2queries = {"raw" : "RSTREAM SELECT * FROM seaDefence[NOW];", \
		 "aggr" : "RSTREAM SELECT AVG(seaLevel) FROM seaDefence[NOW];", \
		 "corr1" : "RSTREAM SELECT e.seaLevel, w.seaLevel FROM seaDefenceEast[NOW] e, seaDefenceWest[NOW] w WHERE e.seaLevel > w.seaLevel;", \
		 "corr2" : "RSTREAM SELECT e.seaLevel, w.seaLevel FROM seaDefenceEast[NOW] e, seaDefenceWest[FROM NOW TO NOW-1 SECOND] w WHERE e.seaLevel > w.seaLevel;", \
		 "LR" : "RSTREAM SELECT * FROM seaDefence[NOW];", #TODO: provide correct query
		 "OD" : "RSTREAM SELECT * FROM seaDefence[NOW];"} #TODO: provide correct query 

def init(scenarioDir):
	global sneeRoot, optScenarioDir

	optScenarioDir = scenarioDir
	
	#copy scenarios to SNEE directory
	#TODO: check whether top files are needed (prob not)
	for f in os.listdir(scenarioDir):
		shutil.copy(scenarioDir + os.sep + f, sneeRoot + os.sep + "etc")


def cleanup(scenarioDir):
	global sneeRoot
	
	#remove scenario files from SNEE directory
	for f in os.listdir(scenarioDir):
		scenarioFile = sneeRoot + os.sep + "etc" + os.sep + f
		if os.path.exists(scenarioFile):
			os.remove(scenarioFile)

def getSneeRoot():
	global sneeRoot
	return sneeRoot

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

def compileQuery(runAttr):
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
	
	runAttr['ExitCode'] = exitVal

	if exitVal==0:
		runAttr['BufferingFactor'] = getBufferingFactor()

def getElfString(numNodes, avroraElfDir):
	elfs = []
	ones = []
	for i in range(0, numNodes):
		fileName = avroraElfDir + os.sep + "mote"+str(i)+".elf"
		if os.path.exists(fileName):
			elfs += [os.path.basename(fileName)]
		else:
			elfs += ["Blink.elf"]
		ones += ['1']
			
	return (string.join(elfs,' '),string.join(ones,","))

def getSensorDataString(numNodes):
	sensorData = []
	for i in range(numNodes):
		sensorData += ["light:"+str(i)+":."]
	return string.join(sensorData,',')

def getAvroraCommandString(runAttr, runAttrCols, avroraElfDir):
	simDuration = int(runAttr["AcquisitionRate"])*runAttr["BufferingFactor"]
	runAttr["SimulationDuration"] = simDuration

	sensorDataString = getSensorDataString(runAttr['NetworkSize'])
	(elfString, nodeCountString) = getElfString(runAttr['NetworkSize'], avroraElfDir)
	#avroraLogFile = generateAvroraLogfileName(runAttr) #move this

	topologyStr = "-topology=static -topology-file="+runAttr['AvroraTopologyFilename']

        #NB: removed serial monitor, not needed as using c-print
	commandStr = "java avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network %s -seconds=%d -monitors=leds,packet,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=%s -report-seconds -colors=false -nodecount=%s  %s" % (topologyStr, simDuration, sensorDataString, nodeCountString, elfString)
	
	return commandStr

def generateAvroraJob(task,xVal,xValLabel,xValAttr,instance,runAttr,runAttrCols,rootOutputDir, runOutputDir, avroraJobsRootDir):
	global sneeRoot, optScenarioDir

	runAttr["Query"] = tasks2queries[task]

	#check if equiv experiment run exists
	#if (runAttr['Experiment'],'INSNEE') in equivRuns.dict:
	#equivRuns.copyExperimentRunResults(runAttr, rootOutputDir)
	#else:

	#1 Compile SNEEql query and compile the nesC to generate the Avrora binaries
	compileQuery(runAttr)

	sneeOutputDir = sneeRoot + os.sep + "output" + os.sep + "query1" + os.sep

	#2 Archive the output of SNEE in case we need to do a post mortem later
	tempSneeFilesRootDir = rootOutputDir + os.sep + "tempSNEEFiles" + os.sep + runOutputDir
	shutil.copytree(sneeOutputDir + "query-plan", tempSneeFilesRootDir+ os.sep + "query-plan")
	if (os.path.exists(sneeOutputDir + "avrora_micaz_t2")):
		shutil.copytree(sneeOutputDir + "avrora_micaz_t2", tempSneeFilesRootDir+ os.sep + "avrora_micaz_t2")
	shutil.copyfile(sneeRoot + os.sep + "logs/snee.log", tempSneeFilesRootDir + os.sep + "snee.log")
	
	#3 Create AvroraJobs folder
	if (runAttr['ExitCode']==0):
		#create dir for Avrora Job
		avroraJobDir = avroraJobsRootDir+os.sep+runOutputDir 
		os.makedirs(avroraJobDir)

		#Copy elf files to Avrora Job dir
		avroraElfDir = sneeOutputDir + "avrora_micaz_t2"
		if (os.path.exists(avroraElfDir)):
			for f in os.listdir(avroraElfDir):
				if (f.endswith(".elf")):
				    shutil.copy(avroraElfDir + os.sep + f, avroraJobDir)

		#Copy top file for avrora
		avroraTopFile = optScenarioDir + os.sep + runAttr['AvroraTopologyFilename']
		shutil.copy(avroraTopFile, avroraJobDir)
				    
		#Create Avrora CommandString.txt
		avroraCommandStr = getAvroraCommandString(runAttr, runAttrCols, avroraElfDir)
		avroraCommandStrFileName = avroraJobDir + os.sep + "avroraCommandString.txt"
		avroraCommandStrFile = open(avroraCommandStrFileName, "w")
		avroraCommandStrFile.writelines(avroraCommandStr)


#Tests a candidate plan using Avrora
#MAYBE SHOULDN'T BE HERE - PUT HERE FOR NOW
def runInAvrora():
	global sneeRoot

	#this will be the Avrora Job Directory
	nescRootDir = sneeRoot + os.sep + "output" + os.sep + "query1" + os.sep + "avrora_micaz_t2"
	os.chdir(nescRootDir)

	commandStr = getAvroraCommandString(runAttr, runAttrCols)

	#comment out when debugging
	os.system(commandStr)
	#sys.exit()

	#The following will happen outside Condor
	#get values for freshness of data, output rate
	parseAcquireDeliverTimes.parse(avroraLogFile, runAttr, True)
	
	#get values for total energy, lifetime
	parseEnergyMonitorOutput(avroraLogFile, runAttr)








