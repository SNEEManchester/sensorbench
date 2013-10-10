import CSVLib, SBLib, os, sys

resultsFiles = []

#This script creates separate files for exp2a on a per-task and per-platform basis 
def main():
	first = True
	for line in open("csv"+os.sep+"all-results-avg.csv", 'r'):
		if first:
			runAttrCols = CSVLib.colNameList(line)
			first = False
			continue

		runAttr = CSVLib.line2Dict(line, runAttrCols)			
		if (runAttr['Experiment'] != '2a'):
			continue

		#Per-experiment/plaftform results file
		resultsFileName = "csv"+os.sep+"exp"+runAttr["Experiment"]+"-"+runAttr["Platform"]+"-"+runAttr["Task"]+"-results-avg.csv"

		#First write to a file, if file exists delete as was created in previous run
		if (not (resultsFileName in resultsFiles)):
			if (os.path.exists(resultsFileName)):
				os.remove(resultsFileName)
			resultsFiles.extend([resultsFileName])
			print "Creating "+resultsFileName

		SBLib.logResultsToFile(runAttr, runAttrCols, resultsFileName)
			

if __name__ == "__main__":
	main()
