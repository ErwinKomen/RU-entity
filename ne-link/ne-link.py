# ==========================================================================================================
# Name :    ne-link
# Goal :    Add Named-Entity linking to FoLiA files
# History:
# 28/sep/2016    ERK Created
# ==========================================================================================================
import sys, getopt, os.path, importlib
import util
import convert
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
  sAnnotator = ""     # If specified
  flStat = 'nel2folia-stats.json'         # Location of the statistics file that is produced (optional argument)

  try:
    # Adapt the program name to exclude the directory
    index = prgName.rfind("\\")
    if (index > 0) :
      prgName = prgName[index+1:]
    sSyntax = prgName + ' [-a <annotator>] [-s <statfile>] -i <inputfile> -o <outputfile>'
    # get all the arguments
    try:
      # Get arguments and options
      opts, args = getopt.getopt(argv, "ha:s:i:o:", ["-annotator","-statfile=","-inputfile=","-outputfile="])
    except getopt.GetoptError:
      print(sSyntax)
      sys.exit(2)
    # Walk all the arguments
    for opt, arg in opts:
      if opt == '-h':
        print(sSyntax)
        sys.exit(0)
      elif opt in ("-a", "--annotator"):
        sAnnotator = arg
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
    if (nel2folia(flInput, flOutput, flStat, sAnnotator)) :
      errHandle.Status("Ready")
    else :
      errHandle.DoError("Could not complete")
  except:
    # act
    errHandle.DoError("main")
    return False


# ----------------------------------------------------------------------------------
# Name :    nel2folia
# Goal :    Link named entities 
# History:
# 28/sep/2016    ERK Created
# ----------------------------------------------------------------------------------
def nel2folia(flInput, flOutput, flStat, sAnnotator):
  bDoAsk = False                  # Local variable
  arInput = []                    # Array of input files
  arOutput = []                   # Array of output files
  iHit = 0                        # Statistics: number of hits
  iFail = 0                       # Statistics: number of failures
  iDocs = 0                       # Number of documents
  lStats = []                     # List of all resolutions
  oConv = convert.convert(errHandle)      # Object that handles the conversion

  try:
    # Create a kwargs information object to be passed on
    info = {"annotator": sAnnotator}
    # Validate: does flInput exist?
    if (os.path.isfile(flInput)) : 
      # The input is one file
      arInput.append(flInput)
      # Check the output type
      if (os.path.isdir(flOutput)):
        # Output is a directory NAME --> create good output file name
        arOutput.append(os.path.normpath(flOutput + "/" + os.path.splitext(os.path.basename(flInput))[0] + ".folia.xml"))
      else:
        # Output is a file NAME
        arOutput.append(flOutput)
    elif (os.path.isdir(flInput) and os.path.isdir(flOutput)):
      # The input and output are directories: add all files in this directory
      # One directory only: for flThis in os.listdir(flInput):
      for dirpath, dirnames, filenames in os.walk(flInput):
        # Determine the subdirectory
        subdir = dirpath.split(flInput, 1)[1]
        for flThis in filenames:
          if flThis.endswith(".folia.xml"):
            # We are expecting input files with extension .folia.xml
            if (flThis.endswith(".folia.xml")):
              # Add this file to the list of input files
              arInput.append(os.path.normpath(dirpath + "/" + flThis))
              # Add a corresponding file to the list of output files
              arOutput.append(os.path.normpath(flOutput + subdir + "/" + os.path.basename(flThis)))
    else:
      errHandle.DoError("Could not find input or output. Input [{}] Output [{}]".format(flInput, flOutput))
      return False
    # Perform the conversion in the Conversion module
    for index in range(len(arInput)):
      # Perform conversion of this file
      oBack = oConv.addOneNelToFolia(arInput[index], arOutput[index], bDoAsk, **info)
      if oBack == None:
        # Signal there was an error
        errHandle.DoError("nel2folia conversion error in " + os.path.basename(arInput[index]))
        return False
      # Otherwise: keep track of statistics
      iHit += oBack['hit']
      iFail += oBack['fail']
      iDocs += 1
      lStats.append({'doc': os.path.basename(arInput[index]),
                     'resolutions': oBack['resolutions']})
      # Perform validation of the output file that has been produced
      if (not oConv.doValidate(arOutput[index])):
        # Signal there was an error
        errHandle.DoError("nel2folia validation error in " + os.path.basename(arOutput[index]))
        return False

    # Provide statistics
    errHandle.Status("nel2folia: hits={}, fail={}, docs={}".format(
                     iHit, iFail, iDocs))
    # Save the statistics in a .json file
    with open(flStat, 'w') as outfile:
        json.dump(lStats, outfile, indent=2)
    # We are happy: return okay
    return True
  except:
    # act
    errHandle.DoError("nel2folia")
    return False



# ----------------------------------------------------------------------------------
# Goal :  If user calls this as main, then follow up on it
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
  # Call the main function with two arguments: program name + remainder
  main(sys.argv[0], sys.argv[1:])
