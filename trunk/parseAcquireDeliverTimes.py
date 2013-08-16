#!/usr/bin/python
import re, fileinput, datetime


def initVars():
	return (-1, -1, -1, {}, {})

def doComputeStats(id,n,m,aqRate,bufferingFactor, acqTupleCount, delTupleCount, tdelta_sum, acquireTimes, deliverTimes):
	#print "A"

	if (id,n,m) in acquireTimes:
		acqTupleCount += 1
		tacq = acquireTimes[(id,n,m)]

		#print "B"

		if (id,n) in deliverTimes:
			tdel = deliverTimes[(id,n)]
			tdelta = tdel - tacq

			#needed for cases of duplicate tuples, when first set are not delivered,
			#then second set when delivered seem to take a really long time!
			#TODO: Think about threshold!!
			if tdelta.seconds > (int(aqRate)*int(bufferingFactor)+1):
				print "doh "+str(tdelta.seconds)
				return (acqTupleCount, delTupleCount)

			#print "C"
			delTupleCount += 1
			tdelta_sum += tdelta
			#print "%d,%d,%d,%s,%s,%s" % (id, n, m, str(tacq), str(tdel), str(tdelta))

	return (acqTupleCount, delTupleCount, tdelta_sum)

def computeStats(aqRate,bufferingFactor, acquireTimes, deliverTimes, MAX_ID, MAX_N, MAX_M, deliverTupleAtATime):
	(acqTupleCount, delTupleCount, tdelta_sum) = (0, 0, datetime.timedelta(0))

	for id in range(0,MAX_ID+1):
		#print id
		for n in range(0,MAX_N+1):
			if (deliverTupleAtATime):
				(acqTupleCount, delTupleCount, tdelta_sum) = doComputeStats(id,n,None,aqRate,bufferingFactor,acqTupleCount, delTupleCount, tdelta_sum, acquireTimes, deliverTimes)
			else:
				for m in range(0,MAX_M+1):
					(acqTupleCount, delTupleCount, tdelta_sum) = doComputeStats(id,n,m,aqRate,bufferingFactor,acqTupleCount, delTupleCount, tdelta_sum, acquireTimes, deliverTimes)

	return (acqTupleCount, delTupleCount, tdelta_sum)


def getRegEx(deliverTupleAtATime):
	if deliverTupleAtATime:
		acquireRegEx = "\d+\s+(\d+):(\d+):(\d+).(\d+)\s+ACQUIRE\(id=(\d+),ep=(\d+)"
		deliverRegEx = "\d+\s+(\d+):(\d+):(\d+).(\d+)\s+DELIVER\(id=(\d+),ep=(\d+)"
	else:
		acquireRegEx = "\d+\s+(\d+):(\d+):(\d+).(\d+)\s+ACQUIRE\(id=(\d+),n=(\d+),m=(\d),"
		deliverRegEx = "\d+\s+(\d+):(\d+):(\d+).(\d+)\s+DELIVER\(id=(\d+),n=(\d+)"
	return (acquireRegEx, deliverRegEx)

def parseFile(avrorafile, acquireTimes, deliverTimes, MAX_ID, MAX_N, MAX_M, deliverTupleAtATime):

	(acquireRegEx, deliverRegEx) = getRegEx(deliverTupleAtATime)
	
	inFile =  open(avrorafile)
	while 1:
		line = inFile.readline()
		if not line:
			return (MAX_ID, MAX_N, MAX_M);
		m = re.search(acquireRegEx, line)
		if (m != None):
			hours = int(m.group(1))
			minutes = int(m.group(2))
			seconds = int(m.group(3))
			microseconds = int(m.group(4))
			id = int(m.group(5))
			n = int(m.group(6))
			if (not deliverTupleAtATime):
				m = int(m.group(7))
			else:
				m = None
			t = datetime.datetime(1970,1,1,hours,minutes,seconds,microseconds)

			#first time only
			if not (id,n,m) in acquireTimes:
				acquireTimes[(id,n,m)]=t
			else:
				print "IGNORING DUPLICATE acquired tuple: t=%s,id=%d,n=%d,m=%d" % (str(t), id, n, m)

			if (id > MAX_ID):
				MAX_ID = id
			if (n > MAX_N):
				MAX_N = n
			if (not deliverTupleAtATime):	
				if (m > MAX_M):
					MAX_M = m	
			
		m = re.search(deliverRegEx, line)
		if (m != None):
			hours = int(m.group(1))
			minutes = int(m.group(2))
			seconds = int(m.group(3))
			microseconds = int(m.group(4))
			id = int(m.group(5))
			n = int(m.group(6))
			t = datetime.datetime(1970,1,1,hours,minutes,seconds,microseconds)

			#first time only
			if not (id,n) in deliverTimes:
				deliverTimes[(id,n)]=t


