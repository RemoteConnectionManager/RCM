import logging
import importlib
import os

# set prefix.
current_file = os.path.realpath(os.path.expanduser(__file__))
current_prefix = os.path.dirname(os.path.dirname(current_file))
current_etc_path = os.path.join(current_prefix, "etc")

from external import hiyapyco

logger = logging.getLogger('rcmServer')


class SessionManager:
    """
    The manager class.
    It is responsible to load from file the scheduler and service plugins.
    List of schedulers and services is written in a configuration yaml file
    """

    def __init__(self):
        self.schedulers = dict()
        self.services = dict()

    def init(self):
        "load plugins from a setting file"
        logger.debug('loading plugins in ' + os.path.join(current_etc_path ,'plugins.yaml'))

        output = hiyapyco.load(
            os.path.join(current_etc_path ,'plugins.yaml')
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
                                 scheduler_obj.__class__.__name__  +
                                 " - " + scheduler_obj.name)
                except Exception as e:
                    logger.error("plugin loading failed")
                    logger.error(e)

        logger.debug('scheduler plugins loaded')

        # load services
        if 'services' in output and output['services']:
            for service_str in output['services']:
                try:
                    module_name, class_name = service_str.rsplit(".", 1)
                    service_class = getattr(importlib.import_module(module_name), class_name)
                    service_obj = service_class()
                    self.services[class_name] = service_obj
                    logger.debug('loaded service plugin ' + service_obj.__class__.__name__  + " - " + service_obj.name)
                except Exception as e:
                    logger.error("plugin loading failed")
                    logger.error(e)

        logger.debug('service plugins loaded')