import sys
import os
import types
import inspect

root_rcm_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_rcm_path)
from server import rcm_protocol_server
import logging
module_logger = logging.getLogger('RCM.protocol')

def rcm_decorate(fn):
    name = fn.__name__
    code = fn.__code__
    argcount = code.co_argcount
    argnames = code.co_varnames[:argcount]

    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kw):
        command = '--command=' + name
        for p in list(kw.keys()):
            if p in argnames:
                command += ' --' + p + '=' + kw[p]
        module_logger.debug("calling " + name + " argnames-> " + str(argnames))
        module_logger.debug(str(kw) + " -- " + str(args))
        module_logger.debug("self-->" + str(args[0]))
        module_logger.debug("running remote:" + command)
        ret = args[0].mycall(command)
        return ret
    return wrapper


for name, fn in inspect.getmembers(rcm_protocol_server.rcm_protocol):
    if sys.version_info >= (3, 0):
        # look for user-defined member functions
        if isinstance(fn, types.FunctionType) and name[:2] != '__':
            module_logger.debug("wrapping-->" + name)
            setattr(rcm_protocol_server.rcm_protocol, name, rcm_decorate(fn))
    else:
        if isinstance(fn, types.MethodType) and name[:2] != '__':
            module_logger.debug("wrapping-->"+name)
            setattr(rcm_protocol_server.rcm_protocol, name, rcm_decorate(fn))


def get_protocol():
    return rcm_protocol_server.rcm_protocol()


if __name__ == '__main__':
    def prex(command='', commandnode=''):
        return "prex:node " + commandnode + " run -->" + command + "<--"

    r = get_protocol()
    for i in ['uno', 'due', 'tre']:
        def mycall(command):
            return prex(command, i)
        module_logger.debug("config return:", r.config(build_platform='mia_build_platform_' + i))
        module_logger.debug("queue return:", r.queue())
