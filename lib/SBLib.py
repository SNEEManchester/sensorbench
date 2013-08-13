#This library holds functions used by more than one sensebench script

import os, CSVLib, AvroraLib

#Logs the contents of RunAttr hash for single file
def logResultsToFile(runAttr, runAttrCols, resultsFileName):
	if not os.path.exists(resultsFileName):
		resultsFile = open(resultsFileName, "w")
		resultsFile.writelines(CSVLib.header(runAttrCols))
	
	resultsFile = open(resultsFileName, "a")
	resultsFile.writelines(CSVLib.line(runAttr, runAttrCols))
	resultsFile.close()


#Logs the contents of RunAttr hash (one global file, one per experiment/platform)
def logResultsToFiles(runAttr, runAttrCols, outputDir):
	#Per-experiment/plaftform results file
	resultsFileName = outputDir+os.sep+"exp"+runAttr["Experiment"]+"-"+runAttr["Platform"]+"-results.csv"
	logResultsToFile(runAttr, runAttrCols, resultsFileName)
	#All experiments results file
	resultsFileName = outputDir+os.sep+"all-results.csv"
	logResultsToFile(runAttr, runAttrCols, resultsFileName)


#Returns dirname according to convention
def getRunOutputDir(runAttr):
	return "exp"+runAttr["Experiment"]+"-"+runAttr["Platform"]+"-x"+runAttr["xvalLabel"]+"-"+runAttr["Task"]+"-"+str(runAttr["Instance"])


#copies parsed values from Avrora simulation into runAttr hash table
def getAvroraEnergyValues(avroraLogFile, runAttr):

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

