# ==========================================================================================================
# Name :    foliaselect
# Goal :    Select folia file identifiers from different genres and dates
# History:
# 28/sep/2016    ERK Created
# ==========================================================================================================
import sys, getopt, os.path, importlib
import util
import broker
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

    try:
        # Adapt the program name to exclude the directory
        index = prgName.rfind("\\")
        if (index > 0) :
            prgName = prgName[index+1:]
        sSyntax = prgName + ' [-s <statfile>] -i <inputfile> -o <outputfile>'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hs:i:o:", ["-statfile=","-inputfile=","-outputfile="])
        except getopt.GetoptError:
              print(sSyntax)
              sys.exit(2)
        # Walk all the arguments
        for opt, arg in opts:
            if opt == '-h':
                print(sSyntax)
                sys.exit(0)
            elif opt in ("-s", "--sfile"):
                flStat = arg
            elif opt in ("-i", "--ifile"):
                flInput = arg
            elif opt in ("-o", "--ofile"):
                flOutput = arg
        # Check if all arguments are there
        if (flInput == '' or flOutput == '' or flStat == ''):
            errHandle.DoError(sSyntax)
        # Continue with the program
        errHandle.Status('Input is "' + flInput + '"')
        errHandle.Status('Output is "' + flOutput + '"')
        errHandle.Status('Statistics: "' + flStat + '"')
        # Call the function that converst input into output
        if (foliaselect(flInput, flOutput, flStat)) :
            errHandle.Status("Ready")
        else :
            errHandle.DoError("Could not complete")    
    except:
        # act
        errHandle.DoError("main")
        return False

def foliaselect(flInput, flOutput, flStat):

    try:
        # Start a broker communication instance
        oBroker = broker(errHandle)

        # Read the specification of the genres and dates we are looking for

        # Return positively
        return True
    except:
        errHandle.DoError("foliaselect")
        return False


# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    # Call the main function with two arguments: program name + remainder
    main(sys.argv[0], sys.argv[1:])
