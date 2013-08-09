#!/usr/bin/python
import re, os, sys, networkLib, math, getopt, UtilLib, CSVLib, shutil

optCondorDir = "condor"
optBinaryDir = "avroraJobsTar"
pathSeperator = os.sep

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
	condorFile.write("universe = vanilla \n executable = start.sh \n when_to_transfer_output = ON_EXIT \n Should_Transfer_Files = YES \n \n Requirements = (HAS_STANDARD_IMAGE =?= True) \n Request_Disk = 204800 \n request_memory = 512 \n #Output = output$(Process).txt \n #Error = error$(Process).txt \n log = log.txt \n Output = out.txt \n Error = err.txt \n notification = error \n\n\n")

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

def condorLine(file):
	file = file.split('.')[0]
	binaryFolderName = optBinaryDir + pathSeperator + file
	condorFile = open(optCondorDir + pathSeperator + "submit.txt", "a") 
	condorFile.write("transfer_input_files = ../avrora-1.7.113.jar,../jre.tar.gz,../%s.tar.gz \n" % (binaryFolderName))
	condorFile.write("Arguments = %s.tar.gz %s \n	initialdir   = %s \n	queue \n\n" % (file, file, file))
	check_dir(optCondorDir + pathSeperator + file)

def generateScriptForEachJob():
	fileList = os.listdir(optBinaryDir)
	for file in fileList:
		condorLine(file)

def generateScript():
    # writes top blurb for condor, which covers spec of machines, memory allocation, etc
		generateTopBlurb()
    #read in each folder from the avrora folder and make a top for it.
		generateScriptForEachJob()


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
	#moveCollections()

  


if __name__ == "__main__":
	main()
            
