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

import sys
import os
import types
import inspect

# root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# sys.path.append(root_rcm_path)

# local includes
from rcm.server.lib.api import ServerAPIs
from rcm.client.miscellaneous.logger import logic_logger


def rcm_decorate(fn):
    name = fn.__name__
    code = fn.__code__
    argcount = code.co_argcount
    argnames = code.co_varnames[:argcount]

    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kw):
        """
        This is the wrapper for functions into ssh command line, it add debug info before calling actual command
        It uses the prex function defined in manager to get return from ssh command output
        """
        command = '--command=' + name
        for p in list(kw.keys()):
            if p in argnames:
                command += ' --' + p + '=' + "'" + kw[p] + "'"
        ret = args[0].decorate(command)
        return ret
    return wrapper


for name, fn in inspect.getmembers(ServerAPIs):
    if sys.version_info >= (3, 0):
        # look for user-defined member functions
        if isinstance(fn, types.FunctionType) and name[:2] != '__':
            logic_logger.debug("wrapping: " + name)
            setattr(ServerAPIs, name, rcm_decorate(fn))
    else:
        if isinstance(fn, types.MethodType) and name[:2] != '__':
            logic_logger.debug("wrapping: "+name)
            setattr(ServerAPIs, name, rcm_decorate(fn))


def get_protocol():
    return ServerAPIs()
