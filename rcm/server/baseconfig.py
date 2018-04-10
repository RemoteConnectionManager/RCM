import logging
import os
import sys
import socket
import ConfigParser
import enumerate_interfaces
import string
import inspect
import json 

class baseconfig:
    def __init__(self): 

        self.confdict=dict()
        self.sections=dict()
        self.options=dict()
        

    def parse(self,configfile=''): 
        print logging.__file__
        logger = logging.getLogger(name='basic')    
        logger.debug("parse")
        config = ConfigParser.RawConfigParser()
        if(not configfile):
            myPath =   os.path.join(
                        os.path.dirname(
                         os.path.dirname(
                          os.path.abspath(__file__)
                         )
                        ),'config')
            myPathOther =   os.path.join(
                        os.path.dirname(
                         os.path.dirname(sys.argv[0])
                        ),'config')
            configfile=os.path.join(myPath, self.filename)
        logger.debug("config file : "+configfile)
        if(not os.path.exists(configfile)):
            print "WARNING FIRST TRY missing platform file -->"+configfile
            configfile=os.path.join(myPathOther, self.filename)
            if(not os.path.exists(configfile)):
                print "WARNING NO WAY missing platform file -->"+configfile
                return(False)
#    print "parsing configfile-->",configfile
        config.read(configfile)
        for s in config.sections():
            for o in config.options(s):
                self.confdict[(s,o)]=config.get(s, o)
                self.sections[s]=self.sections.get(s,[])+[o]
                self.options[o]=self.options.get(o,[])+[s]

        logger.debug(self.sections)

        

