import os, CSVLib

###THIS SCRIPT IS CURRENTLY NOT USED

#For MHOSC, any tasks that are not 'raw' are safely ignored!
dict = {}

#dummy - for testing only
#dict[('0b','INSNEE')] = ('0a','INSNEE')

dict[('0b','MHOSC')] = ('0a','MHOSC') #for the same xVal etc
dict[('0c','MHOSC')] = ('0a','MHOSC')
dict[('0d','MHOSC')] = ('0a','MHOSC') 
dict[('0e','MHOSC')] = ('0a','MHOSC') 

dict[('0c','INSNEE')] = ('0b','INSNEE')
dict[('0d','INSNEE')] = ('0b','INSNEE') 
dict[('0e','INSNEE')] = ('0b','INSNEE') 

dict[('1b','MHOSC')] = ('1a','MHOSC')

dict[('2b','MHOSC')] = ('2a','MHOSC')

dict[('3b','MHOSC')] = ('3a','MHOSC')

dict[('4b','MHOSC')] = ('4a','MHOSC')
dict[('4b','INSNEE')] = ('4a','INSNEE')

dict[('5b','MHOSC')] = ('5a','MHOSC')
dict[('5b','INSNEE')] = ('5a','INSNEE')

dict[('6b','MHOSC')] = ('6a','MHOSC')
dict[('6b','INSNEE')] = ('6a','INSNEE')


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
    
