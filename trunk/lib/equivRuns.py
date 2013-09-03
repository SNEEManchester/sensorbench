import os, CSVLib

#For MHOSC, any tasks that are not 'raw' are safely ignored!
dict = {}

#INSNEE
dict[('4b','INSNEE')] = '4a'
dict[('5b','INSNEE')] = '5a'
dict[('6b','INSNEE')] = '6a'

#MHOSC
dict[('0b','MHOSC')] = '0a' #for the same xVal etc
dict[('0c','MHOSC')] = '0a'
dict[('0d','MHOSC')] = '0a'
dict[('0e','MHOSC')] = '0a'
dict[('1b','MHOSC')] = '1a'
dict[('2b','MHOSC')] = '2a'
dict[('3b','MHOSC')] = '3a'
dict[('4b','MHOSC')] = '4a'
dict[('5b','MHOSC')] = '5a'
dict[('6b','MHOSC')] = '6a'


def copyExperimentRunResults(runAttr, rootOutputDir):
    global dict
    
    resultsFileName = rootOutputDir+os.sep+"all-results.csv"

    originalExp = runAttr['Experiment']
    (equivExp, equivPlat) = (dict[runAttr['Experiment'],runAttr['Platform']])

    first = True
    for line in open(resultsFileName, 'r'):
        if first:
            resultAttrCols = CSVLib.colNameList(line)
            first = False
            continue

        resultAttr = CSVLib.line2Dict(line, resultAttrCols)

        if ((equivExp, equivPlat) == (resultAttr['Experiment'], resultAttr['Platform'])) and (runAttr['xvalLabel'] == resultAttr['xvalLabel']):
            for k in resultAttr.iterkeys():
                runAttr[k] = resultAttr[k] #overwrite everything!
            runAttr['Comments'] = 'Copied results from experiment '+equivExp
            print 'Copied results from experiment '+equivExp+'\n'
            runAttr['Experiment'] = originalExp
            break
    
