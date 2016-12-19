import sys, traceback

class ErrHandle:
  """Error handling"""

  # ======================= CLASS INITIALIZER ========================================
  def __init__(self):
    # Initialize a local error stack
    self.loc_errStack = []

  # ----------------------------------------------------------------------------------
  # Name :    Status
  # Goal :    Just give a status message
  # History:
  # 6/apr/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def Status(self, msg):
    # Just print the message
    print(msg, file=sys.stderr)

  # ----------------------------------------------------------------------------------
  # Name :    DoError
  # Goal :    Process an error
  # History:
  # 6/apr/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def DoError(self, msg, bExit = False):
    # Append the error message to the stack we have
    self.loc_errStack.append(msg)
    # Print the error message for the user
    print("Error: "+msg+"\nSystem:", file=sys.stderr)

    try:
        # Do we actually have a real error?
        if sys.exc_info() != None and traceback != None:
            for nErr in sys.exc_info():
              if (nErr != None):
                print(nErr, file=sys.stderr)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback,
                                      limit=2, file=sys.stderr)
    except:
        print("  (no traceback)", file=sys.stderr)
        pass
    # Is this a fatal error that requires exiting?
    if (bExit):
      sys.exit(2)

class interaction:
  """User-interation"""

  # ----------------------------------------------------------------------------------
  # Name :    query_yes_no
  # Goal :    Elicit confirmation from user
  # Source:   http://stackoverflow.com/questions/3041986/python-command-line-yes-no-input
  # History:
  # 6/apr/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "true": True, "t": True, "1": True,
             "no": False, "n": False, "false": False, "f": False, "0": False}
    if default is None:
      prompt = " [y/n] "
    elif default == "yes":
      prompt = " [Y/n] "
    elif default == "no":
      prompt = " [y/N] "
    else:
      raise ValueError("invalid default answer: '%s'" % default)

    while True:
      sys.stdout.write(question + prompt)
      choice = raw_input().lower()
      if default is not None and choice == '':
        return valid[default]
      elif choice in valid:
        return valid[choice]
      else:
        sys.stdout.write("Please respond with 'yes' or 'no' "
                            "(or 'y' or 'n').\n")

