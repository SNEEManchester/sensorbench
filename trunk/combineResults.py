import os, getopt, sys, shutil
import CSVLib, SBLib

optResultsRootDir = os.getenv('HOME')+os.sep+'SenseBench-results'
optCombinedResultsDir = optResultsRootDir+os.sep+'combined99'

def parseArgs(args):	
	global optResultsRootDir, optCombinedResultsDir
	try:
		optNames = ["results-root-dir=", "combined-results-dir="]
	
		#append the result of getOpNames to all the libraries 
		optNames = UtilLib.removeDuplicates(optNames)
		
		opts, args = getopt.getopt(args, "h",optNames)
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
			
	for o, a in opts:
		if (o == "--combined-results-dir"):
			optCombinedResultsDir = a
		elif (o == "--results-root-dir"):
			optResultsRootDir = a
		else:
			usage()
			sys.exit(2)


def usage():
	print "Use this script to combine the results of several runs prior to running generateResultsCSV.py"
	print "Usage:"
	print "combineResults.py --combined-results-dir=<dir>\n\t\tdefault="+optCombinedResultsDir

def shouldBeIncluded(desiredAttr,runAttr):
	exps = desiredAttr['exps'].split(';')
	plats = desiredAttr['plats'].split(';')
	tasks = desiredAttr['tasks'].split(';')
	startInstance = int(desiredAttr['instances'].split('-')[0])
	endInstance = int(desiredAttr['instances'].split('-')[1])

	if ((runAttr['Experiment'] in exps) and (runAttr['Platform'] in plats) and (runAttr['Task'] in tasks) and (int(runAttr['Instance'])>=startInstance) and (int(runAttr['Instance'])<=endInstance)):
		return True
	return False


def copyDataAcross(resultsRootDir, runAttr, runAttrCols):
	global optCombinedResultsDir	

	#copy line to combined all-runs.csv
	resultsFileName = optCombinedResultsDir + os.sep + "all-runs.csv"
	SBLib.logResultsToFile(runAttr, runAttrCols, resultsFileName)

	#copy rundir to combined dir
	try:
		sourceDir = resultsRootDir + os.sep + SBLib.getRunOutputDir(runAttr)
		destDir = optCombinedResultsDir + os.sep + SBLib.getRunOutputDir(runAttr)
		shutil.copytree(sourceDir, destDir)
	except:
		print "Warning: " + sourceDir + " not found"	


def parseExperimentalRun(desiredAttr):
	resultsRootDir = optResultsRootDir + os.sep + desiredAttr['dir']
	allRunsFile = resultsRootDir + os.sep + "all-runs.csv"

	print allRunsFile
	first = True
	for line in open(allRunsFile, 'r'):
		if first:
			runAttrCols = CSVLib.colNameList(line)
			first = False
			continue
		runAttr = CSVLib.line2Dict(line, runAttrCols)		
		if (shouldBeIncluded(desiredAttr,runAttr)):
			copyDataAcross(resultsRootDir, runAttr, runAttrCols)


def main():
	global optResultsRootDir, optCombinedResultsDir

	first = True
	for line in open("combine.csv", 'r'):
		if first:
			desiredAttrCols = CSVLib.colNameList(line)
			first = False
			continue
		desiredAttr = CSVLib.line2Dict(line, desiredAttrCols)
		parseExperimentalRun(desiredAttr)

	print "\nBefore running generateResultsCSV.py, open "+optCombinedResultsDir+os.sep+"all-runs.csv using a spreadsheet application and sort by:"
	print "1. Platform"
	print "2. Experiment"
	print "3. Task"
	print "4. xValLabel"
	print "5. Instance\n"
	print "Make sure you save the above as a CSV file without quotation marks."


if __name__ == "__main__":
	main()