#avroraOutputFile
#aqRate in seconds
#bufferingFactor
#simulationDuration in seconds
#Example invocation:
#        parse("mhosc_1024_5_cprintstr_example-output_no-top.txt",1,5,200)

def parse2(avroraOutputFile,aqRate,bufferingFactor,simulationDuration,deliverTupleAtATime):

       	(MAX_ID, MAX_N, MAX_M, acquireTimes, deliverTimes) = initVars()
	(MAX_ID, MAX_N, MAX_M) = parseFile(avroraOutputFile, acquireTimes, deliverTimes, MAX_ID, MAX_N, MAX_M,deliverTupleAtATime)
	(acqTupleCount, delTupleCount, tdelta_sum) = computeStats(aqRate,bufferingFactor, acquireTimes, deliverTimes, MAX_ID, MAX_N, MAX_M,deliverTupleAtATime)
	
	print "tdelta sum="+str(tdelta_sum)
	print "tdelta average (data freshness)="+str(tdelta_sum/delTupleCount)
	print "num tuples acquired="+str(acqTupleCount)
	print "num tuples delivered="+str(delTupleCount)
	print "output rate (tuples/s)="+str(float(delTupleCount)/simulationDuration)
	print "delivery rate="+str(float(delTupleCount)/float(acqTupleCount))	

def parse(avroraOutputFile, runAttr, deliverTupleAtATime):

	(MAX_ID, MAX_N, MAX_M, acquireTimes, deliverTimes) = initVars()
	aqRate = int(runAttr["AcquisitionRate"])
	bufferingFactor = runAttr["BufferingFactor"]
	simulationDuration = runAttr["SimulationDuration"]
	
	(MAX_ID, MAX_N, MAX_M) = parseFile(avroraOutputFile, acquireTimes, deliverTimes, MAX_ID, MAX_N, MAX_M, deliverTupleAtATime)
	(acqTupleCount, delTupleCount, tdelta_sum) = computeStats(aqRate,bufferingFactor, acquireTimes, deliverTimes, MAX_ID, MAX_N, MAX_M, deliverTupleAtATime)

	print "delTupleCount=" + str(delTupleCount)

	runAttr["Tuple Acq Count"] = acqTupleCount
	runAttr["Tuple Del Count"] = delTupleCount
	runAttr["Tuple Delta Sum"] = tdelta_sum.seconds
	if (delTupleCount>0):
		runAttr["Data Freshness"] = tdelta_sum.seconds/delTupleCount #tuple delta avg	
	else:
		runAttr["Data Freshness"] = 0 # No tuples delivered
	runAttr["Output Rate"] = float(delTupleCount)/float(simulationDuration) #tuples/s
	if (acqTupleCount>0):
		runAttr["Delivery Rate"] = float(delTupleCount)/float(acqTupleCount)
	else:
		runAttr["Delivery Rate"] = 0 # No tuples acquired

def testMHOSCFile():	
	avroraOutputFile = "MHOSC-exp0a-x1-avrora-log.txt"
	
	aqRate = 1
	bufferingFactor = 5
	simulationDuration = 50

	deliverTupleAtATime = False

	print "Testing MHOSC file: "+avroraOutputFile
	parse2(avroraOutputFile, aqRate, bufferingFactor, simulationDuration, deliverTupleAtATime)


def testSNEEFile():	
	avroraOutputFile = "snee-avrora-sample-output.txt"
	
	aqRate = 25
	bufferingFactor = 1
	simulationDuration = 100

	deliverTupleAtATime = True

	print "Testing SNEE file: "+avroraOutputFile
	parse2(avroraOutputFile, aqRate, bufferingFactor, simulationDuration, deliverTupleAtATime)

if __name__ == "__main__":
	#testMHOSCFile()
	testSNEEFile()
