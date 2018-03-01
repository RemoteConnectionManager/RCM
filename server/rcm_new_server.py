#!/bin/env python

import os
import pwd
import re
import logging
#from __future__ import print_function

import rcm


import rcm_protocol_server
import rcm_protocol_parser
import sys
import platformconfig



if __name__ == '__main__':

    # init loggger
    logger_name = 'basic'
    logger = logging.getLogger(logger_name)
    logger.setLevel( "DEBUG"  )
    ch = logging.StreamHandler(sys.stdout)
    username=pwd.getpwuid(os.geteuid())[0]
    rcmdir=os.path.expanduser("~%s/.rcm" % username)
    if ( not os.path.isdir(rcmdir) ):
        os.mkdir(rcmdir)
        os.chmod(rcmdir,0755)
    rcmlog=os.path.join(rcmdir,'logfile')
    fh = logging.FileHandler(rcmlog, mode='a')
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s (%(module)s %(funcName)s) : %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)


    #logger.addHandler(ch)
    logger.addHandler(fh)

    logger.debug("---------------------------------")
    logger.debug("                                 ")
    logger.debug("   RCM server command launched   ")
    logger.debug("                                 ")
    logger.debug("---------------------------------")

    #launch rcm
    p=platformconfig.platformconfig()
    s=p.get_rcm_server()
    r=rcm_protocol_server.rcm_protocol(s)
    c=rcm_protocol_parser.CommandParser(r)

    c.handle()

