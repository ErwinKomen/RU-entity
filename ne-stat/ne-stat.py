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
    sMethod = ''        # Method to be used

    try:
        # Adapt the program name to exclude the directory (for windows)
        index = prgName.rfind("\\")
        if (index > 0) :
            prgName = prgName[index+1:]
        sSyntax = prgName + ' -i <inputfile/dir> -o <outputfile/dir>'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hi:o:m:", ["-inputfile=","-outputfile=", "-method="])
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
            elif opt in ("-m", "--method"):
                sMethod = arg
        # Check if all arguments are there
        if (flInput == '' or flOutput == ''):
            errHandle.DoError(sSyntax)
        # Continue with the program
        errHandle.Status('Input is "' + flInput + '"')
        errHandle.Status('Output is "' + flOutput + '"')
        # Call the function that converst input into output
        kwargs = {"input": flInput, "output": flOutput}
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
        if not "input" in kwargs or not "output" in kwargs: return False
        # Get the obligatory parameters from the kwargs
        flInput = kwargs['input']
        flOutput = kwargs['output']
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
                    oLogDirStat[sDir] = oTmp

        # Disambiguate the statistics
        for (k,v) in oLogDirStat.items():
            if "/" in k:
                arDirs = k.split("/")
            else:
                arDirs = k.split("\\")
            oItem = v
            sSet = str(arDirs[-2])
            if not sSet in oLogTotal:
                oLogTotal[sSet] = {}
            # oItem['num'] = int(arDirs[-1])
            oLogTotal[sSet][arDirs[-1]] = oItem
            # lstLogStat.append(oItem)

        # Save the statistics results
        with open(flOutput, "w") as fOut:
            json.dump(oLogTotal, fOut, indent=2)

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
