
CSV_DIR = "csv/"
DELIVERY_RATE_COL = 27
OUTPUT_RATE_COL = 26
SUM_6M_ENERGY_COL = 29
FRESHNESS_COL = 25
LIFETIME_COL = 36

def moveData():
	global CSV_DIR, DELIVERY_RATE_COL, OUTPUT_RATE_COL, SUM_6M_ENERGY_COL, FRESHNESS_COL, LIFETIME_COL
	sneeDataRawDELIVERY = []
	sneeDataAggDELIVERY = []
	MHOSCDataDELIVERY = []
	OD1DataDELIVERY = []
	OD2DataDELIVERY = []
	OD3DataDELIVERY = []
	LRDataDELIVERY = []
	sneeDataRawOUTPUT = []
	sneeDataAggOUTPUT = []
	MHOSCDataOUTPUT = []
	OD1DataOUTPUT = []
	OD2DataOUTPUT = []
	OD3DataOUTPUT = []
	LRDataOUTPUT = []
	sneeDataRawSUM = []
	sneeDataAggSUM = []
	MHOSCDataSUM = []
	OD1DataSUM = []
	OD2DataSUM = []
	OD3DataSUM = []
	LRDataSUM = []
	sneeDataRawFRESHNESS = []
	sneeDataAggFRESHNESS = []
	MHOSCDataFRESHNESS = []
	OD1DataFRESHNESS = []
	OD2DataFRESHNESS = []
	OD3DataFRESHNESS = []
	LRDataFRESHNESS = []
	sneeDataRawLIFETIME = []
	sneeDataAggLIFETIME = []
	MHOSCDataLIFETIME = []
	OD1DataLIFETIME = []
	OD2DataLIFETIME = []
	OD3DataLIFETIME = []
	LRDataLIFETIME = []

	SNEEin = open(CSV_DIR + "exp2a-INSNEE-results-avg.csv", "r")
	MHOSCin = open(CSV_DIR + "exp2a-MHOSC-results-avg.csv", "r")
	
	#readin snee results
	columnLine = True
	sneeRaw = 1
	for line in SNEEin:
		if(columnLine):
			columnLine = False
		else:
			bits = line.split(",")
			if(sneeRaw <= 3):
				sneeDataRawDELIVERY.append(bits[DELIVERY_RATE_COL])
				sneeDataRawOUTPUT.append(bits[OUTPUT_RATE_COL])
				sneeDataRawSUM.append(bits[SUM_6M_ENERGY_COL])
				sneeDataRawFRESHNESS.append(bits[FRESHNESS_COL])
				sneeDataRawLIFETIME.append(bits[LIFETIME_COL])
			else:
				sneeDataAggDELIVERY.append(bits[DELIVERY_RATE_COL])
				sneeDataAggOUTPUT.append(bits[OUTPUT_RATE_COL])
				sneeDataAggSUM.append(bits[SUM_6M_ENERGY_COL])
				sneeDataAggFRESHNESS.append(bits[FRESHNESS_COL])
				sneeDataAggLIFETIME.append(bits[LIFETIME_COL])
			sneeRaw= sneeRaw + 1
	SNEEin.close()
	
	#readin mhosc results
	columnLine = True
	for line in MHOSCin:
		if(columnLine):
			columnLine = False
		else:
			bits = line.split(",")
			MHOSCDataDELIVERY.append(bits[DELIVERY_RATE_COL])
			MHOSCDataOUTPUT.append(bits[OUTPUT_RATE_COL])
			MHOSCDataSUM.append(bits[SUM_6M_ENERGY_COL])
			MHOSCDataFRESHNESS.append(bits[FRESHNESS_COL])
			MHOSCDataLIFETIME.append(bits[LIFETIME_COL])
	MHOSCin.close()

	#readin OD1 results

	#readin OD2 results

	#readin OD3 results

	#readin LR results


	#outputResults
	outDelivery = open(CSV_DIR + "exp2a-Delivery.data", "w")
	outOutput = open(CSV_DIR + "exp2a-Output.data", "w")
	outSum = open(CSV_DIR + "exp2a-Sum.data", "w")
	outFresh = open(CSV_DIR + "exp2a-Freshness.data", "w")
	outLifetime = open(CSV_DIR + "exp2a-Lifetime.data", "w")

	for index in range(3):
		#all need to be expanded to include OD and LR when braught in
		outDelivery.write(str(index+1) + " " + sneeDataRawDELIVERY[index] + " " + sneeDataAggDELIVERY[index] + " " + MHOSCDataDELIVERY[index] + " \n")
		outOutput.write(str(index+1) + " " + sneeDataRawOUTPUT[index] + " " + sneeDataAggOUTPUT[index] + " " + MHOSCDataOUTPUT[index] + " \n")
		outSum.write(str(index+1) + " " + sneeDataRawSUM[index] + " " + sneeDataAggSUM[index] + " " + MHOSCDataSUM[index] + " \n")
		outFresh.write(str(index+1) + " " + sneeDataRawFRESHNESS[index] + " " + sneeDataAggFRESHNESS[index] + " " + MHOSCDataFRESHNESS[index] + " \n")
		outLifetime.write(str(index+1) + " " + sneeDataRawLIFETIME[index] + " " + sneeDataAggLIFETIME[index] + " " + MHOSCDataLIFETIME[index] + " \n")
	outDelivery.close()
	outOutput.close()
	outSum.close()
	outFresh.close()
	outLifetime.close()

def main(): 	
	moveData()

if __name__ == "__main__":
	main()

