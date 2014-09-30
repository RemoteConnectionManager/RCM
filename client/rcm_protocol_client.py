import sys
import os
import types
import inspect

sys.path.append( os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)) ) , "server"))

import logging
module_logger = logging.getLogger('RCM.protocol')

def rcm_decorate(fn):
    name=fn.func_name
    code=fn.func_code
    argcount = code.co_argcount
    argnames = code.co_varnames[:argcount]
#    print "inside_decorator "+inspect.stack()[0][3]+" function->"+name,
#    print "argcount->",argcount, " argnames-->",argnames

    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kw):
        command='--command='+name
        for p in kw.keys():
            if p in argnames:
                command +=' --'+p+'='+kw[p]
        module_logger.debug( "calling "+name+" argnames-> "+str(argnames))
        #ret=fn(*args, **kw)
        module_logger.debug( str(kw)+" -- "+ str(args))
        module_logger.debug( "self-->"+str(args[0]))
        module_logger.debug("running remote:"+command)
        ret=args[0].mycall(command)
        #print "returning-->"+ret
        return ret
    return wrapper

import rcm_protocol_server



for name,fn in inspect.getmembers(rcm_protocol_server.rcm_protocol):
    if isinstance(fn, types.UnboundMethodType) and name[:2] != '__':
        module_logger.debug( "wrapping-->"+name)
        setattr(rcm_protocol_server.rcm_protocol, name, rcm_decorate(fn))

def get_protocol():
    return rcm_protocol_server.rcm_protocol()
if __name__ == '__main__':

    def prex(command='',commandnode=''):
        return "prex:node "+commandnode+" run -->"+ command+"<--"

    r=get_protocol()
    for i in ['uno','due','tre']:
      def mycall(command):
          return prex(command,i)
      module_logger.debug( "config return:",r.config(build_platform='mia_build_platform_'+i))
      module_logger.debug( "queue return:",r.queue())

#class rcm_protocol_client(rcm.rcm_protocol):
