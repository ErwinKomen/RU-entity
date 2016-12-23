# ==========================================================================================================
# Name :    ne-stat
# Goal :    Get statistics from one or more Named-Entity log files
# History:
# 22/dec/2016    ERK Created
# ==========================================================================================================
import sys, getopt, os.path, importlib
import util
import nelstats
import json
import csv

# ============================= LOCAL VARIABLES ====================================
errHandle = util.ErrHandle()

# ----------------------------------------------------------------------------------
# Name :    main
# Goal :    Main body of the function
# History:
# 28/sep/2016    ERK Created
# ----------------------------------------------------------------------------------
def main(prgName, argv) :
    flInput = ''        # input file name
    flOutput = ''       # output file name
    flGather = ''       # JSON file describing the set 
    sMethod = ''        # Method to be used

    try:
        # Adapt the program name to exclude the directory (for windows)
        index = prgName.rfind("\\")
        if (index > 0) :
            prgName = prgName[index+1:]
        sSyntax = prgName + ' -i <inputfile/dir> -o <outputfile/dir> -g <gatherfile>'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:g:m:", ["-inputfile=","-outputfile=", "-gatherfile=", "-method="])
        except getopt.GetoptError:
              print(sSyntax)
              sys.exit(2)
        # Walk all the arguments
        for opt, arg in opts:
            if opt == '-h':
                print(sSyntax)
                sys.exit(0)
            elif opt in ("-i", "--ifile"):
                flInput = arg
            elif opt in ("-o", "--ofile"):
                flOutput = arg
            elif opt in ("-g", "--gfile"):
                flGather = arg
            elif opt in ("-m", "--method"):
                sMethod = arg
        # Check if all arguments are there
        if (flInput == '' or flOutput == ''):
            errHandle.DoError(sSyntax)
        # Continue with the program
        errHandle.Status('Input is "' + flInput + '"')
        errHandle.Status('Output is "' + flOutput + '"')
        errHandle.Status('Gather is "' + flGather + '"')
        # Call the function that converst input into output
        kwargs = {"input": flInput, "output": flOutput, "gather": flGather}
        if sMethod != '':
            kwargs['method'] = sMethod
        if (calculate(**kwargs)) :
            errHandle.Status("Ready")
        else :
            errHandle.DoError("Could not complete")    
    except:
        # act
        errHandle.DoError("main")
        return False

