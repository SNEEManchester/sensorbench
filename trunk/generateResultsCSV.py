import os, sys, getopt, SBLib, CSVLib, AvroraLib

#The directory that contains the directories produced by condor with results
optCondorOutputDir = os.getenv("HOME") + os.sep + "condor_results_6aug2013"

def parseArgs(args):
	global optCondorOutputDir, optRunDataCSV

	try:
		optNames = ["condor-output-dir="]
		opts, args = getopt.getopt(args, "h", optNames)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
			
	for o, a in opts:
		if (o == "--condor-output-dir"):
			optCondorOutputDir = a



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




def processCondorResults():
	global optCondorOutputDir

	resultsDir = optCondorOutputDir
	os.chdir(resultsDir)

	first = True 
	#TODO: We need all-results.csv copied into condor output folder
	for line in open("all-results.csv", 'r'):
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

			#TODO: find output file and process
			#parseEnergyMonitorOutput(avroraLogFile, runAttr)

		#SBLib.logResultsToFiles(runAttr, runAttrCols, outputDir)			


def main():
	global optCondorOutputDir

	#Reread CSV produced from runExperiments


	#parse the command-line arguments
	parseArgs(sys.argv[1:]) 

	processCondorResults()

if __name__ == "__main__":
	main()


