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
    def __init__(self):
        self.schedulers = None

    def init(self):
        "load schedulers plugins from a setting file"
        logger.debug('loading scheduler plugins in ' + os.path.join(current_etc_path ,'plugins.yaml'))

        output = hiyapyco.load(
            os.path.join(current_etc_path ,'plugins.yaml')
        )
        for scheduler in output['schedulers']:
            module_name, class_name = scheduler.rsplit(".", 1)
            scheduler_class = getattr(importlib.import_module(module_name), class_name)
            scheduler_obj = scheduler_class()
            logger.debug('laoded scheduler plugin ' + scheduler_obj.__class__.__name__  + " - " + scheduler_obj.name)

        logger.debug('scheduler plugins loaded')
