#!/usr/bin/python
import random, sys, array, math, os.path, UtilLib

#network library 
#generates avrora network topologies (co-ordinate-based), random or grid (TODO)
#converts avrora topology to QoS weighted network connectivity graph with edges representing energy and time between nodes
#(energy is computed by applying the freespace model

optFreq = 432969975					#Default frequency for Avrora Mica2 radio NEED THIS FOR MICAZ
optMinRXPower = 0.000009				#This is the minimum receive power at which packets can be received
lightConst = math.pow(299792458 / (4 * math.pi),2)	#Constant used by freespace model

logger = None
			
#Registers a logger for this library
def registerLogger(l):
 	global logger
 	logger = l


#Ouput info message to screen and logger if applicable
def report(message):
 	if (logger != None):
 		logger.info (message)
 	#print message


#Ouput warning message to screen and logger if applicable
def reportWarning(message):
 	if (logger != None):
 		logger.warning(message)
 	#print message


#Ouput error message to screen and logger if applicable
def reportError(message):
 	if (logger != None):
 		logger.error(message)
 	#print message

#Object representing a sensor network node
class Node(object):
    
	def __init__(self, id, xPos, yPos):
		self.id = id
        	self.xPos = xPos
        	self.yPos = yPos
        	
        #Returns the distance to another node
        def getDistanceApart(self, otherNode):
        	xDelta = self.xPos - otherNode.xPos
        	yDelta = self.yPos - otherNode.yPos
        	dist = math.sqrt(math.pow(xDelta,2) + math.pow(yDelta,2))
        	return dist	
        
        
#Object representing a sensor network field
class Field(object):
		
	def __init__(self, xDim, yDim, xOrigin, yOrigin, seed, edgesNeeded = []):
		random.seed(seed)
		self.xDim = xDim
		self.yDim = yDim
		self.xOrigin = xOrigin
		self.yOrigin = yOrigin
		#Stores nodeid at each cell (initialized to None)
		self.cells = []
		for i in range(0, xDim):
			self.cells.append([None] * yDim)
		#maps node id to node object
		self.nodes = {}
		self.edges = None
		self.edgesNeeded = edgesNeeded #the edges that are essential

	def addNode(self, i, x, y):
		self.cells[x][y] = i
		n = Node(i, x, y)
		self.nodes[i] = n
		self.edges = None

	def addNodeAtRandomLocation(self, i):
		added = False
		while (added == False):		
			x = random.randrange(0, self.xDim)
			y = random.randrange(0, self.yDim)
			if (self.cells[x][y] == None):
				#report("Node %d situated at cell %d,%d" % (i, x, y))
				self.addNode(i, x, y)
				added = True
			#else:
				#report("Attempting to situate Node %d, Cell %d,%d is not free, retrying" % (i, x, y))

	def removeNode(self, i):
		(x, y) = (self.nodes[i].xPos, self.nodes[i].yPos)  
		self.cells[x][y] = None
		del self.nodes[i]
		self.edges = None
		
	def generateTopFile(self, fname):
		outFile = open(fname, 'w')
		outFile.writelines("""
# simple topology specification
#
# syntax: nodeName x y z
# nodeName: any string without space
# coordinates: integer values,
# one line per node
# negative coordinates are welcome
""")
		for i in range(0, len(self.nodes.keys())):
			n = self.nodes.get(i)
			outFile.writelines("node%d %d %d %d\n" % (i, n.xPos, n.yPos, 0))
		outFile.close()

	def getDistance(self, senderID, receiverID):
		sender = self.nodes.get(senderID)
		receiver = self.nodes.get(receiverID)
		dist = sender.getDistanceApart(receiver)
		return dist	


	# Returns the tx power required for two nodes to communcate with each other
	# This is computed using the freespace radio model
	# txPower = (minRXPower * freq^2 * dist^2) / lightConst
	def getTXPower(self, senderID, receiverID):
		dist = self.getDistance(senderID, receiverID)
		txPower = (optMinRXPower * optFreq * optFreq * dist * dist) / lightConst
		return txPower


	#Gives the Tx power setting for communication between two given nodes in the network
	#Note: This converts power in Watts to a power setting for CC1000 (0-255); if out of range returns -1
	def getTXPowerSetting(self, senderID, receiverID):
	
		minTxPower = self.getTXPower(senderID, receiverID)
		dist = self.getDistance(senderID, receiverID)
	
		#print "sender=%d receiver=%d distance apart=%gm tx power (W)=%g" % (senderID, receiverID, dist, minTxPower)
		
		if (dist>15): #WARNING! Hard coded value!!!
			return -1
		else:
			return 255

