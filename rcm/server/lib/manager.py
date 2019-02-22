import logging
import logging.config
import importlib
import os
import json
import copy
from collections import OrderedDict

# set prefix.
current_file = os.path.realpath(os.path.expanduser(__file__))
current_prefix = os.path.dirname(os.path.dirname(current_file))
print("current_prefix", current_prefix)
current_etc_path = os.path.join(current_prefix, "etc")

import sys
current_path = os.path.dirname(os.path.dirname(current_file))
current_lib_path = os.path.join(current_path, "lib")
sys.path.insert(0, current_path)
sys.path.insert(0, current_lib_path)

# local import
import config
import jobscript_builder
#import manager
import scheduler
from external import hiyapyco


logger = logging.getLogger('rcmServer')


class ServerManager:
    """
    The manager class.
    It is responsible to load from file the scheduler and service plugins.
    List of schedulers and services is written in a configuration yaml file
    """

    def __init__(self):
        self.schedulers = dict()
        self.services = dict()
        self.downloads = dict()

    def init(self, config_paths=[]):

        # load and merge yaml config from config_paths by loading logging
        # being a singleton , this first call define  the yaml files that are loaded
        # subsequent calls, reuse the same info, even if change the list_paths
        logging.config.dictConfig(config.CascadeYamlConfig(list_paths = config_paths)[['logging_configs']])

        # load client download info
        self.downloads = config.CascadeYamlConfig()[['plugins', 'schedulers']]

        # load plugins

        for scheduler_str in config.CascadeYamlConfig()[['plugins', 'schedulers']]:
            try:
                module_name, class_name = scheduler_str.rsplit(".", 1)
                print("try allocating: ",module_name, class_name)

                scheduler_class = getattr(importlib.import_module(module_name), class_name)
                scheduler_obj = scheduler_class()
                print("ALLOCATING: ",class_name)
                self.schedulers[class_name] = scheduler_obj
                logger.debug('loaded scheduler plugin ' +
                             scheduler_obj.__class__.__name__ +
                             " - " + scheduler_obj.NAME)
            except Exception as e:
                logger.error("plugin " + scheduler_str + " loading failed")
                logger.error(e)

        # load services

        for service_str in config.CascadeYamlConfig()[['plugins', 'services']]:
            try:
                module_name, class_name = service_str.rsplit(".", 1)
                service_class = getattr(importlib.import_module(module_name), class_name)
                service_obj = service_class()
                self.services[class_name] = service_obj
                logger.debug('loaded service plugin ' + service_obj.__class__.__name__ + " - " + service_obj.name)
            except Exception as e:
                logger.error("plugin loading failed")
                logger.error(e)

        # instantiate widget tree
        class_table = dict()
        plug_instances = dict()
        for scheduler in self.schedulers:
            plug_instances[self.schedulers[scheduler].NAME] = self.schedulers[scheduler]
        class_table['SCHEDULER'] = (jobscript_builder.ConnectedManager, plug_instances)

        # SchedulerManager.register_scheduler([SlurmScheduler, PBSScheduler, LocalScheduler])
        self.widget_root = jobscript_builder.AutoChoiceNode(name='TOP',
                              # schema=config.conf['schema']['TOP'],
                              # defaults=config.conf.get('defaults', OrderedDict()).get('TOP',None),
                              class_table=class_table)

    def get_checksum_and_url(self, build_platform):
        checksum = ""
        for download in self.downloads['checksum']:
            key = list(download.keys())[0]
            if key == build_platform:
                checksum = str(list(download.values())[0])

        downloadurl = ""
        for download in self.downloads['url']:
            key = list(download.keys())[0]
            if key == build_platform:
                downloadurl = str(list(download.values())[0])

        return checksum, downloadurl

    def get_gui_options(self):
        return self.widget_root.get_gui_options()

    def get_jobscript_json_menu(self):
        return json.dumps(self.get_gui_options())

    def substitute(self,choices):
        return self.widget_root.substitute(choices)


