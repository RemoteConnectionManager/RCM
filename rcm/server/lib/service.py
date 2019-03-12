#
import logging
import plugin

class Service(plugin.Plugin):

    COMMANDS = {}

    def __init__(self, *args, **kwargs):
        super(Service, self).__init__(*args, **kwargs)

    def search_port(self, logfile=''):
        raise NotImplementedError()



class TurboVNCServer(Service):
    def __init__(self):
        super(TurboVNCServer, self).__init__()
        self.NAME = "TurboVNC"

class Fake(Service):
    def __init__(self):
        super(Fake, self).__init__()
        self.NAME = "FakeService"