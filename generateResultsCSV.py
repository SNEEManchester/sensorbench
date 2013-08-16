#!/usr/bin/python
import os, sys, getopt, SBLib, CSVLib, SBLib
import parseAcquireDeliverTimes

#The directory that contains the directories produced by condor with results
optCondorOutputDir = os.getenv("HOME") + os.sep + "condor_results_6aug2013"

#This is the directry where the results CSV files will end up
optOutputDir = os.getcwd() + os.sep + "graphs"


def parseArgs(args):
	global optCondorOutputDir, optOutputDir

	try:
		optNames = ["condor-output-dir=", "output-dir="]
		opts, args = getopt.getopt(args, "h", optNames)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
			
	for o, a in opts:
		if (o == "--condor-output-dir"):
			optCondorOutputDir = a
		elif (o == "--outputDir"):
			optOutputDir = a


def usage():
	print "generateResultsCSV.py --condor-output-dir=<dir> --output-dir=<dir>"

#Generates one line per scenario instance in the CSV file 
def generatePerRunResults():
	global optCondorOutputDir, optOutputDir

	resultsDir = optCondorOutputDir
	os.chdir(resultsDir)

	first = True
	for line in open("all-runs.csv", 'r'):
		if first:
			runAttrCols = CSVLib.colNameList(line)
			first = False
			continue

		runAttr = CSVLib.line2Dict(line, runAttrCols)

		#find folder with run results for current line in all-results.csv
		runDirName = SBLib.getRunOutputDir(runAttr)
		if (os.path.exists(optCondorOutputDir + os.sep + runDirName)):
			print runDirName
			avroraLogFile = runDirName + os.sep + "out.txt"

			#find output file and process
			SBLib.getAvroraEnergyValues(avroraLogFile, runAttr)
			parseAcquireDeliverTimes.parse(avroraLogFile, runAttr, False)

		#Recreates the CSV, this time with the results from the Avrora simulation
		SBLib.logResultsToFiles(runAttr, runAttrCols, optOutputDir, "results-raw")			


#Generates one line per scenario in the CSV file (aggregates the instances)
def generateAggregatedResults():
	global optOuputDir
	os.chdir(optOutputDir)

	first = True
	#The "averageable" attributes
	avgAttrList = ['Tuple Acq Count', 'Tuple Del Count', 'Tuple Delta Sum',	'Data Freshness', 'Output Rate', 'Delivery Rate', 'Sum Energy', 'Sum Energy 6M', 'Max Energy', 'Average Energy', 'CPU Energy', 'Sensor Energy', 'Other Energy', 'Network Lifetime secs', 'Network Lifetime days']

	#Used for computing average values for attributes
	cumSumAttr = None
	counter = 0
	#Used to keep track of which instances belong to the same scenario
	prevX = None
	currentX = None

	for line in open("all-results-raw.csv", 'r'):
		#Header line in file
		if first:
			runAttrCols = CSVLib.colNameList(line)
			first = False
			continue

		#Non-header lines in the file
		runAttr = CSVLib.line2Dict(line, runAttrCols)
		if runAttr.has_key('xvalLabel'):
			currentX = runAttr["xvalLabel"]
		else:
			break;

		if (cumSumAttr == None): #First instance of the file
			#Reset cumulative sum/counter
			cumSumAttr = runAttr
			counter += 1
			prevX = currentX
			continue
		if (currentX == prevX):
			#Add averageable attributes from current runAttr to cumSumAttr
			for attr in avgAttrList:
				cumSumAttr[attr] = float(cumSumAttr[attr]) + float(runAttr[attr])
			counter += 1
			continue
		else:
			#Calculate average
			for attr in avgAttrList:
				cumSumAttr[attr] = float(cumSumAttr[attr]) / float(counter)
			#Write to file
			SBLib.logResultsToFiles(cumSumAttr, runAttrCols, optOutputDir, "results-avg")
			#Reset cumulative sum/counter
			cumSumAttr = runAttr
			counter = 1
			prevX = currentX
			continue

	#At the end of file
	#Calculate average
	if (counter > 0):
		for attr in avgAttrList:
			cumSumAttr[attr] =  float(cumSumAttr[attr]) / float(counter)
		#Write to file
		SBLib.logResultsToFiles(cumSumAttr, runAttrCols, optOutputDir, "results-avg")


def processCondorResults():
	generatePerRunResults()
	generateAggregatedResults()


def main():
	global optCondorOutputDir

	#parse the command-line arguments
	parseArgs(sys.argv[1:]) 

	processCondorResults()

if __name__ == "__main__":
	main()


