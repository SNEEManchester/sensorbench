#!/usr/bin/python
import re, os, sys, networkLib, math, getopt, UtilLib, CSVLib, shutil

optNumInstances = 10
optCondorDir = "condor"
optBinaryDir = "avrora-Bineries"
pathSeperator = os.sep

optExprList = ["1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b", "5a", "5b", "6a", "6b", "7"]
optPlatList = ["INSNEE", "HC", "TinyDB", "MHOCS"]
def parseArgs(args):	
	global optScenarioDir
	try:
		optNames = ["condor-dir=", "num-instances=", "binary-dir="]
	
		#append the result of getOpNames to all the libraries 
		optNames = UtilLib.removeDuplicates(optNames)
		
		opts, args = getopt.getopt(args, "h", optNames)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
			
	for o, a in opts:
		if (o == "--condor-dir"):
			optCondorDir = a
		elif (o == "--num-instances"):
			optNumInstances = int(a)
		elif (o == "--binary-dir"):
			optBinaryDir = a
		else:
			usage()
			sys.exit(2)


def usage():
	print "generate-scenarios.py --condor-dir=<dir> --num-instances=<int> --binary-dir=<dir>"


def check_dir(d):
	if not os.path.exists(d):
		os.makedirs(d)

def generateTopBlurb():
	check_dir(optCondorDir)
	condorFile = open(optCondorDir + pathSeperator + "submit.txt", "w") 
	condorFile.write("universe = vanilla \n executable = start.sh \n when_to_transfer_output = ON_EXIT \n Should_Transfer_Files = YES \n transfer_input_files = ../avrora-1.7.113.jar,../jre.tar.gz,../%s \n Requirements = (OpSys == \"LINUX\") &&(HAS_STANDARD_IMAGE =?= True) \n Request_Disk = 3000000 \n request_memory = 2048 \n #Output = output$(Process).txt \n #Error = error$(Process).txt \n log = log.txt \n Output = out.txt \n Error = err.txt \n notification = error \n\n\n" %(optBinaryDir+".zip"))

def getRunOutputDir(runAttr, task):
	return "exp"+runAttr["Experiment"]+"-"+runAttr["Platform"]+"-x"+runAttr["xvalLabel"]+"-"+task+"-"+str(runAttr["Instance"])

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
		runAttr['NetworkPercentSources'] = int(m.group(4))
		runAttr['PhysicalSchemaFilename'] = networkLib.getPhysicalSchemaFilename(runAttr['NetworkSize'],runAttr['Layout'],runAttr['NetworkDensity'],runAttr['NetworkPercentSources'],runAttr['Instance'])
		(runAttr['SNEETopologyFilename'],runAttr['AvroraTopologyFilename']) = networkLib.getTopologyFilenames(runAttr['NetworkSize'],runAttr['Layout'],runAttr['NetworkDensity'],runAttr['Instance'])
	else:
		print "ERROR: physical schema filename %s does not conform to standard format" % (physicalSchemaName)
		sys.exit(2)

def condorLine(task,xVal,xValLabel,xValAttr,exprAttr,instance, plat, runAttr):
	condorFile = open(optCondorDir + pathSeperator + "submit.txt", "a") 
	CONVENTION =getRunOutputDir(runAttr, task)
	binaryFolderName = optBinaryDir + pathSeperator + CONVENTION
	condorFile.write("Arguments = %s \n	initialdir   = %s \n	queue \n\n"%(binaryFolderName, CONVENTION))
	check_dir(optCondorDir + pathSeperator + CONVENTION)




def generateScriptForEachJob(exprAttr, exprAttrCols):
	global optPlatList, noInstances

	tasks = exprAttr["Tasks"].split(";")
	xValAttr = exprAttr["XvalAttr"]
	xVals = exprAttr[xValAttr+"s"].split(";")
	xValLabels = exprAttr["XvalLabels"].split(";")

	for plat in optPlatList:	
		for task in tasks:
			for (xVal,xValLabel) in zip(xVals,xValLabels):
				for instance in range(1,optNumInstances):
					runAttr = initRunAttr(exprAttr, xVal, xValLabel, xValAttr, instance, plat, task)
					condorLine(task,xVal,xValLabel,xValAttr,exprAttr,instance,plat,runAttr)

def generateScript():
	colNames = None
	first = True

	for line in open("experiments.csv", 'r'):
		if first:
			exprAttrCols = CSVLib.colNameList(line)
			exprAttrCols += ["TimeStamp"]
			first = False
			continue

		exprAttr = CSVLib.line2Dict(line, exprAttrCols)

		if not str(exprAttr['Experiment']) in optExprList:
			continue

		#Experiment,X,Y,Tasks,Xlabels,Network,RadioLossRate,AcquisitionRate
		generateTopBlurb()
		generateScriptForEachJob(exprAttr, exprAttrCols)


def moveCollections():
	shutil.copyfile(optBinaryDir+".zip", optCondorDir + pathSeperator + optBinaryDir+".zip")
	shutil.copyfile("avrora-1.7.113.jar", optCondorDir + pathSeperator + "avrora-1.7.113.jar")
	shutil.copyfile("jre.tar.gz", optCondorDir + pathSeperator + "jre.tar.gz")



def generateAvroraCode():
	avroraCode = open(optCondorDir + pathSeperator + "start.sh", "w")
	bineryZipFolder = optBinaryDir+".zip"
	
	avroraCode.write("#!/bin/bash \n echo $1 \n\n  unzip avrora-1.7.113.jar -d avrora \n rm avrora-1.7.113.jar \n mv jre.tar.gz avrora/jre.tar.gz \n mv %s avrora/%s \n cd  avrora \n tar -zxf jre.tar.gz \n rm jre.tar.gz \n unzip %s -d %s \n if \"$1\" == \"\" \n then exit(0) \N fi \n mv $1/* . \n rm %s \n rm -rf %s \n line=$(head -n 1 \"commandLine.txt\") \n	jre1.6.0_27/bin/java $line \n exit 0" %(bineryZipFolder, bineryZipFolder, bineryZipFolder, optBinaryDir, bineryZipFolder, optBinaryDir))

def main(): 	
	global optScenarioDir

  #parse the command-line arguments
	parseArgs(sys.argv[1:]) 
	generateScript()
	generateAvroraCode()
	moveCollections()

  


if __name__ == "__main__":
	main()
            