#		if (dist==0):
#			return 1
#		tmp1 = math.ceil((math.log(minTxPower, 10) + 1.8) / 0.12)
#		tmp2 = math.ceil((math.log(minTxPower, 10) + 0.06459) / 0.00431)
#		txPowerSetting = max(1, tmp1, tmp2)
#			
#		if (txPowerSetting>255): #TODO: unhardcode this
#			return -1;
#		else:
#			return txPowerSetting


	def removeEdge(self, i, j):
		del self.edges[i][j]
		del self.edges[j][i]
	
	def edgeNeeded(self, i, j):
		if self.edgesNeeded == []:
			return True
		else:
			v1 = str(i)+':'+str(j)
			v2 = str(j)+':'+str(i)
			return (v1 in self.edgesNeeded or v2 in self.edgesNeeded)
	
	def updateEdges(self):
		if self.edges == None:	
			numNodes = len(self.nodes.keys())
			self.edges = []
			for i in range(0, numNodes):
				self.edges.append({})


			for i in range(0,numNodes):
				for j in range(0,numNodes):
					if (i>=j):
						continue
					powerSetting = self.getTXPowerSetting(i,j)		
					if powerSetting > -1 and self.edgeNeeded(i,j):
						self.edges[i][j] = powerSetting
						self.edges[j][i] = powerSetting

			# print self.edges

	
	#Trims n random edges in the network graph
	#Will not cause graph to become disconnected
	def trimEdgesRandomly(self, numToTrim):
		numNodes = len(self.nodes.keys())

		for n in range(0, numToTrim):
			self.updateEdges()

			i = random.randrange(0, numNodes, 1)

			#Leave at least one edge per node
			if len(self.edges[i].keys()) > 1:
				tmp = random.randrange(1, len(self.edges[i].keys()), 1)
				j = self.edges[i].keys()[tmp]
				
				if len(self.edges[j].keys()) > 1:
					self.removeEdge(i, j)
		
	
	#Trims random edges in the network graph until the average edge degree is above a certain threshold
	def trimEdgesRandomlyToMeetAverageDegree(self, targetEdgeDegree):
		numNodes = len(self.nodes.keys())
		
		#Trim 10% of the edges until averageNodeDegree <= targetEdgeDegree
		while self.getAverageNodeDegree() > targetEdgeDegree:
			numToTrim = int(self.getAverageNodeDegree() * numNodes * 0.1)
			report("About to randomly trim %d edges" % numToTrim)
			self.trimEdgesRandomly(numToTrim)
		
	
	#Trims edges above a certain power setting threshold
	#May cause graph to become disconnected
	def trimEdgesAboveThreshold(self, thresh):
		self.updateEdges()
		
		for i in range(0, numNodes):
			for j in self.edges.keys():
				if self.edges > thresh:
					self.removeEdge(i, j)

	def nodeConnected(self, i):
		self.updateEdges()
		if len(self.edges[i].keys()) == 0:
			return False
		else:
			return True

		
	#Checks whether a sensor node is connected
	def hasAllNodesConnected(self):
		self.updateEdges()
		allConnected = True
		numNodes = len(self.nodes.keys())

		for i in range(0,numNodes):
				connected = self.nodeConnected(i)	
			
				if not connected:
					reportWarning("Node %d is disconnected from the network" % (i))
					allConnected = False
					break
			
		return connected

	#Computes the node degree average (i,e., number of radio links per node)			
	def getAverageNodeDegree(self):
		self.updateEdges()
		numNodes = len(self.nodes.keys())
		nodeDegreeTotal = 0

		for i in range(0,numNodes):
			nodeDegreeTotal += len(self.edges[i].keys())
					
		return float(nodeDegreeTotal/numNodes)
		
		
	
	#Creates a file with network in Sneeql QoS-aware format (with energy/latency associated with each radio link)
	def generateSneeqlNetFile(self, fname):
		self.updateEdges()
	
		outFile = open(fname, 'w')
