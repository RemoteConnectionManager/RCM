import logging
import importlib
import os
import json
import copy
from collections import OrderedDict

# set prefix.
current_file = os.path.realpath(os.path.expanduser(__file__))
current_prefix = os.path.dirname(os.path.dirname(current_file))
current_etc_path = os.path.join(current_prefix, "etc")

import sys
current_path = os.path.dirname(os.path.dirname(current_file))
current_lib_path = os.path.join(current_path, "lib")
sys.path.insert(0, current_path)
sys.path.insert(0, current_lib_path)

# local import
import cascade_yaml_config
import jobscript_builder
import manager
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

    def init(self):
        # load plugins from a setting file
        logger.debug('loading plugins in ' + os.path.join(current_etc_path, 'plugins.yaml'))

        output = hiyapyco.load(
            os.path.join(current_etc_path, 'plugins.yaml')
        )

        logger.debug('loading download url and checksum in ' + os.path.join(current_etc_path, 'download.yaml'))

        self.downloads = hiyapyco.load(
            os.path.join(current_etc_path, 'download.yaml')
        )

        # load plugins
        if 'services' in output and output['services']:
            for scheduler_str in output['schedulers']:
                try:
                    module_name, class_name = scheduler_str.rsplit(".", 1)
                    scheduler_class = getattr(importlib.import_module(module_name), class_name)
                    scheduler_obj = scheduler_class()
                    self.schedulers[class_name] = scheduler_obj
                    logger.debug('loaded scheduler plugin ' +
                                 scheduler_obj.__class__.__name__ +
                                 " - " + scheduler_obj.NAME)
                except Exception as e:
                    logger.error("plugin loading failed")
                    logger.error(e)

        # load services
        if 'services' in output and output['services']:
            for service_str in output['services']:
                try:
                    module_name, class_name = service_str.rsplit(".", 1)
                    service_class = getattr(importlib.import_module(module_name), class_name)
                    service_obj = service_class()
                    self.services[class_name] = service_obj
                    logger.debug('loaded service plugin ' + service_obj.__class__.__name__ + " - " + service_obj.name)
                except Exception as e:
                    logger.error("plugin loading failed")
                    logger.error(e)

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

    def get_jobscript_json_menu(self):
        manager.SchedulerManager.register_scheduler([
            scheduler.SlurmScheduler,
            scheduler.PBSScheduler,
            scheduler.LocalScheduler])

        list_paths = []
        self.config_path = ""
        import socket
        nodelogin = socket.gethostname()
        self.config_path_other = ""
        home_config_dir = os.path.join(os.environ.get('HOME', ''), '.rcm', 'config')
        for basepath in [home_config_dir, self.config_path, self.config_path_other]:
            list_paths.append(os.path.join(basepath, 'config.yaml'))
            list_paths.append(os.path.join(basepath, nodelogin + '.yaml'))

        self.cascade_config = cascade_yaml_config.CascadeYamlConfig(list_paths)

        gui_composer = jobscript_builder.AutoChoiceNode(
            schema=self.cascade_config.conf['schema'],
            defaults=self.cascade_config.conf.get('defaults', None),
            class_table={'SCHEDULER': manager.SchedulerManager})

        display_dialog_ui = gui_composer.get_gui_options()
        return json.dumps(display_dialog_ui)


class SchedulerManager(jobscript_builder.ManagerChoiceNode):
    NAME = 'SCHEDULER'
    SCHEDULERS = []

    _allInstances = []

    def __init__(self, *args, **kwargs):
        super(SchedulerManager, self).__init__(*args, **kwargs)

        SchedulerManager._allInstances.append(self)

        logger.debug("schedulers:" + str(self.SCHEDULERS))
        if 'list' in self.schema and hasattr(self.defaults, 'get'):
            for class_name in self.defaults:
                logger.debug("handling child  : " + class_name)
                managed_class = jobscript_builder.ManagedChoiceNode
                for sched_class in self.SCHEDULERS:
                    if sched_class.NAME == class_name:
                        managed_class = sched_class
                        break
                child = managed_class(name=class_name,
                                      schema=copy.deepcopy(self.schema['list']),
                                      defaults=copy.deepcopy(self.defaults.get(class_name, OrderedDict())))
                # here we override child shema_name, as is neede to be different from instance class name
                # WARNING.... external set of member variable outside object methods
                child.schema_name=self.NAME
                if child.working:
                    self.add_child(child)


    def active_scheduler(self):
        print("scheduler attivo:",self.active_child.NAME)
        return self.active_child

    @classmethod
    def register_scheduler(cls, sched_class_list):
        logger.debug("setting class " + str(cls) + " to " +  str(sched_class_list))
        for sched_class in sched_class_list:
            if sched_class not in  cls.SCHEDULERS:
                cls.SCHEDULERS.append(sched_class)
