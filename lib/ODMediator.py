import os, shutil, sys, re, string, AvroraLib

OD_BETA = 1 #Outlier Detection Buffering factor

def init(scenarioDir, sourceDir):
	global optScenarioDir, optSourceRootDir
	optScenarioDir = scenarioDir
	optSourceRootDir = sourceDir
	#Compile ELF binaries. Binaries are assumed to be already compiled


def cleanup():
	#Do nothing!
	print


def getODElfFilename(runAttr):
	a = runAttr['AcquisitionRate']
	b = OD_BETA
	return "od-a"+str(a)+"-b"+str(b)+".elf"

def getAvroraCommandString(runAttr, runAttrCols, avroraElfDir):
	global OD_BETA

	simDuration = int(runAttr["AcquisitionRate"])*OD_BETA*10
	runAttr["SimulationDuration"] = simDuration

	topologyStr = "-topology=static -topology-file="+runAttr['AvroraTopologyFilename']
	sensorDataString = AvroraLib.getSensorDataString(runAttr['NetworkSize'])
	nodeCountStr = runAttr['NetworkSize']
	elfString = getODElfFilename(runAttr)

	commandStr = "avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network -seconds=%d %s -monitors=leds,packet,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=%s -report-seconds -colors=false -nodecount=%d  %s" % (simDuration, topologyStr, sensorDataString, nodeCountStr, elfString)
	return commandStr


def generateAvroraJob(task,xVal,xValLabel,xValAttr,instance,runAttr,runAttrCols,rootOutputDir, runOutputDir, avroraJobsRootDir):
	global optScenarioDir, optSourceRootDir

	#3 Create AvroraJobs folder
	#create dir for Avrora Job
	avroraJobDir = avroraJobsRootDir+os.sep+runOutputDir 
	os.makedirs(avroraJobDir)
	
	#generate header files from snee RT
	generateNodeHeaderFiles(SNEEMediator.defineTempSneeFilesRootDir(), avroraJobDir)
	
  #copy correct setup file into outputFolder as D3gen.h file (this contains all the hard coded variables for OD, such as acquisition rate etc
	copyCorrectDataFilesFromStore(avroraJobDir)

	#compile bineries for OD

	#Copy top file for avrora
	avroraTopFile = optScenarioDir + os.sep + runAttr['AvroraTopologyFilename']
	shutil.copy(avroraTopFile, avroraJobDir)
			    
	#Create Avrora CommandString.txt
	avroraCommandStr = getAvroraCommandString(runAttr, runAttrCols, optSourceRootDir)
	avroraCommandStrFileName = avroraJobDir + os.sep + "avroraCommandString.txt"
	avroraCommandStrFile = open(avroraCommandStrFileName, "w")
	avroraCommandStrFile.writelines(avroraCommandStr)

def generateNodeHeaderFiles(tempSneeFolder, avroraJobDir):
	print "should generate node header files now"


def copyCorrectDataFilesFromStore(avroraJobDir):
	print "should by copying correct files from store now"
	shutil.copy(optSourceRootDir+os.sep+"elf"+os.sep+"D3AppC.nc", avroraJobDir)
	shutil.copy(optSourceRootDir+os.sep+"elf"+os.sep+"D3C.nc", avroraJobDir)
	shutil.copy(optSourceRootDir+os.sep+"elf"+os.sep+"Makefile", avroraJobDir)
	shutil.copy(optSourceRootDir+os.sep+"elf"+os.sep+"AvroraPrint.h", avroraJobDir)


#TODO: PROBABLY DOESN'T GO HERE
def runODInAvrora(runAttr, outputDir):
	global OD_BETA
	
	#An example avrora command string to invoke Multihop Oscilloscope
	#java avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network -seconds=10 -monitors=leds,packet,serial,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=light:1:.,light:2:.,light:3:.,light:4:.,light:5:.,light:6:.,light:7:.,light:8:.,light:9:.,light:10:.,light:11:.,light:12:.,light:13:.,light:14:.,light:15:.,light:16:.,light:17:.,light:18:.,light:19:.,light:20:.,light:21:.,light:22:.,light:23:.,light:24:.,light:25:. -report-seconds -nodecount=25  mhosc_1024_5_cprint.elf > mhosc_1024_5_cprintstr_example-output_no-top.txt

	simDuration = int(runAttr["AcquisitionRate"])*OD_BETA*10
	runAttr["SimulationDuration"] = simDuration
	
	networkSize = runAttr['NetworkSize']
	sensorDataString = getSensorDataString(runAttr['NetworkSize'])
	odExe = "od-a%s-b%d.elf" % (runAttr["AcquisitionRate"], OD_BETA)
	avroraLogFile = generateAvroraLogfileName(runAttr)

	topologyStr = "-topology=static -topology-file="+sneeRoot+"/etc/"+runAttr['AvroraTopologyFilename']

        #NB: no serial monitor, using cprint instead
       	commandStr = "java avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network -seconds=%d %s -monitors=leds,packet,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=%s -report-seconds -colors=false -nodecount=%d  %s > %s" % (simDuration, topologyStr, sensorDataString, networkSize, mhoscExe, avroraLogFile)

	print commandStr

	#comment out when debugging
	os.system(commandStr)
	#sys.exit()

	#get values for freshness of data, output rate
	parseAcquireDeliverTimes.parse(avroraLogFile, runAttr, False)
	
	#get values for total energy, lifetime
	parseEnergyMonitorOutput(avroraLogFile, runAttr)

	#move Avrora file out to results dir
	shutil.move(avroraLogFile,outputDir+os.sep+avroraLogFile)



