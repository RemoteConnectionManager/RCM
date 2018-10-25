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
from  logger_server import logger

if __name__ == '__main__':

    string_info="run--->"+__file__+" "
    for a in sys.argv[1:]:
        string_info+=a+" "
    string_debug = "python->" + sys.executable
    logger.info(string_info)
    logger.debug(string_debug)

    #launch rcm
    p=platformconfig.platformconfig()
    s=p.get_rcm_server()
    r=rcm_protocol_server.rcm_protocol(s)
    c=rcm_protocol_parser.CommandParser(r)

    c.handle()

