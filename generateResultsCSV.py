import os, sys, getopt

optCondorOutputDir = os.getcwd()

def parseArgs(args):
	global optCondorOutputDir

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


#Reread CSV produced from runExperiments


#TODO: Move this to after Condor/Avrora script
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


def main():
	global optCondorOutputDir

	#parse the command-line arguments
	parseArgs(sys.argv[1:]) 

	for filename in os.listdir(optCondorOutputDir):
		print filename	

if __name__ == "__main__":
	main()


