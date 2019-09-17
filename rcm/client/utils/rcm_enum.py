#
# Copyright (c) 2014-2019 CINECA.
#
# This file is part of RCM (Remote Connection Manager) 
# (see http://www.hpc.cineca.it/software/rcm).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from enum import Enum


class Status(Enum):
    NOTDEFINED = "Not defined"
    INIT = "init"
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
