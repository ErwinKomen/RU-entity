#! /usr/bin/env python3
# -*- coding: utf8 -*-

import util
import sys
import os.path
import time
import re
import lxml     # As used in alpino2folia.xml
import json
from xml.sax.saxutils import quoteattr
import requests
import urllib
# Make sure that folia is imported
try:
  from pynlpl.formats import folia
except:
  print("ERROR: pynlpl not found. Please obtain PyNLPL from the Python Package Manager ($ sudo easy_install pynlpl) or directly from github: $ git clone git://github.com/proycon/pynlpl.git", file=sys.stderr)
  sys.exit(2)
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

# Set the location of the (Dutch) REST service here and the default confidence level
SPOTLIGHT_REQUEST = "http://spotlight.sztaki.hu:2232/rest/annotate"
SPOTLIGHT_DISAMBI = "http://spotlight.sztaki.hu:2232/rest/disambiguate"
SPOTLIGHT_CONFIDENCE = "0.20"
# Note: it is also possible to set the "support" parameter -- the number of inlinks
#       that should minimally exist for a valid result

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
      sConfidence = SPOTLIGHT_CONFIDENCE
      if ("annotator" in info): sAnnotator = info["annotator"]
      if ("annotatortype" in info): iAnnotatorType = getAnnotatorType(info["annotatortype"])
      if ("confidence" in info): sConfidence = info["confidence"]
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
      self.errHandle.Status("Loading file: " + flInput )
      doc = folia.Document(file=flInput)
      # Immediately save it as the output document
      self.errHandle.Status("Saving file: " + flOutput )
      doc.save(filename = flOutput)

      # Add the annotator information for this "nel2folia" conversion
      doc.declare(folia.AnnotationType.ALIGNMENT, sAnnotator+"-NEL", **kwargs)

      # Find and leaf through all the NER elements
      for sentence in doc.sentences():

          # We ourselves build the text of the sentence that is being looked through
          sSent = ""

          # visit the entity layer
          for layer in sentence.select(folia.EntitiesLayer):

              # visit all Entity elements
              for entity in layer.select(folia.Entity):

                  # Get the class of this entity
                  entClass = entity.cls
                  # Find all the words belonging to this entity
                  sEntity = ""
                  idStart = ""
                  for word in entity.wrefs():
                      # Combine the words of the entity into a string
                      if sEntity != "": 
                          sEntity = sEntity + " "
                      else:
                          # Note the start id of the entity
                          idStart = word.id
                      sEntity = sEntity + str(word)
                  
                  # Calculate the offset for this entity
                  iOffset = 0
                  for word in sentence.select(folia.Word):
                      # Keep track of the sentence
                      if sSent != "": sSent = sSent + " "
                      sSent = sSent + str(word)
                      # Note where the offset is
                      if word.id == idStart: 
                          iOffset = len(sSent)

                  # Check and remove any existing alignments
                  for alg in entity.select(folia.Alignment):
                      alg.parent.remove(alg)

                  # We now have the whole entity and its class: add to a list of todo's
                  oEntity = {"entity": sEntity, "class": entClass, "sent": sSent, "offset": str(iOffset)}
                  # Get a list of alignments for this entity
                  lResults = self.oneEntityToLinks(oEntity, sConfidence)
                  # Walk the results
                  for result in lResults:

                      # Define an alignment layer for this result
                      alignment = entity.append(folia.Alignment)
                      alignment.cls = "NEL"     # Named Entity Link
                      alignment.href = result['uri']
                      alignment.type = "simple"
                      # alignment.format = "application/rdf+xml"
                      alignment.format = "application/json"



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

  # ----------------------------------------------------------------------------------
  # Name :    oneSpotlightRequest
  # Goal :    Make an annotate or disambiguate request to spotlight
  # History:
  # 17/oct/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def oneSpotlightRequest(self, sReqType, oEntity, sConfidence):
      oResult = {}
      data = ""

      # Debugging statement
      self.errHandle.Status(oEntity['class'] + " - " + oEntity['entity'])

      # Try to get a link from a REST service
      # Example: http://spotlight.sztaki.hu:2232/rest/annotate?text=panamese&confidence=0.35
      sEntity = urllib.parse.quote_plus(quoteattr(oEntity['entity']))
      if sReqType == 'annotate':
          strUrl = SPOTLIGHT_REQUEST + '?confidence=' + sConfidence + '&text=' + sEntity

          # Changes for POST method
          oData = {'confidence': sConfidence,
                   'text': oEntity['entity']}
          data = urllib.parse.urlencode(oData).encode('ascii')
          strUrl = SPOTLIGHT_REQUEST

      elif sReqType == 'disambiguate':
          sSent = urllib.parse.quote_plus(quoteattr(oEntity['sent'], {'"':'&amp;'}))
          iOffset = oEntity['offset']
          sXml = urllib.parse.quote_plus('<annotation text="') + sSent + \
                 urllib.parse.quote_plus('"><surfaceForm name="') + sEntity + \
                 urllib.parse.quote_plus('" offset="' + iOffset + '" /></annotation>')
          strUrl = SPOTLIGHT_DISAMBI + '?confidence=' + sConfidence + '&text=' + sXml

          # Prepare POST data
          sXmlPost = '<annotation text="' + oEntity['sent'].replace('&', '&amp;').replace('"', '&amp;') + \
              '"><surfaceForm name="' + oEntity['entity'].replace('&', '&amp;').replace('"', '&amp;') + \
              '" offset="' + iOffset + '" /></annotation>'
          oData = {'confidence': sConfidence,
                   'text': sXmlPost}
          data = urllib.parse.urlencode(oData).encode('ascii')
          strUrl = SPOTLIGHT_DISAMBI

      
      # DEBUGGING x,y = urllib.request.splittype(strUrl)

      # POST: content-type = application/x-www-form-urlencoded
      # GET method: req = urllib.request.Request(strUrl, headers={'accept':'application/json'})
      # POST method:
      oPost = {'accept':'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
      req = urllib.request.Request(strUrl, headers=oPost, data=data, method='POST')
      
      try:
          # Perform the actual request to the URL
          with urllib.request.urlopen(req) as response:
              # Get the response as a text
              sResult = response.read().decode('utf-8')
              # Convert the response text to an object, interpreting it as JSON
              oResult = json.loads(sResult)
      except urllib.error.URLError as e:
          self.errHandle.Status('URLopen URL error: ' + e.reason)
          return false
      except urllib.error.HTTPError as e:
          self.errHandle.Status('URLopen HTTP error: ' + e.code)
          return false
      except:
          description = sys.exc_info()[1]
          self.errHandle.Status(description)      
          return false
      # Return the JSON result object
      return oResult

  # ----------------------------------------------------------------------------------
  # Name :    oneEntityToLinks
  # Goal :    Get a list of possibilities to which one entity can be linked
  # History:
  # 10/oct/2016    ERK Created
  # ----------------------------------------------------------------------------------
  def oneEntityToLinks(self, oEntity, sConfidence):
      lResults = []

      # First try making a disambiguation spotlight request
      oResult = self.oneSpotlightRequest('disambiguate', oEntity, sConfidence)
      if not 'Resources' in oResult:
          # Second try: annotation request
          oResult = self.oneSpotlightRequest('annotate', oEntity, sConfidence)


      # Have any resources been found?
      if 'Resources' in oResult:
          # Walk through the list of resources returned
          lResources = oResult['Resources']
          for resThis in lResources:
              # Get the resource type
              resType = resThis['@types']
              # Do we have a type?
              if resType != '':
                  # Double check whether the resource type matches the entity class
                  eClass = oEntity['class']
                  bFound = False
                  if eClass == 'loc' and 'Schema:Place' in resType: 
                      # Location
                      bFound = True
                  elif eClass == 'org' and (':Organization' in resType or ':Organisation' in resType):
                      # Organization
                      bFound = True
                  elif eClass == 'pro' and (':Language' in resType):
                      # Product -- could be language
                      bFound = True
                  elif eClass == 'per' and (':Agent' in resType):
                      # This should be a person
                      bFound = True
                  elif eClass == 'misc':
                      # Miscellaneous allows all types
                      bFound = True
                  else:
                      # We have something, but it's either of a different type or it doesn't match
                      bFound = False

                  if bFound:
                      # There is a type and it fits the class, so process it
                      oneResult = {'uri': resThis['@URI'], 'type': resType }
                      lResults.append(oneResult)
                      self.errHandle.Status('  Result: ' + resThis['@URI'])

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



