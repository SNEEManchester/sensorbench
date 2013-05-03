#!/usr/bin/python

import re, getopt, logging, sys, os, string, UtilLib, CSVLib, AvroraLib, networkLib, shutil
import parseAcquireDeliverTimes, equivRuns

optLabel = ""
optOutputDir = os.getenv('HOME')+os.sep+"tmp"+os.sep+"results"+os.sep

sneeRoot = os.getenv('SNEEROOT')

#optPlatList = ["MHOSC", "INSNEE"]
optPlatList = ["INSNEE"]
directory = ""

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

#Tests a candidate plan using Avrora
def runSNEEInAvrora(runAttr, runAttrCols):
	global sneeRoot

	nescRootDir = sneeRoot + os.sep + "output" + os.sep + "query1" + os.sep + "avrora_micaz_t2"
	os.chdir(nescRootDir)
	
	simDuration = int(runAttr["AcquisitionRate"])*runAttr["BufferingFactor"]
	runAttr["SimulationDuration"] = simDuration
	
	sensorDataString = getSensorDataString(runAttr['NetworkSize'])
	(elfString, nodeCountString) = getElfString(runAttr['NetworkSize'])
	avroraLogFile = generateAvroraLogfileName(runAttr)

	#topologyStr = ""
	topologyStr = "-topology=static -topology-file="+sneeRoot+"/etc/"+runAttr['AvroraTopologyFilename']
	
        #NB: removed serial monitor, not needed as using c-print
	commandStr = "java avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network %s -seconds=%d -monitors=leds,packet,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=%s -report-seconds -colors=false -nodecount=%s  %s > %s" % (topologyStr, simDuration, sensorDataString, nodeCountString, elfString, avroraLogFile)

	print commandStr

	#comment out when debugging
	os.system(commandStr)
	#sys.exit()

	#get values for freshness of data, output rate
	parseAcquireDeliverTimes.parse(avroraLogFile, runAttr, True)
	
	#get values for total energy, lifetime
	parseEnergyMonitorOutput(avroraLogFile, runAttr)



def logResultsToFile(runAttr, runAttrCols, resultsFileName):
	if not os.path.exists(resultsFileName):
		resultsFile = open(resultsFileName, "w")
		resultsFile.writelines(CSVLib.header(runAttrCols))
	
	resultsFile = open(resultsFileName, "a")
	resultsFile.writelines(CSVLib.line(runAttr, runAttrCols))
	resultsFile.close()


def logResultsToFiles(runAttr, runAttrCols, outputDir):
	#Per-experiment/plaftform results file
	resultsFileName = outputDir+os.sep+"exp"+runAttr["Experiment"]+"-"+runAttr["Platform"]+"-results.csv"
	logResultsToFile(runAttr, runAttrCols, resultsFileName)
	#All experiments results file
	resultsFileName = outputDir+os.sep+"all-results.csv"
	logResultsToFile(runAttr, runAttrCols, resultsFileName)

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
	
	                #2 Run the query in Avrora
			if (runAttr['SNEEExitCode']==0):
				runSNEEInAvrora(runAttr, runAttrCols)

		        #copy SNEE/nesC/avrora files over
			runOutputDir = getRunOutputDir(runAttr, rootOutputDir, task) 
			os.makedirs(runOutputDir)
			sneeOutputDir = sneeRoot + os.sep + "output" + os.sep + "query1" + os.sep
			shutil.copytree(sneeOutputDir + "query-plan", runOutputDir+ os.sep + "query-plan")
			if (os.path.exists(sneeOutputDir + "avrora_micaz_t2")):
				shutil.copytree(sneeOutputDir + "avrora_micaz_t2", runOutputDir+ os.sep + "avrora_micaz_t2")
			shutil.copyfile(sneeRoot + os.sep + "logs/snee.log", runOutputDir + os.sep + "snee.log")

	        #3 Log the results
		logResultsToFiles(runAttr, runAttrCols, rootOutputDir)   
		

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

