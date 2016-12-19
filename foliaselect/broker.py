#! /usr/bin/env python3
# -*- coding: utf8 -*-

import util
import sys
import os.path
import time
import re
import lxml     # As used in alpino2folia.xml
import json

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
        # Get the relax NG schema
        self.schema = lxml.etree.RelaxNG(folia.relaxng())
        self.quick = False
        self.reHref = re.compile(r"href=['\"]?([^'\"]+)")
