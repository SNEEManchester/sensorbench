#!/usr/bin/python
import os, sys, networkLib, math, getopt, UtilLib

optScenarioDir = "scenarios"
pathSeperator = os.sep
#NOTE: For mica2 radio range is 60m, for micaz radio range is 15m!!!

nSizes = [9, 25, 100]
optNumInstances = 10
nSourcesPercent = [20, 40, 60, 80, 100]
nDensities = [1, 2, 3, 8]
#nLayouts = ['line', 'grid', 'rand']

(universalExtent, eastExtent, westExtent) = ('SeaDefence', 'SeaDefenceEast', 'SeaDefenceWest')


def parseArgs(args):	
	global optScenarioDir, optNumInstances
	try:
		optNames = ["scenario-dir=", "num-instances="]
	
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
		elif (o == "--num-instances"):
			optNumInstances = int(a)
		else:
			usage()
			sys.exit(2)


def usage():
		print "generate-scenarios.py --scenario-dir=<dir> --num-instances=<int>"

def check_dir(d):
	if not os.path.exists(d):
		os.makedirs(d)

def generateScenarios():
	global optScenarioDir, pathSeperator

	check_dir(optScenarioDir)
	scenarioDir = optScenarioDir + pathSeperator

	for nSize in nSizes:
		for nDensity in nDensities:
			for instance in range(1,optNumInstances+1):
				#create random layout
				(sneeTopFname,avroraTopFname)=networkLib.getTopologyFilenames(scenarioDir,nSize,"random",nDensity, instance)
				allConnected = False
				retries = 0
				while (not allConnected) and (retries < 100):
					field = networkLib.generateConnectedRandomTopology(instance, numNodes = nSize, rValue = nDensity, radioRange = 15, sinkAtCenter = False, sinkAtOrigin = True)
					#field.trimEdgesRandomlyToMeetAverageDegree(6) #TODO: unhardcode this
					allConnected = field.hasAllNodesConnected()
					retries += 1
					if not allConnected:
						print "ERROR: giving up on random topology for n=%d, rval=%d" % (nSize, nDensity)
					else:    
						field.generateTopFile(avroraTopFname) # avrora topology file
						field.generateSneeqlNetFile(sneeTopFname) # snee topology file
						for nSourcePercent in nSourcesPercent:
							physSchemaFname = networkLib.getPhysicalSchemaFilename(scenarioDir,nSize,"random",nDensity,nSourcePercent, instance)
							networkLib.generatePhysicalSchema(nSize, nSourcePercent, universalExtent, eastExtent, westExtent, sneeTopFname, physSchemaFname) #snee physical Schema

			#create linear layout
			for instance in range(1,optNumInstances):
				(sneeTopFname,avroraTopFname)=networkLib.getTopologyFilenames(scenarioDir,nSize,"linear",nDensity, instance)
				field = networkLib.generateLinearTopology(instance, numNodes = nSize, radioRange = 15, rValue = nDensity)
				field.generateTopFile(avroraTopFname)
				field.generateSneeqlNetFile(sneeTopFname)
				for nSourcePercent in nSourcesPercent:
					physSchemaFname = networkLib.getPhysicalSchemaFilename(scenarioDir,nSize,"linear",nDensity,nSourcePercent, instance)
					networkLib.generatePhysicalSchema(nSize, nSourcePercent, universalExtent, eastExtent, westExtent, sneeTopFname, physSchemaFname)

			#create grid layout
			for instance in range(1,optNumInstances):
				(sneeTopFname,avroraTopFname)=networkLib.getTopologyFilenames(scenarioDir,nSize,"grid",nDensity, instance)
				numNodesX = int(math.sqrt(nSize))
				numNodesY = numNodesX 
				field = networkLib.generateGridTopology(instance, numNodesX = numNodesX, numNodesY = numNodesY, radioRange = 15, rValue = nDensity)
				field.generateTopFile(avroraTopFname)
				field.generateSneeqlNetFile(sneeTopFname)
				for nSourcePercent in nSourcesPercent:
					physSchemaFname = networkLib.getPhysicalSchemaFilename(scenarioDir,nSize,"grid",nDensity,nSourcePercent, instance)
					networkLib.generatePhysicalSchema(nSize, nSourcePercent, universalExtent, eastExtent, westExtent, sneeTopFname, physSchemaFname)

def main(): 	
	global optScenarioDir

  #parse the command-line arguments
	parseArgs(sys.argv[1:]) 
	generateScenarios()
  


if __name__ == "__main__":
	main()
            
