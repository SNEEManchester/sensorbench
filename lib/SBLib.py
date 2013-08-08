#This library holds functions used by more than one sensebench script

import os, CSVLib

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


