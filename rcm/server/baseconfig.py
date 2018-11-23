import os
import sys
import socket
import logging

if sys.version_info.major == 3:
    import configparser as ConfigParser
else:
    import ConfigParser


# new
root_rcm_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_rcm_path)
from utils.cascade_yaml_config import *
from utils.jobscript_composer_base import *
from utils.scheduler_pbs import *

import  logger_server

logger = logging.getLogger("RCM." + __name__)



class baseconfig:
    def __init__(self): 

        self.confdict = dict()
        self.sections = dict()
        self.options = dict()
        self.filename = ''
        self.config_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ), 'config')
        self.config_path_other = os.path.join(
            os.path.dirname(
                os.path.dirname(sys.argv[0])
            ), 'config')

        list_paths = []
        nodelogin = socket.gethostname()
        home_config_dir = os.path.join(os.environ.get('HOME',''), '.rcm', 'config')
        for basepath in [home_config_dir, self.config_path, self.config_path_other]:
            list_paths.append(os.path.join(basepath, 'config.yaml'))
            list_paths.append(os.path.join(basepath, nodelogin + '.yaml'))

        self.cascade_config = CascadeYamlConfig(list_paths)
        logger.debug("setting logging levels " + str(self.cascade_config.conf.get('logging',dict())))
        logger_server.logger_server.config(self.cascade_config.conf.get('logging',dict()))

    def cascade_parse(self):

        SchedulerManager.register_scheduler([SlurmScheduler, PBSScheduler, LocalScheduler])
        self.gui_composer = AutoChoiceGuiComposer(schema=self.cascade_config.conf['schema'],
                                                  defaults=self.cascade_config.conf.get('defaults', None),
                                                  class_table={'SCHEDULER': SchedulerManager})

        config = self.cascade_config.conf.get('old', [])
        for s in config:
            for o in config[s]:
                value = config[s][o]
                if (s, o) in self.confdict:
                    if value == self.confdict[(s, o)]:
                        logger.info("MATCH OK " + str((s, o)))
                    else:
                        logger.warning("MATCH FAIL " + str((s, o)) + "previous:" + str(self.confdict[(s, o)]) + "new:" + str(value))
                else:
                    logger.debug("NEW "+ str((s, o)) + "==>" + str(value))
                self.confdict[(s, o)] = value
                self.sections[s] = self.sections.get(s, []) + [o]
                self.options[o] = self.options.get(o, []) + [s]

    def config_parse(self, configfile=''):
        logger.debug("config_parse")
        config = ConfigParser.RawConfigParser()
        if not configfile:
            configfile = os.path.join(self.config_path, self.filename)
        logger.debug("config file : " + configfile)
        if not os.path.exists(configfile):
            logger.debug("WARNING FIRST TRY missing platform file -->" + configfile)
            configfile = os.path.join(self.config_path_other, self.filename)
            if not os.path.exists(configfile):
                logger.debug("WARNING NO WAY missing platform file -->" + configfile)
                return False
#    print "parsing configfile-->",configfile
        config.read(configfile)
        for s in config.sections():
            for o in config.options(s):
                self.confdict[(s, o)] = config.get(s, o)
                self.sections[s] = self.sections.get(s, []) + [o]
                self.options[o] = self.options.get(o, []) + [s]

        logger.debug(self.sections)

    def parse(self, configfile=''):
        self.config_parse(configfile=configfile)
        self.cascade_parse()

        

