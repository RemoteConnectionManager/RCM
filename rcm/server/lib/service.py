#
import logging
import plugin

class Service(plugin.Plugin):

    COMMANDS = {}

    def search_port(self, logfile=''):
        raise NotImplementedError()



class TurboVNCServer(Service):
    def __init__(self):
        super(TurboVNCServer, self).__init__()
        self.name = "TurboVNC"