# ----------------------------------------------------------------------------------
# Name :    calculate
# Goal :    Calculate statistics for the input files
# History:
# 22/dec/2016    ERK Created
# ----------------------------------------------------------------------------------
def calculate(**kwargs):

    try:
        # Check
        if not "input" in kwargs or not "output" in kwargs or not "gather" in kwargs: return False
        # Get the obligatory parameters from the kwargs
        flInput = kwargs['input']
        flOutput = kwargs['output']
        flGather = kwargs['gather']
        sMethod = ''
        if "method" in kwargs: sMethod = kwargs['method']
        arInput = []        # List of input files

        # Open a statistics object
        oStat = nelstats.nelstats(errHandle)

        # Read the specification of the genres and dates we are looking for
        if os.path.isdir(flInput):
            # Input is a directory
            for root, dirs, files in os.walk(flInput):
                for file in files:
                    if file.endswith(".folia.log"):
                        arInput.append(os.path.abspath( os.path.join(root,file)))
        elif os.path.isfile(flInput):
            arInput.append(flInput)
        else:
            # There is no valid input file
            errHandle.DoError("Could not find input or output. Input [{}]".format(flInput))
            return False

        # Keep track of statistics
        lstLogStat = []
        oLogDirStat = {}
        oLogTotal = {}
        # Walk through all the input files
        for logfile in arInput:
            # Process this file
            oLogStat = oStat.treat(logfile)
            if oLogStat == None:
                # Did not receive a reply
                iStop = 1
            else:
                # Get the directory
                sDir = os.path.dirname(logfile)
                if not sDir in oLogDirStat:
                    oLogDirStat[sDir] = oLogStat
                else:
                    oTmp = oLogDirStat[sDir]
                    for (k,v) in oLogStat.items():
                        if str(v).isnumeric():
                            oTmp[k] += v
                        else:
                            if not k in oTmp:
                                oTmp[k] = v
                            else:
                                oTmp[k]['hit'] += v['hit']
                                oTmp[k]['fail'] += v['fail']
                    # Keep track of the number of documents
                    if not 'docs' in oTmp: oTmp['docs'] = 0
                    oTmp['docs'] += 1
                    # Put the stuff back
                    oLogDirStat[sDir] = oTmp

        # Read the gather file
        with open(flGather, "r") as fGat:
            oCollect = json.load(fGat)

        # Disambiguate the statistics that have just been created in [oLogDirStat]
        #   Then combine results in:
        #   1) oLogTotal - 
        #   2) oCollect  - 
        for (k,v) in oLogDirStat.items():
            if "/" in k:
                arDirs = k.split("/")
            else:
                arDirs = k.split("\\")
            oItem = v
            sSet = str(arDirs[-2])
            iGat = arDirs[-1]
            if not sSet in oLogTotal:
                oLogTotal[sSet] = {}
            # Create an object with the services used in this Set
            oLogTotal[sSet]['services'] = []
            oLogTotal[sSet]['ptc'] = []
            # Find the section in the gather file
            for g in oCollect['collection']:
                if g['dir'] == sSet:
                    lGather = g['gather']
                    oGather = lGather[int(iGat)]
                    for (p,q) in oGather.items():
                        oItem[p] = q

                    # what is the number of named entities here?
                    iNE = oItem['ne']
                    # Visit all the services
                    for (keyService, oService) in oItem.items():
                        if isinstance(oService, dict) and 'hit' in oService:
                            # This really is a service
                            iPtc = 100 * oService['hit'] / iNE
                            oGather[keyService+'_ptc'] = iPtc
                            # Find out which row it is in the 'services' array
                            if not keyService in oLogTotal[sSet]['services']:
                                # Add it to the services
                                oLogTotal[sSet]['services'].append(keyService)
                            iServiceRow = oLogTotal[sSet]['services'].index(keyService)

                    # oItem['num'] = int(arDirs[-1])
                    oLogTotal[sSet][iGat] = oItem

        # Try to extract information from oLogTotal to make a CSV file
        oCsv = {}
        for (sSet,oSet) in oLogTotal.items():
            lRows = []
            # First row contains column information
            oRow = ['set', 'genre', 'start', 'docs', 'ne']
            # Add one column header for each service
            for sThis in oSet['services']: oRow.append(sThis)
            # Add this row to the list of rows
            lRows.append(oRow)
            # Walk all the elements of this set
            for (sKey, oItem) in oSet.items():
                if str(sKey) != 'services' and str(sKey) != 'ptc':
                    # Start a new ro
                    oRow = [sSet]
                    # Get the standard information from this row
                    try:
                        oRow.append(oItem['genre'])
                    except:
                        iStop = 1
                    oRow.append(oItem['start'])
                    if 'docs' in oItem:
                        oRow.append(oItem['docs'])
                    else:
                        oRow.append(0)
                    if 'ne' in oItem:
                        oRow.append(oItem['ne'])
                    else:
                        oRow.append(0)
                    # Walk all the services
                    for sThis in oSet['services']: 
                        # See if this service is represented
                        if sThis in oItem:
                            # Add this count of hits
                            oRow.append(oItem[sThis]['hit'])
                        else:
                            # Not represented: count = 0
                            oRow.append(0)
                    # Add the row to the list
                    lRows.append(oRow)
            # Combine into oCsv
            oCsv[sSet] = lRows
            with open(flOutput.replace(".json", "_"+sSet+".csv"), "w") as csvfile:
                wOut = csv.writer(csvfile, delimiter='\t')
                for oRow in lRows:
                    wOut.writerow(oRow)



        # Save the statistics results
        with open(flOutput, "w") as fOut:
            json.dump(oLogTotal, fOut, indent=2)
        # Save the adapted collect
        with open(flOutput.replace(".json", "-collect.json"), "w") as fOut:
            json.dump(oCollect, fOut, indent = 2)

        # Save a CSV file
        with open(flOutput.replace(".json", "_csv.json"), "w") as fOut:
            json.dump(oCsv, fOut, indent = 2)

        # Return positively
        return True
    except:
        errHandle.DoError("ne-stat")
        return False


# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    # Call the main function with two arguments: program name + remainder
    main(sys.argv[0], sys.argv[1:])