def runMHOSCInAvrora(runAttr, outputDir):
	global directory
	global MHOSC_BETA
	
	#An example avrora command string to invoke Multihop Oscilloscope
	#java avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network -seconds=10 -monitors=leds,packet,serial,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=light:1:.,light:2:.,light:3:.,light:4:.,light:5:.,light:6:.,light:7:.,light:8:.,light:9:.,light:10:.,light:11:.,light:12:.,light:13:.,light:14:.,light:15:.,light:16:.,light:17:.,light:18:.,light:19:.,light:20:.,light:21:.,light:22:.,light:23:.,light:24:.,light:25:. -report-seconds -nodecount=25  mhosc_1024_5_cprint.elf > mhosc_1024_5_cprintstr_example-output_no-top.txt

	simDuration = int(runAttr["AcquisitionRate"])*MHOSC_BETA*10
	runAttr["SimulationDuration"] = simDuration
	
	networkSize = runAttr['NetworkSize']
	sensorDataString = getSensorDataString(runAttr['NetworkSize'])
	mhoscExe = "%smhosc-a%s-b%d.elf" % (directory, runAttr["AcquisitionRate"], MHOSC_BETA)
	avroraLogFile = generateAvroraLogfileName(runAttr)

	topologyStr = "-topology=static -topology-file="+sneeRoot+"/etc/"+runAttr['AvroraTopologyFilename']

        #NB: no serial monitor, using cprint instead
       	commandStr = "java avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network -seconds=%d %s -monitors=leds,packet,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=%s -report-seconds -colors=false -nodecount=%d  %s > %s" % (simDuration, topologyStr, sensorDataString, networkSize, mhoscExe, avroraLogFile)

	print commandStr

	#comment out when debugging
	os.system(commandStr)
	#sys.exit()

	#get values for freshness of data, output rate
	parseAcquireDeliverTimes.parse(avroraLogFile, runAttr, False)
	
	#get values for total energy, lifetime
	parseEnergyMonitorOutput(avroraLogFile, runAttr)

	#move Avrora file out to results dir
	shutil.move(avroraLogFile,outputDir+os.sep+avroraLogFile)


def parseEnergyMonitorOutput(avroraLogFile, runAttr):

	simulationDuration = runAttr["SimulationDuration"]
	(sumEnergy, maxEnergy, averageEnergy, radioEnergy, cpu_cycleEnergy, sensorEnergy, otherEnergy, networkLifetime) = AvroraLib.computeEnergyValues(".", simulationDuration, avroraLogFile, ignoreLedEnergy = True, defaultSiteEnergyStock = 31320, siteLifetimeRankFile = None, sink = 0, ignoreList = [])
	#All node energy in Joules for simulation duration
	runAttr["Sum Energy"] = sumEnergy
        #All node energy in Joules scaled to 6 month period
	runAttr["Sum Energy 6M"] = sumEnergy*((60.0*60.0*24.0*30.0*6.0)/float(simulationDuration))
	runAttr["Max Energy"] = maxEnergy
	runAttr["Average Energy"] = averageEnergy
	runAttr["CPU Energy"] = cpu_cycleEnergy
	runAttr["Sensor Energy"] = sensorEnergy
	runAttr["Other Energy"] = otherEnergy
	runAttr["Network Lifetime secs"] = networkLifetime
	runAttr["Network Lifetime days"] = float(networkLifetime)/60.0/60.0/24.0


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

		
def runMHOSCExperiment(task,xVals,xValLabels,xValAttr,exprAttr,runAttrCols,outputDir):
	global directory, MHOSC_BETA

	if task != 'raw':
		return
	
	runAttr["Query"] = tasks2queries[task]
	for (x,xValLabel) in zip(xVals,xValLabels):
		runAttr = initRunAttr(exprAttr, x, xValLabel, xValAttr, 'MHOSC', task)
		
		print "\n**********Experiment="+runAttr['Experiment']+" Platform=MHOSC task="+task+" x="+x + " xLabel="+xValLabel
		runAttr["BufferingFactor"] = MHOSC_BETA

		#check if equiv experiment run exists
		if (runAttr['Experiment'],'MHOSC') in equivRuns.dict:
			equivRuns.copyExperimentRunResults(runAttr, rootOutputDir)
		else:
			#2 Run osc in Avrora
			runMHOSCInAvrora(runAttr, outputDir, directory)
	
		#3 Log the results
		logResultsToFiles(runAttr, runAttrCols, outputDir)

def runExperiment(exprAttr, exprAttrCols, outputDir):
	global directory, optPlatList

	runAttrCols = exprAttrCols + ["BufferingFactor", "Platform", "Task", "xvalLabel", "SNEEExitCode", "NetworkSize", "Layout", "NetworkDensity","NetworkPercentSources", "SimulationDuration", "Tuple Acq Count", "Tuple Del Count", "Tuple Delta Sum", "Data Freshness", "Output Rate", "Delivery Rate", "Sum Energy", "Sum Energy 6M", "Max Energy", "Average Energy", "CPU Energy", "Sensor Energy", "Other Energy", "Network Lifetime secs", "Network Lifetime days", "Comments"]

	tasks = exprAttr["Tasks"].split(";")
	xValAttr = exprAttr["XvalAttr"]
	xVals = exprAttr[xValAttr+"s"].split(";")
	xValLabels = exprAttr["XvalLabels"].split(";")

	for plat in optPlatList:	
		for task in tasks:
			if (plat == "MHOSC"):
				runMHOSCExperiment(task,xVals,xValLabels,xValAttr,exprAttr,runAttrCols,outputDir,directory)
			if (plat == "INSNEE"):
				runINSNEEExperiment(task,xVals,xValLabels,xValAttr,exprAttr,runAttrCols,outputDir,directory)
				

				
def runExperiments(timeStamp, outputDir, directory):
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
		runExperiment(exprAttr, exprAttrCols, outputDir, directory)
						

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
