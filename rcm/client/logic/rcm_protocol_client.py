# std lib
import sys
import os
import types
import inspect

root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)

# local includes
from server.lib.api import ServerAPIs
from client.miscellaneous.logger import logic_logger


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
