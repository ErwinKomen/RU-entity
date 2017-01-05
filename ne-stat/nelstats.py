#! /usr/bin/env python3
# -*- coding: utf8 -*-

import util
import sys
import os.path
import csv

# ----------------------------------------------------------------------------------
# Name :    stats
# Goal :    Derive statistics from a .folia.log file
# History:
# 22/dec/2016    ERK Created
# ----------------------------------------------------------------------------------
class nelstats:
    """Statistics from a .folia.log file"""


    # ======================= CLASS INITIALIZER ========================================
    def __init__(self, oErr):
        # Set the error handler
        self.errHandle = oErr

    # ----------------------------------------------------------------------------------
    # Name :    treat
    # Goal :    Treat one file: 
    # History:
    # 22/dec/2016    ERK Created
    # ----------------------------------------------------------------------------------
    def treat(self, fInput):
        """Get statistics from this file"""

        # Initialise the statistics with the number of named entities set to 0
        oStats = {'ne': 0}  
        bMakeLst = False

        if bMakeLst: oStats['lst'] = []

        try:
            # CHeck existence
            if not os.path.exists(fInput): return None
            # Open and start reading the input
            with open(fInput, "r",  encoding='utf-8') as fIn:
                rdCsv = csv.reader(fIn, delimiter="\t")
                # Row division:
                # 0  File
                # 1  sentId
                # 2  type of named-entity: 'per', 'loc', 'misc', 'org', 'pro' and so forth
                # 3  Named-Entity
                # 4  hit
                # 5  Service
                # 6  Method
                # 7  Result URI
                # 8  NER-form
                # 9  ClassMatch
                # 10 Support
                # 11 Offset
                # 12 Similarity
                # 13 2ndOfRank

                sFileId = ""
                sSentId = ""
                sEntity = ""
                sService = ""
                sMethod = ""
                sFirstService = ""

                for row in rdCsv:
                    # Sanity check: number of columns
                    if len(row) == 14:
                        # Make sure we do not count doubles
                        if not(sSentId == row[1] and sFileId == row[0] and sEntity == row[3] and sService == row[5] and sMethod == row[6]):
                            # Check for changes in the entity
                            if sSentId != row[1] or sFileId != row[0] or sEntity != row[3] or row[5] == sFirstService:
                                # New entity
                                oStats['ne'] += 1
                                try:
                                    sFirstService = row[5]
                                except:
                                    iStop = 1
                                if bMakeLst:
                                    oStats['lst'].append({'sent': row[1], 'entity': row[3]})

                            # Make sure this service is in the 'oHits'
                            sThisService = row[5]
                            if sThisService == "":
                                # Do not account for 'empty' services
                                iStop = 1
                            else:
                                # Make sure the 'overall' counting elements are there
                                if not sThisService in oStats: oStats[sThisService] = {'hit': 0, 'fail': 0}
                                # Make sure the 'NE-type-specific' counting elements are there
                                sNEtype = row[2]
                                if not sNEtype in oStats[sThisService]: oStats[sThisService][sNEtype] =  {'hit': 0, 'fail': 0}
                                # Keep track of the frequencies for this service
                                bHit = (row[4] == 'true')
                                if bHit:
                                    # Add to the 'overall' count of hits for this service
                                    oStats[sThisService]['hit'] += 1
                                    # Add to the NE-type-specific count of hits for this service
                                    oStats[sThisService][sNEtype]['hit'] += 1
                                else:
                                    # Add to the 'overall' count of fails for this service
                                    oStats[sThisService]['fail'] += 1
                                    # Add to the NE-type-specific count of fails for this service
                                    oStats[sThisService][sNEtype]['fail'] += 1

                        # Bookkeeping
                        sFileId = row[0]
                        sSentId = row[1]
                        sEntity = row[3]
                        sService = row[5]
                        sMethod = row[6]

            # Return the results
            return oStats
        except:
            # Show the user what is wrong
            self.errHandle.DoError('Could not get statistics: {}\n'.format(
                fInput))
            # Return failure
            return None

