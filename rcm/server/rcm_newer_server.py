#!/bin/env python

import os
import pwd
import re
import logging
import logging.handlers
#from __future__ import print_function

import rcm


import rcm_protocol_server
import rcm_protocol_parser
import sys
import platformconfig

import  logger_server
import logging
logger = logging.getLogger("RCM." + __name__)


if __name__ == '__main__':

    #logger_setup(0)
    string_info = " "
    for a in sys.argv[1:]:
        string_info+=a+" "

    logger.info(__file__ + string_info)
    logger.debug(sys.executable + " "+ os.path.abspath(__file__) + string_info)

    #launch rcm
    #logger_setup(1)
    p=platformconfig.platformconfig()
    s=p.get_rcm_server()
    r=rcm_protocol_server.rcm_protocol(s)
    c=rcm_protocol_parser.CommandParser(r)
    c.handle()

