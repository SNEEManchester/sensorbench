import os, shutil, sys, re, string, AvroraLib

MHOSC_BETA = 5 #Multihop Oscilloscope Buffering factor

def init(scenarioDir, avroraElfDir):
	global optScenarioDir, optAvroraElfDir
	optScenarioDir = scenarioDir
	optAvroraElfDir = avroraElfDir
	#Compile ELF binaries binaries are assumed to be already compiled


def cleanup():
	#Do nothing!
	print


def getMHOSCElfFilename(runAttr):
	a = runAttr['AcquisitionRate']
	b = MHOSC_BETA
	return "mhosc-a"+str(a)+"-b"+str(b)+".elf"

def getAvroraCommandString(runAttr, runAttrCols, avroraElfDir):
	global MHOSC_BETA

	simDuration = int(runAttr["AcquisitionRate"])*MHOSC_BETA*10
	runAttr["SimulationDuration"] = simDuration

	topologyStr = "-topology=static -topology-file="+runAttr['AvroraTopologyFilename']
	sensorDataString = AvroraLib.getSensorDataString(runAttr['NetworkSize'])
	nodeCountStr = runAttr['NetworkSize']
	elfString = getMHOSCElfFilename(runAttr)

	commandStr = "java avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network -seconds=%d %s -monitors=leds,packet,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=%s -report-seconds -colors=false -nodecount=%d  %s" % (simDuration, topologyStr, sensorDataString, nodeCountStr, elfString)
	return commandStr


def generateAvroraJob(task,xVal,xValLabel,xValAttr,instance,runAttr,runAttrCols,rootOutputDir, runOutputDir, avroraJobsRootDir):
	global optScenarioDir, optAvroraElfDir

	#check if equiv experiment run exists
	#if (runAttr['Experiment'],'INSNEE') in equivRuns.dict:
	#equivRuns.copyExperimentRunResults(runAttr, rootOutputDir)
	#else:

	#3 Create AvroraJobs folder
	#create dir for Avrora Job
	avroraJobDir = avroraJobsRootDir+os.sep+runOutputDir 
	os.makedirs(avroraJobDir)

	#Copy elf files to Avrora Job dir
	if (os.path.exists(optAvroraElfDir)):
		f = getMHOSCElfFilename(runAttr)
		shutil.copy(optAvroraElfDir + os.sep + f, avroraJobDir)

	#Copy top file for avrora
	avroraTopFile = optScenarioDir + os.sep + runAttr['AvroraTopologyFilename']
	shutil.copy(avroraTopFile, avroraJobDir)
			    
	#Create Avrora CommandString.txt
	avroraCommandStr = getAvroraCommandString(runAttr, runAttrCols, optAvroraElfDir)
	avroraCommandStrFileName = avroraJobDir + os.sep + "avroraCommandString.txt"
	avroraCommandStrFile = open(avroraCommandStrFileName, "w")
	avroraCommandStrFile.writelines(avroraCommandStr)