#TODO: review units in XML QoS top file -- they are not really applicable now
#TODO: review need for radio-loss attribute in XML QoS top file
		outFile.writelines("""<?xml version="1.0"?>

<network-topology
xmlns="http://snee.cs.manchester.ac.uk"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xsi:schemaLocation="http://snee.cs.manchester.ac.uk network-topology.xsd">

<units>
	<energy>MILLIJOULES</energy>
	<memory>BYTES</memory>
	<time>MILLISECONDS</time>
</units>

<radio-links>
""")
		numNodes = len(self.nodes.keys())
		for i in range(0,numNodes):
			connected = False
			for j in range(i,numNodes):
				if (i>=j):
					continue

				if self.edges[i].has_key(j):					
					txPowerSetting = self.edges[i][j]
					dist = self.getDistance(i, j)
					line = "\t<radio-link source=\"%d\" dest=\"%d\" bidirectional=\"true\" energy=\"%d\" time=\"%d\" radio-loss=\"0\"/>\n"
					outFile.writelines(line % (i, j, txPowerSetting, dist))

		outFile.writelines("""
</radio-links>
		
</network-topology>			
""")
	 	outFile.close()


	#Creates file with network in Tossim format (showing connectivity between nodes only)
	def generateTossimNetFile(self, fname):
		self.updateEdges()
	
		outFile = open(fname, 'w')	
		numNodes = len(self.nodes.keys())
		for i in range(0,numNodes):
			connected = False
			for j in range(i,numNodes):
				if (i==j):
					continue
				
				if self.edges[i].has_key(j):					
					txPowerSetting = self.edges[i][j]
					line = "%d:%d:0.0\n%d:%d:0.0\n" % (i, j, j, i)
					outFile.writelines(line)
		outFile.close()

	
	def drawNetworkGeometry(self, outputFilename):
    	
		#first generate plotFile
		outputDir = os.path.dirname(outputFilename)
		if outputDir == "":
			outputDir = os.getenv("PWD")
		
		plotFilename = "%s/plot.txt" % (outputDir)
		plotFile = open(plotFilename, 'w')
		plotFile.write("Id \"x\" \"y\"\n")
		for n in self.nodes.keys():
			id =str(self.nodes[n].id)
			x = str(self.nodes[n].xPos)
			y = str(self.nodes[n].yPos)
			plotFile.write("%s %s %s\n" % (id, x, y))
		plotFile.close()

		#now generate script file
		#TODO: unhardcode this
		gnuPlotExe = '/cygdrive/c/Program\ Files/gnuplot/bin/pgnuplot.exe'    	
		
		scriptStr = """
set term postscript eps font "Times-Bold,24" size 7,3.5
set out '%s'

set style data points
set pointsize 5
set key off
set xtics
set xrange [%d:%d]
set yrange [%d:%d]
set datafile missing '?'
linewidth 3 
plot '%s' using 2:3 ti col linewidth 3
		"""
		
		scriptStr = scriptStr % (UtilLib.winpath(outputFilename), self.xOrigin, self.xOrigin+self.xDim, self.yOrigin, self.yOrigin+self.yDim, UtilLib.winpath(plotFilename))

		scriptFilename = "%s/gnu-plot-script.txt" % (outputDir)
		scriptFile = scriptFilename
		f = open(scriptFile,'w')	
		f.write(scriptStr)	
		f.close()

		report('running: '+gnuPlotExe+' < '+scriptFilename)
		exitVal = os.system(gnuPlotExe+' < '+scriptFilename)
		if (exitVal!=0):
			reportWarning('Error during graph plotting')	



		
#Creates a random topology
def generateRandomTopology(seed, numNodes = 10, xDim = 100, yDim = 100, xOrigin = 0, yOrigin = 0, sinkAtCenter = False, sinkAtOrigin = True):
	
	if (xDim*yDim < numNodes):
		sys.exit(-2); #TODO: no room

	field = Field(xDim, yDim, xOrigin, yOrigin)

	if (sinkAtCenter and sinkAtOrigin):
		print "Error - sink cannot be both at center and at origin"

	startNode = 0
	#place the sink at the center of the sensing field, if requested
	if sinkAtCenter:
		x = int((xOrigin + xDim) / 2)
		y = int((yOrigin + yDim) / 2)
		report("Sink node situated at cell %d,%d" % (x, y))
		field.addNode(0, x, y)
		startNode = 1

	if sinkAtOrigin:
		field.addNode(0, xOrigin, yOrigin)
		startNode = 1

	for i in range(startNode,numNodes):
		field.addNodeAtRandomLocation(i, seed)

	return field


def generateRandomTopology2(numNodes = 10, rValue = 3, radioRange = 60, sinkAtCenter = False, sinkAtOrigin = True):
	gap = radioRange / rValue
	x = gap * int(numNodes/2) + 1
	y = x
	#print "Dimensions of field are %d x %d" % (x, y)
	
	return generateRandomTopology(numNodes, xDim = x, yDim = y, xOrigin = 0, yOrigin = 0, sinkAtCenter = False, sinkAtOrigin = True)

