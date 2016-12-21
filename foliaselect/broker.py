#! /usr/bin/env python3
# -*- coding: utf8 -*-

import util
import sys
import os.path
import time
import re
import lxml     # As used in alpino2folia.xml
import urllib
import urllib.request
import json
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

# ----------------------------------------------------------------------------------
NEDERLAB_BROKER = "http://www.nederlab.nl/broker2/search/"
NEDERLAB_OPENSKOS = "https://openskos.meertens.knaw.nl/nederlab/archief/get/"

# ----------------------------------------------------------------------------------
# Name :    foliareq
# Goal :    Methods to issue requests to the Nederlab broker
# History:
# 19/dec/2016    ERK Created
# ----------------------------------------------------------------------------------
class broker:
    """Methods to communicate with the broker"""

    # ======================= CLASS INITIALIZER ========================================
    def __init__(self, oErr):
        # Set the error handler
        self.errHandle = oErr
        self.oInt = util.interaction()
        self.iSu = 0
        self.quick = False
        self.reHref = re.compile(r"href=['\"]?([^'\"]+)")

    # ----------------------------------------------------------------------------------
    # Name :    task2request
    # Goal :    Convert one task object into a broker request
    #           Task object: 
    #             {"genre": "verhalen", "start": 1990, "end": 1995, "number": 50}
    # History:
    # 20/dec/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def task2request(self, oTask):
        """Convert a broker task to a request"""

        # Validate data we receive
        if oTask == None or not 'start' in oTask or not 'genre' in oTask or not 'number' in oTask:
            # Return the None object
            return None

        # Figure out start and end
        iStart = oTask["start"]
        if "end" in oTask:
            iEnd = oTask["end"]
        else:
            iEnd = iStart + 1

        # Create a correct object
        oData = { "condition": {
                    "type": "and",
                    "list": [
                        { "type": "cql", "field": "NLContent_mtas", "value": "[]" },
                        { "type": "equals", "field": "NLCore_NLAdministrative_sourceCollection", "value": "DBNL" },
                        { "type": "equals", "field": "NLTitle_genre", "value": oTask["genre"]},
                        { "type": "range", "field": "NLTitle_yearOfPublicationMin",
                            "start": str(iStart), "end": str(iEnd) }
                      ]
                  },
                  "response": {
                    "documents": {
                        "number": oTask["number"], "start": 0,
                        "fields": [
                            "NLCore_NLIdentification_nederlabID",
                            "NLCore_NLAdministrative_sourceCollection",
                            "NLTitle_title", "NLTitle_yearOfPublicationMin",
                            "NLTitle_yearOfPublicationMax",
                            "NLTitle_yearOfPublicationLabel",
                            "NLTitle_genre",
                            {   "name": "title_authorinfo",
                                "join": {"from":"NLTitle_NLPersonRef_personID", "to": "NLCore_NLIdentification_nederlabID"},
                                "fields": ["NLPerson_NLPersonName_preferredFullName"]
                            }
                        ]},
                    "stats": True
                    }
                }
        # Return the object that we have made
        return oData


    # ----------------------------------------------------------------------------------
    # Name :    request
    # Goal :    Make a request for information to the broker and return the result
    # History:
    # 20/dec/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def request(self, oData):
        """ Issue a request to the broker"""

        # data = urllib.parse.urlencode(oData).encode('ascii')
        # data = str(oData).replace("'", '"').encode('ascii')
        data = json.dumps(oData).encode('ascii')
        strUri = NEDERLAB_BROKER      
        oPost = {'Accept':'application/json', 
               'Content-Type': 'application/x-www-form-urlencoded'}
        # Prepare a POST request
        req = urllib.request.Request(strUri, headers=oPost, data=data, method='POST')

        try:
            # Perform the actual request
            with urllib.request.urlopen(req, timeout = 20) as response:
                # Get the response as a text
                sResult = response.read().decode('utf-8')
                # First check the result myself
                if sResult == "" or sResult[:1] != "{":
                    # The result is empty, or at least not JSON
                    oResult = {}
                else:
                    # Convert the response text to an object, interpreting it as JSON
                    oResult = json.loads(sResult)
                
        except urllib.error.URLError as e:
            # Show the user what is wrong
            self.errHandle.Status('URLopen URL error: {}\n{}\ndata: {}\n url: {}\n'.format(
                e.reason, str(oData), str(data), strUri))
            # Return failure
            return None
       
        # Getting here means that we have a valid [oResult] object
        return oResult

    def getFolia(self, sFoliaId, flOutput):
        """Retrieve the folia file and save it"""

        strUri = NEDERLAB_OPENSKOS + sFoliaId
        # Prepare a request
        req = urllib.request.Request(strUri, method='GET')

        # Make sure the output is GZ
        if not flOutput.endswith(".gz"):
            flOutput += ".gz"

        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                # Read the response
                with open(flOutput,"wb") as fOut:
                    fOut.write(response.read())

            # Return positively
            return True
        except urllib.error.URLError as e:
            # Show the user what is wrong
            self.errHandle.Status('URLopen URL error: {}\nURI: {}\n'.format(
                e.reason, strUri))
            # Return failure
            return False
        except:
            # Show the user what is wrong
            self.errHandle.DoError("Could not retrieve a file")
            # Return failure
            return False
