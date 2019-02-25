import logging
import copy
from collections import OrderedDict
import utils

logger = logging.getLogger('rcmServer')


class Plugin(object):
    NAME = None
    PARAMS = {}
    COMMANDS = {}

    def __init__(self):
        for command in self.COMMANDS:
            exe = utils.which(command)
            if exe:
                self.COMMANDS[command] = exe
                logger.debug("command: " + command + " found")
            else:
                logger.error("command: " + command + " not found !!!!")
                raise RuntimeError("Plugin " + self.__class__.__name__ + " need command: " + command + " NOT FOUND")

        self.templates = dict()


    @staticmethod
    def merge_list(preset, computed):
        logger.debug("merging:" + str(preset) + "----" + str(computed))
        out = copy.deepcopy(preset)
        for a in computed:
            if a not in out:
                if hasattr(out, 'append'):
                    out.append(a)
                else:
                    out[a] = OrderedDict()
        logger.debug("merged:" + str(out))
        return out