def generateConnectedRandomTopology(seed, numNodes = 10, rValue = 3, radioRange = 60, sinkAtCenter = False, sinkAtOrigin = True):
	gap = radioRange / rValue
	xDim = gap * int(numNodes/2) + 1
	yDim = xDim

	xOrigin = 0
	yOrigin = 0

	if (xDim*yDim < numNodes):
		sys.exit(-2); #TODO: no room

	field = Field(xDim, yDim, xOrigin, yOrigin, seed)

	if (sinkAtCenter and sinkAtOrigin):
		print "Error - sink cannot be both at center and at origin"

	#place the sink
	if sinkAtCenter:
		x = int((xOrigin + xDim) / 2)
		y = int((yOrigin + yDim) / 2)
		report("Sink node situated at cell %d,%d" % (x, y))
		field.addNode(0, x, y)
	elif sinkAtOrigin:
		field.addNode(0, xOrigin, yOrigin)
	else:
		field.addNodeAtRandomLocation(0)

	for i in range(1,numNodes):
		field.addNodeAtRandomLocation(i)
       		while not field.nodeConnected(i):
			field.removeNode(i)
			field.addNodeAtRandomLocation(i)
	return field

def generateLinearTopology(seed, numNodes = 10, radioRange = 60, rValue = 3):
	gap = radioRange / rValue
	print gap
	xDim = gap * numNodes + 1
	yDim = 1

	field = Field(xDim, yDim, 0, 0, seed)

	for i in range(0,numNodes):
		x = (i*gap)
		y = 0
		field.addNode(i, x, y)
	
	return field


def generateGridTopology(seed, numNodesX = 3, numNodesY = 3, radioRange = 60, rValue = 3):
	gap = radioRange / rValue
	xDim = gap * numNodesX + 1
	yDim = gap * numNodesY + 1

	field = Field(xDim, yDim, 0, 0, seed)
	
	for i in range(0,numNodesX):
		for j in range(0,numNodesY):
			x = (i*gap)
			y = (j*gap)
			id = (j*numNodesY) + i
			field.addNode(id, x, y)
	return field


#Reads in a coordinate file and returns the corresponding field object	
#Peforms a valdility check that all nodes are within field dimensions
def parseAvroraTopFile(inputFile, xDim, yDim, xOrigin = 0, yOrigin = 0, rtFiles = None):
	
	edgesNeeded = []
	if rtFiles!=None:
		for rtFile in rtFiles.split(','):
			rtF = open(rtFile, 'r')
			while 1:
				line = rtF.readline()
				if not line:
					break
				if line.strip() == "":
					continue				
				edgesNeeded.append(line.strip())
	
	field = Field(xDim, yDim, xOrigin, yOrigin, edgesNeeded)

	inFile = open(inputFile, 'r')
	while 1:
		line = inFile.readline()
		if not line:
			break

		if line.strip().startswith("#") or line.strip() == "":
			continue
			
		#print "line=" + line
		tmp = line.split()
		i = int(tmp[0].replace("node",""))
		x = int(tmp[1])
		y = int(tmp[2])
		
		if x >= xOrigin and x <= xOrigin+xDim and y >= yOrigin and y <= yOrigin+yDim:
			field.addNode(i, x, y)
		else:
			reportError("Node %d at location (%d,%d) is outside sensor field dimensions" % (i, x, y))
			sys.exit(2)

	return field

def generatePhysicalSchema(numNodes, percentSources, universalExtent, eastExtent, westExtent, topologyFname, fname):
    numSources = int(math.ceil(float(numNodes)*(percentSources/100.0)))
    nodes = range(0,numNodes)
    sourceNodes = sorted(random.sample(nodes, numSources))
    eastSourceNodes = sorted(random.sample(sourceNodes, (numSources / 2)))
    westSourceNodes = sorted(list(set(sourceNodes) - set(eastSourceNodes)))

    #print "sourceNodes = %s, eastSourceNodes = %s, westSourceNodes = %s" % (sourceNodes, eastSourceNodes, westSourceNodes)

    sourceNodeStr = ",".join(map(str,sourceNodes))
    eastSourceNodeStr = ",".join(map(str,eastSourceNodes))
    westSourceNodeStr = ",".join(map(str,westSourceNodes))    

    schemaStr = """<?xml version="1.0" encoding="UTF-8"?>
<source xmlns="http://snee.cs.man.ac.uk/namespace/physical-schema"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://snee.cs.man.ac.uk/namespace/physical-schema ../schema/physical-schema.xsd ">

	<sensor_network name="wsn1">
		<topology>etc/%s</topology>
		<site-resources>etc/inqp-telosb.xml</site-resources>
		<gateways>0</gateways>
		<extents>
			<extent name="SeaDefence">
				<sites>%s</sites>
				<sensorTypes>
					<attribute name="seaLevel" sensorType="seaLevel"/>
					<attribute name="voltage" sensorType="voltage"/>		
				</sensorTypes>						
			</extent>
 			<extent name="SeaDefenceEast">
				<sites>%s</sites>
				<sensorTypes>
					<attribute name="seaLevel" sensorType="seaLevel"/>
					<attribute name="voltage" sensorType="voltage"/>		
				</sensorTypes>						
			</extent>
			<extent name="SeaDefenceWest">
				<sites>%s</sites>
				<sensorTypes>
					<attribute name="seaLevel" sensorType="seaLevel"/>
					<attribute name="voltage" sensorType="voltage"/>		
				</sensorTypes>				
			</extent>
		</extents>
	</sensor_network>

</source>
""" % (topologyFname, sourceNodeStr, eastSourceNodeStr, westSourceNodeStr)

    outFile = open(fname, 'w')
    outFile.writelines(schemaStr)
    outFile.close()

