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
    flStat = ''         # statistics file name
    sMethod = ''        # Method to be used

    try:
        # Adapt the program name to exclude the directory
        index = prgName.rfind("\\")
        if (index > 0) :
            prgName = prgName[index+1:]
        sSyntax = prgName + ' [-s <statfile>] -i <inputfile> -o <outputfile>'
        # get all the arguments
        try:
            # Get arguments and options
            opts, args = getopt.getopt(argv, "hs:i:o:m:", ["-statfile=","-inputfile=","-outputfile=", "-method="])
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
            elif opt in ("-m", "--method"):
                sMethod = arg
        # Check if all arguments are there
        if (flInput == '' or flOutput == '' or flStat == ''):
            errHandle.DoError(sSyntax)
        # Continue with the program
        errHandle.Status('Input is "' + flInput + '"')
        errHandle.Status('Output is "' + flOutput + '"')
        errHandle.Status('Statistics: "' + flStat + '"')
        # Call the function that converst input into output
        kwargs = {"input": flInput, "output": flOutput, "stat": flStat}
        if sMethod != '':
            kwargs['method'] = sMethod
        if (foliaselect(**kwargs)) :
            errHandle.Status("Ready")
        else :
            errHandle.DoError("Could not complete")    
    except:
        # act
        errHandle.DoError("main")
        return False

# ----------------------------------------------------------------------------------
# Name :    foliaselect
# Goal :    Deal with all the requests inside the [flInput] file
# History:
# 20/dec/2016    ERK Created
# ----------------------------------------------------------------------------------
def foliaselect(**kwargs):

    try:
        # Check
        if not "input" in kwargs or not "output" in kwargs: return False
        # Get the obligatory parameters from the kwargs
        flInput = kwargs['input']
        flOutput = kwargs['output']
        sMethod = ''
        if "method" in kwargs: sMethod = kwargs['method']

        # Start a broker communication instance
        oBroker = broker.broker(errHandle)

        # Read the specification of the genres and dates we are looking for
        if not os.path.isfile(flInput):
            # There is no valid input file
            errHandle.DoError("Could not find input or output. Input [{}]".format(flInput))
            return False
        # Read the input file as JSON
        with open(flInput, "r") as fIn:
            oInput = json.load(fIn)
        sDate = oInput['date']
        iTotal = 0
        # Derive an output directory
        sDirOut = os.path.dirname(flOutput)
        # Load the collection array
        lstCollection = oInput['collection']
        # Walk the collections
        for oCol in lstCollection:
            # Treat this collection
            sTitle = oCol['title']
            lstGather = oCol['gather']
            # Walk all gather elements
            for iGather, oGather in enumerate(lstGather):
                # Get the information from this object
                oRequest = oBroker.task2request(oGather)
                oResponse = oBroker.request(oRequest)
                # Interpret the response
                if oResponse == None:
                    errHandle.DoError("Could not get a response from the broker")
                    return False
                elif oResponse['status'] != 'ok':
                    errHandle.DoError("Broker returned error: " + oResponse['status'])
                    return False

                # Process the documents we received
                iResults = oResponse['stats']['total']
                oGather['results'] = iResults
                oGather['documents'] = oResponse['documents']
                # Keep track of how much we get
                iTotal += iResults
                # Show what we are doing
                if "end" in oGather:
                    iEnd = oGather['end']
                else:
                    iEnd = oGather['start'] + 1
                errHandle.Status("{} collection[{}] genre[{}] years: [{}-{}]: {}".format(
                    sDate, sTitle, oGather['genre'], oGather['start'], iEnd, iResults))

                # Create a directory for these results
                sResDir = os.path.join(os.path.abspath(sDirOut), oCol['dir'])
                if not os.path.exists(sResDir): os.mkdir(sResDir)
                sResDir = os.path.join(os.path.abspath(sResDir), str(iGather) )
                if not os.path.exists(sResDir): os.mkdir(sResDir)

                # Walk through the results
                for iRes, oRes in enumerate(oGather['documents']):
                    # Create a file name
                    sResBase = os.path.join(sResDir, str(iRes) )
                    sResFolia = sResBase + ".folia.xml"
                    sResJson = sResBase + ".json"

                    # Save the meta information
                    with open(sResJson, "w") as fMeta:
                        json.dump(oRes, fMeta, indent=2)

                    # Resumption?
                    if sMethod != 'resume' or not os.path.exists(sResFolia + ".gz"):
                        # Get and save the folia file
                        print("Downloading: {}".format(sResFolia))
                        oBroker.getFolia(oRes['NLCore_NLIdentification_nederlabID'], sResFolia)

        # Save all the document details
        errHandle.Status("saving to: " + flOutput)
        with open(flOutput, "w") as fOut:
            json.dump(oInput, fOut, indent=2)

        errHandle.Status("Results: {}".format(iTotal))

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
