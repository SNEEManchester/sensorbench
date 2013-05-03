

MHOSC_BETA = 5 #Multihop Oscilloscope Buffering factor

		
def runMHOSCExperiment(task,xVals,xValLabels,xValAttr,exprAttr,runAttrCols,outputDir):
	global MHOSC_BETA

	if task != 'raw':
		return
	
	runAttr["Query"] = tasks2queries[task]
	for (x,xValLabel) in zip(xVals,xValLabels): #THis loop is now in RunExperiment !!!!!!!!!
		runAttr = initRunAttr(exprAttr, x, xValLabel, xValAttr, 'MHOSC', task)
		
		print "\n**********Experiment="+runAttr['Experiment']+" Platform=MHOSC task="+task+" x="+x + " xLabel="+xValLabel
		runAttr["BufferingFactor"] = MHOSC_BETA

		#check if equiv experiment run exists
		if (runAttr['Experiment'],'MHOSC') in equivRuns.dict:
			equivRuns.copyExperimentRunResults(runAttr, rootOutputDir)
		else:
			#2 Run osc in Avrora
			runMHOSCInAvrora(runAttr, outputDir)
	
		#3 Log the results
		logResultsToFiles(runAttr, runAttrCols, outputDir)

#PROBABLY DOESN'T GO HERE
def runMHOSCInAvrora(runAttr, outputDir):
	global MHOSC_BETA
	
	#An example avrora command string to invoke Multihop Oscilloscope
	#java avrora.Main -mcu=mts300 -platform=micaz -simulation=sensor-network -seconds=10 -monitors=leds,packet,serial,energy,c-print -ports=0:0:2390 -random-seed=1 -sensor-data=light:1:.,light:2:.,light:3:.,light:4:.,light:5:.,light:6:.,light:7:.,light:8:.,light:9:.,light:10:.,light:11:.,light:12:.,light:13:.,light:14:.,light:15:.,light:16:.,light:17:.,light:18:.,light:19:.,light:20:.,light:21:.,light:22:.,light:23:.,light:24:.,light:25:. -report-seconds -nodecount=25  mhosc_1024_5_cprint.elf > mhosc_1024_5_cprintstr_example-output_no-top.txt

	simDuration = int(runAttr["AcquisitionRate"])*MHOSC_BETA*10
	runAttr["SimulationDuration"] = simDuration
	
	networkSize = runAttr['NetworkSize']
	sensorDataString = getSensorDataString(runAttr['NetworkSize'])
	mhoscExe = "mhosc-a%s-b%d.elf" % (runAttr["AcquisitionRate"], MHOSC_BETA)
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


