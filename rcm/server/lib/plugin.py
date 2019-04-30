import logging
import copy
from collections import OrderedDict
import utils

logger = logging.getLogger('rcmServer' + '.' + __name__)


class Plugin(object):

    def __init__(self):
        if not hasattr(self, 'NAME'):
            self.NAME = ''
        if not hasattr(self, 'COMMANDS'):
            self.COMMANDS = {}
        self.PARAMS = {}
        if self.NAME:
            self.logger = logging.getLogger('rcmServer' + '.' + __name__ + '.' + self.NAME)
        else:
            self.logger = logger
        for command in self.COMMANDS:
            exe = utils.which(command)
            if exe:
                self.COMMANDS[command] = exe
                self.logger.debug("command: " + command + " found")
            else:
                self.logger.error("command: " + command + " not found !!!!")
                raise RuntimeError("Plugin " + self.__class__.__name__ + " need command: " + command + " NOT FOUND")

        self.templates = dict()
        self.selected = False

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
