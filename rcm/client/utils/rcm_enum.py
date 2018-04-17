# std lib
from enum import Enum


class Status(Enum):
    PENDING = "pending"
    RUNNING = "valid"
    FINISHED = "finished"

    def __str__(self):
        return '{0}'.format(self.value)
