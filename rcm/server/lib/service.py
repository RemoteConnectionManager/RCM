#


class Service(object):
    def __init__(self):
        self.name = ""


class TurboVNCServer(Service):
    def __init__(self):
        super(TurboVNCServer, self).__init__()
        self.name = "TurboVNC"
