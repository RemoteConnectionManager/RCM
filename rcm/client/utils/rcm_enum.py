# std lib
from enum import Enum


class Status(Enum):
    NOTDEFINED = "Not defined"
    PENDING = "pending"
    RUNNING = "valid"
    KILLING = "killing"
    FINISHED = "finished"

    def __str__(self):
        return '{0}'.format(self.value)


class Mode(Enum):
    GUI = 1
    CLI = 2
    TEST = 3
