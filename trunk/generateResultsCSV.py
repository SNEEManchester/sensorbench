#!/usr/bin/python
import os, sys, getopt, SBLib, CSVLib, SBLib
import parseAcquireDeliverTimes

#The directory that contains the directories produced by condor with results
optCondorOutputDir = os.getenv("HOME") + os.sep + "condor_results_6aug2013"

#This is the directry where the results CSV files will end up
optOutputDir = os.getcwd()


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


def processCondorResults():
	global optCondorOutputDir, optOutputDir

	resultsDir = optCondorOutputDir
	os.chdir(resultsDir)

	first = True 
	#TODO: We need all-results.csv copied into condor output folder
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
		SBLib.logResultsToFiles(runAttr, runAttrCols, optOutputDir, "results")			


def main():
	global optCondorOutputDir

	#parse the command-line arguments
	parseArgs(sys.argv[1:]) 

	processCondorResults()

if __name__ == "__main__":
	main()


