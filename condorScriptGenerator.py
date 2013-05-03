#!/usr/bin/python
import os, sys, networkLib, math, getopt, UtilLib

noInstances = 10

def parseArgs(args):	
	global optScenarioDir
	try:
		optNames = ["scenario-dir="]
	
		#append the result of getOpNames to all the libraries 
		optNames = UtilLib.removeDuplicates(optNames)
		
		opts, args = getopt.getopt(args, "h", optNames)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
			
	for o, a in opts:
		if (o == "--scenario-dir"):
			optScenarioDir = a
		else:
			usage()
			sys.exit(2)


def usage():
		print "generate-scenarios.py --scenario-dir=<dir>"

def check_dir(d):
	if not os.path.exists(d):
		os.makedirs(d)

def generateTopBlurb():
	open("test.txt", "w") as condorFile
  condorFile.write("universe = vanilla \n executable = start.sh \n when_to_transfer_output = ON_EXIT \n Should_Transfer_Files = YES \n transfer_input_files = ../SNEE.jar,../jre.tar.gz
Requirements = (OpSys == "LINUX") &&(HAS_STANDARD_IMAGE =?= True)
Request_Disk = 3000000 
request_memory = 2048 
#Output = output$(Process).txt 
#Error = error$(Process).txt 
log = log.txt 
Output = out.txt 
Error = err.txt 
notification = error 
	



def condorLine(task,xVals,xValLabels,xValAttr,exprAttr,runAttrCols,outputDir):
	




def generateScriptForEachJob(exprAttr, exprAttrCols, outputDir):
	global optPlatList, noInstances

	runAttrCols = exprAttrCols + ["BufferingFactor", "Platform", "Task", "xvalLabel", "SNEEExitCode", "NetworkSize", "Layout", "NetworkDensity","NetworkPercentSources", "SimulationDuration", "Tuple Acq Count", "Tuple Del Count", "Tuple Delta Sum", "Data Freshness", "Output Rate", "Delivery Rate", "Sum Energy", "Sum Energy 6M", "Max Energy", "Average Energy", "CPU Energy", "Sensor Energy", "Other Energy", "Network Lifetime secs", "Network Lifetime days", "Comments"]

	tasks = exprAttr["Tasks"].split(";")
	xValAttr = exprAttr["XvalAttr"]
	xVals = exprAttr[xValAttr+"s"].split(";")
	xValLabels = exprAttr["XvalLabels"].split(";")

	for plat in optPlatList:	
		for task in tasks:
			for instance in range(1,noInstances):
				condorLine(task,xVals,xValLabels,xValAttr,exprAttr,runAttrCols,outputDir)

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

		exprAttr['TimeStamp']=timeStamp
		#Experiment,X,Y,Tasks,Xlabels,Network,RadioLossRate,AcquisitionRate
		generateTopBlurb()
		generateScriptForEachJob(exprAttr, exprAttrCols, outputDir)



def main(): 	
	global optScenarioDir

  #parse the command-line arguments
	parseArgs(sys.argv[1:]) 
	generateScript()
  


if __name__ == "__main__":
	main()
            