def getPhysicalSchemaFilename(nSize,nType,nDensity,nSourcePercent,instanceValue):
	physSchemaFname = "n%d_%s_d%d_s%d_%d_physical_schema.xml" % (nSize,nType,nDensity,nSourcePercent,instanceValue)
	return physSchemaFname

def getTopologyFilenames(nSize,nType,nDensity,instanceValue):
	sneeTopFname = "n%d_%s_d%d_%d_topology.xml" % (nSize,nType,nDensity,instanceValue)
	avroraTopFname = "n%d_%s_%d_%d.top" % (nSize,nType,nDensity,instanceValue)
	return (sneeTopFname,avroraTopFname)
	
def testLinearTopologyGenerator():
	field = generateLinearTopology(9, 60, 3)
       	field.generateTopFile("linear.top")
	if field.hasAllNodesConnected():
		print "SUCCESS: Network generated has all nodes connected"
	else:
		print "WARNING: Network generated contains disconnected nodes"
	field.generateSneeqlNetFile("linear.xml")

	
def testGridTopologyGenerator():
	field = generateGridTopology(3, 3, 60, 1)
       	field.generateTopFile("grid.top")
	if field.hasAllNodesConnected():
		print "SUCCESS: Network generated has all nodes connected"
	else:
		print "WARNING: Network generated contains disconnected nodes"
	field.generateSneeqlNetFile("grid.xml")

def testRandomTopologyGenerator():
	field = generateRandomTopology(numNodes = 100, xDim= 15, yDim = 15)
	field.trimEdgesRandomlyToMeetAverageDegree(6) #TODO: unhardcode this	
	field.generateTopFile("test.top")
	field.generateSneeqlNetFile("test.xml")
	field.generateTossimNetFile("test.nss")

	if field.hasAllNodesConnected():
		print "SUCCESS: Network generated has all nodes connected"
	else:
		print "WARNING: Network generated contains disconnected nodes"
	print "INFO: The average node degree is " + str(field.getAverageNodeDegree())

	
	field.trimEdgesRandomlyToMeetAverageDegree(6)
	print field.edges


def testRandomTopologyGenerator2():
	allConnected = False

	while not allConnected:
		field = generateRandomTopology2(numNodes = 10, rValue = 1, radioRange = 60, sinkAtCenter = False, sinkAtOrigin = True)
		field.trimEdgesRandomlyToMeetAverageDegree(6) #TODO: unhardcode this	
		field.generateTopFile("rand2.top")
		field.generateSneeqlNetFile("rand2.xml")

		allConnected = field.hasAllNodesConnected()
		if allConnected:
			print "SUCCESS: Network generated has all nodes connected"
		else:
			print "WARNING: Network generated contains disconnected nodes"
		print "INFO: The average node degree is " + str(field.getAverageNodeDegree())

		field.trimEdgesRandomlyToMeetAverageDegree(6)
		print field.edges
	
def testGeneratePhysicalSchema():
	numNodes = 10
	percentSources = 80
	universalExtent = "SeaDefence"
	eastExtent = "SeaDefenceEast"
	westExtent = "SeaDefenceWest"
	fname = "phys-schema.xml"
	
	generatePhysicalSchema(numNodes, percentSources, universalExtent, eastExtent, westExtent, "topology.xml", fname)
	

	
def main(): 	
	testGeneratePhysicalSchema()


if __name__ == "__main__":
	main()
	
