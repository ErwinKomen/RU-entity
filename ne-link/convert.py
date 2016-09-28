#! /usr/bin/env python3
# -*- coding: utf8 -*-

import util
import os.path
import time
import re
import lxml     # As used in alpino2folia.xml
# Make sure that folia is imported
try:
  from pynlpl.formats import folia
except:
  print("ERROR: pynlpl not found. Please obtain PyNLPL from the Python Package Manager ($ sudo easy_install pynlpl) or directly from github: $ git clone git://github.com/proycon/pynlpl.git", file=sys.stderr)
  sys.exit(2)

# ----------------------------------------------------------------------------------
# Name :    convert
# Goal :    Methods to convert text files from one format to another
# History:
# 28/sep/2016    ERK Created
# ----------------------------------------------------------------------------------
class convert:
  """Methods supporting named-entity linking conversion"""
  loc_arLang = ["Dutch", "German", "English", "Spanish", "French", "Welsh", "Vlaams", "Lezgi", "Lak", "Chechen"]
  loc_arEthno = ["nld", "deu", "eng", "spa", "fra", "cym", "vls", "lez", "lak", "che"]
  loc_arXmlIn = ["&", "<", ">", "\""]
  loc_arXmlNamed = ["&amp;", "&lt;", "&gt;", "&quot;"]

  # ======================= CLASS INITIALIZER ========================================
  def __init__(self, oErr):
    # Set the error handler
    self.errHandle = oErr
    self.oInt = util.interaction()
    self.iSu = 0
    # Get the relax NG schema
    self.schema = lxml.etree.RelaxNG(folia.relaxng())
    self.quick = False

  # ----------------------------------------------------------------------------------
  # Name :    doValidate
  # Goal :    Perform validation
  # History:
  # 28/sep/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def doValidate(self, flInput):
    # Validation gives an exception if something goes wrong
    try:
      # Attempt validation
      folia.validate(flInput, self.schema, self.quick)
      # Getting here means that all went well
      return True
    except:
      # something went wrong
      return False

  # ----------------------------------------------------------------------------------
  # Name :    addOneNelToFolia
  # Goal :    Add one Named-Entity-Linking layer to a Folia xml file
  # History:
  # 28/sep/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def addOneNelToFolia(self, flInput, flOutput, bDoAsk = False, **info):
    try:
      # Initialisations
      patPunct = re.compile(r"[\.\,\?\!\'\"\`\;\:\-]")
      # Validate: does flInput exist?
      if (not os.path.isfile(flInput)) : 
        self.errHandle.DoError("Input file not found: " + flInput)
        return False
      # Validate: do we need to check the existence of the destination?
      if (bDoAsk):
        # Yes, check if it exists already
        if (os.path.isfile(flOutput)):
          # The file already exists: ask if it should be overwritten
          sReply = self.oInt.query_yes_no("Overwrite existing file?")
          if (sReply != "yes"):
            # Return peacefully
            self.errHandle.Status("Aborted")
            return True
      # Extract the relevant information from the info object
      sAnnotator = ""
      iAnnotatorType = -1
      if ("annotator" in info): sAnnotator = info["annotator"]
      if ("annotatortype" in info): iAnnotatorType = getAnnotatorType(info["annotatortype"])
      # Determine the language code according to the ethnologue
      sEthno = self.langToEthno(sLang)
      # Set optional arguments
      kwargs = {}
      if (sAnnotator != ""):
        kwargs["annotator"] = sAnnotator
        if (iAnnotatorType >=0): 
          kwargs["annotatortype"] = iAnnotatorType
        else: 
          kwargs["annotatortype"] = folia.AnnotatorType.AUTO
      else:
        sAnnotator = "nel2folia" 

      # Load the indicated .folia.xml INPUT document
      doc = folia.Document(file=flInput)
      # Immediately save it as the output document
      doc.save(filename = flOutput)

      # Add the annotator information for this "nel2folia" conversion
      doc.declare(folia.AnnotationType.ALIGNMENT, sAnnotator+"-NEL", **kwargs)

      # Find and leaf through all the NER elements
      for sentence in doc.sentences:

          # visit the entity layer
          for layer in sentence.select(folia.EntitiesLayer):

              # visit all Entity elements
              for entity in layer.select(folia.Entity):

                  # Get the class of this entity
                  entClass = entity.cls
                  # Find all the words belonging to this entity
                  sEntity = ""
                  for word in entity.wrefs():
                      if sEntity != "": sEntity = sEntity + " "
                      sEntity = sEntity + word

                  # We now have the whole entity and its class: add to a list of todo's
                  oEntity = {"entity": sEntity, "class": entClass}
                  # Get a list of alignments for this entity
                  lResults = oneEntityToLinks(oEntity)
                  # Walk the results
                  for result in lResults:

                      # Add an alignment layer for this result
                      alignment = entity.append(folia.Alignment)
                      alignment.cls = "NEL"     # Named Entity Link
                      alignment.href = ""
                      alignment.type = "simple"
                      alignment.format = "application/rdf+xml"


      # Save the FoLiA document that has been created
      doc.save(filename = flOutput)
      # all went well, so return positively
      return True
    except:
      # act
      self.errHandle.DoError("convert/addOneNelToFolia exception")
      return False

  # ----------------------------------------------------------------------------------
  # Name :    getAnnotatorType
  # Goal :    Conver the string name into an integer annotatortype
  # History:
  # 6/apr/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def getAnnotatorType(self, sName):
    try:
      # Look at the lower-case variant of the name
      sName = sName.lower()
      # Decide what to return
      if (sName == "manual"): return folia.AnnotatorType.MANUAL
      elif (sName == "automatic"): return folia.AnnotatorType.AUTO
      else: return folia.AnnotatorType.UNSET
    except:
      # act
      self.errHandle.DoError("convert/getAnnotatorType exception")
      return  folia.AnnotatorType.UNSET

  def oneEntityToLinks(self, oEntity):
      lResults = []

      try:
          # Convert entity to link

          return lResults
      except:
          # act
          self.errHandle.DoError("oneEntityToLinks")
          return False


  # ----------------------------------------------------------------------------------
  # Name :    XmlEscape
  # Goal :    Convert certain characters into XML okay characters
  # History:
  # 04-12-2008  ERK Created for vb.NET
  # 8/apr/2016  ERK Ported to Python
  # ----------------------------------------------------------------------------------
  def XmlEscape(self, strIn):
    try:
      # Walk the list of potential replacements
      for i in range(len(self.loc_arXmlIn)):
        strIn = strIn.replace(self.loc_arXmlIn[i], self.loc_arXmlNamed[i])
      # Return the result
      return strIn
    except:
      self.errHandle.DoError("XmlEscape")
      return None

  # ----------------------------------------------------------------------------------
  # Name :    langToEthno
  # Goal :    Convert the language name (e.g. "Dutch") to a valid ethnologue code
  #           If this does not work, return the language name in full
  # History:
  # 4/apr/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def langToEthno(self, sLang):
    try:
      # Prepare the string: lower-case, trimmed
      sLang = sLang.strip().lower()
      # Iterate over all member of loc_arLang
      for i in range(len(self.loc_arLang)):
        if (self.loc_arLang[i].lower() == sLang):
          return self.loc_arEthno[i]
      # Getting here means that the name is not found in the array
      # So: return the name in full
      return sLang
    except:
      # act
      self.errHandle.DoError("langToEthno exception")
      return ""



