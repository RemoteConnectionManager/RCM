#


class Service:
    def __init__(self):
        self.name = ""


class TurboVNCServer(Service):
    def __init__(self):
        super().__init__()
        self.name = "TurboVNC"
