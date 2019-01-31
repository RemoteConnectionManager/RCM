#


class Scheduler:
    def __init__(self):
        self.name = ""


class OSScheduler(Scheduler):
    def __init__(self):
        super().__init__()
        self.name = "OS"


class SlurmScheduler(Scheduler):
    def __init__(self):
        super().__init__()
        self.name = "Slurm"


class PBSScheduler(Scheduler):
    def __init__(self):
        super().__init__()
        self.name = "PBS"