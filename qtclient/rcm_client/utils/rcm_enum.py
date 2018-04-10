# std lib
from enum import Enum


class Status(Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    FINISHED = "Finished"

    def __str__(self):
        return '{0}'.format(self.value)
