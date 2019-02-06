#


class Scheduler(object):
    def __init__(self):
        self.name = ""


class OSScheduler(Scheduler):
    def __init__(self):
        super(OSScheduler, self).__init__()
        self.name = "OS"


class SlurmScheduler(Scheduler):
    def __init__(self):
        super(SlurmScheduler, self).__init__()
        self.name = "Slurm"

class PBSScheduler(Scheduler):
    def __init__(self):
        super(PBSScheduler, self).__init__()
        self.name = "PBS"