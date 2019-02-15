import logging
import importlib
import os
import json

# set prefix.
current_file = os.path.realpath(os.path.expanduser(__file__))
current_prefix = os.path.dirname(os.path.dirname(current_file))
current_etc_path = os.path.join(current_prefix, "etc")

import sys
current_path = os.path.dirname(os.path.dirname(current_file))
current_lib_path = os.path.join(current_path, "lib")
sys.path.insert(0, current_path)
sys.path.insert(0, current_lib_path)

import cascade_yaml_config
import jobscript_composer_base
import scheduler_base
import scheduler_pbs
import scheduler_slurm

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
                                 " - " + scheduler_obj.name)
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
        scheduler_base.SchedulerManager.register_scheduler([
            scheduler_slurm.SlurmScheduler,
            scheduler_pbs.PBSScheduler,
            scheduler_pbs.LocalScheduler])

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

        gui_composer = jobscript_composer_base.AutoChoiceNode(
            schema=self.cascade_config.conf['schema'],
            defaults=self.cascade_config.conf.get('defaults', None),
            class_table={'SCHEDULER': scheduler_base.SchedulerManager})

        display_dialog_ui = gui_composer.get_gui_options()
        return json.dumps(display_dialog_ui)
